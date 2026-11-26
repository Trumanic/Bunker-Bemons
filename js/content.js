import { round, score, creatorPoints, RATINGS } from './score.js';
import { countryName, normalizeCountry, parseDate } from './util.js';

/**
 * Path to directory containing `_list.json` and all levels
 */
const dir = '/data';

/**
 * Keeps each data file's result for the lifetime of the page, so moving between
 * List / Leaderboard / Packs doesn't download everything again. Calls made while
 * a load is still running share it. Failed or incomplete loads are not kept, so
 * the next call tries again. Reloading the page always starts fresh.
 */
const cache = new Map();

function cached(key, load, isComplete) {
    if (!cache.has(key)) {
        const promise = load().then(
            (value) => {
                if (!isComplete(value)) {
                    cache.delete(key);
                }
                return value;
            },
            (error) => {
                cache.delete(key);
                throw error;
            },
        );
        cache.set(key, promise);
    }
    return cache.get(key);
}

// A list of levels is only kept when every level file loaded
const allLoaded = (list) =>
    Array.isArray(list) && list.length > 0 && list.every(([, err]) => !err);

/**
 * Loads and returns the packs definition array from data/_packs.json.
 * Returns an empty array if the file is missing or malformed.
 */
export function fetchPacks() {
    return cached(
        'packs',
        async () => {
            try {
                const result = await fetch(`${dir}/_packs.json`);
                const data = await result.json();
                return Array.isArray(data) ? data : [];
            } catch {
                return [];
            }
        },
        (packs) => packs.length > 0,
    );
}

/**
 * Loads level files by name. Each result is [level, null], or [null, name] when
 * a file could not be read. Records of banned players are left out.
 */
async function loadLevels(names, players) {
    return Promise.all(
        names.map(async (path) => {
            try {
                const levelResult = await fetch(`${dir}/${path}.json`);
                const level = await levelResult.json();
                return [
                    {
                        ...level,
                        path,
                        records: level.records
                            .filter((r) => !playerInfo(players, r.user).banned)
                            .sort((a, b) => {
                                const dateA = parseDate(a.date);
                                const dateB = parseDate(b.date);

                                return (dateB ?? -Infinity) - (dateA ?? -Infinity);
                            }),
                    },
                    null,
                ];
            } catch {
                console.error(`Failed to load level ${path}.`);
                return [null, path];
            }
        }),
    );
}

/**
 * The ranked list (data/_list.json), in rank order
 */
export function fetchList() {
    return cached(
        'list',
        async () => {
            // Banned players are hidden: their records are left out everywhere
            const players = await fetchPlayers();
            try {
                const listResult = await fetch(`${dir}/_list.json`);
                const list = await listResult.json();
                return await loadLevels(list, players);
            } catch {
                console.error(`Failed to load list.`);
                return null;
            }
        },
        allLoaded,
    );
}

/**
 * The legacy list (data/_legacy.json): archived levels with no rank and no points.
 * Returns an empty list when there is no legacy file.
 */
export function fetchLegacy() {
    return cached(
        'legacy',
        async () => {
            const players = await fetchPlayers();
            try {
                const legacyResult = await fetch(`${dir}/_legacy.json`);
                const legacy = await legacyResult.json();
                return await loadLevels(legacy, players);
            } catch {
                return [];
            }
        },
        allLoaded,
    );
}

/**
 * The Created list (data/_created.json): levels made by Bunker members, in rank order.
 * A level can also be on the ranked list: both lists point at the same level file.
 * Returns an empty list when there is no created file.
 */
export function fetchCreated() {
    return cached(
        'created',
        async () => {
            const players = await fetchPlayers();
            try {
                const createdResult = await fetch(`${dir}/_created.json`);
                const created = await createdResult.json();
                return await loadLevels(created, players);
            } catch {
                return [];
            }
        },
        allLoaded,
    );
}

export async function fetchEditors() {
    try {
        const editorsResults = await fetch(`${dir}/_editors.json`);
        const editors = await editorsResults.json();
        return editors;
    } catch {
        return null;
    }
}

/**
 * Reads data/players.json (optional) and returns it keyed by lowercase name:
 * { amine: { name: 'Amine', country: 'ma', pfp: 'amine.png', banned: false } }
 */
export function fetchPlayers() {
    return cached(
        'players',
        async () => {
            try {
                const result = await fetch(`${dir}/players.json`);
                const raw = await result.json();
                const players = {};
                Object.entries(raw).forEach(([rawName, info]) => {
                    const cleanName = String(rawName ?? '').trim();
                    if (!cleanName) return;
                    const country = normalizeCountry(info?.country);
                    if (String(info?.country ?? '').trim() && !country) {
                        console.warn(
                            `players.json: "${info.country}" (${cleanName}) is not a valid country code.`,
                        );
                    }
                    players[cleanName.toLowerCase()] = {
                        name: cleanName,
                        country,
                        pfp: String(info?.pfp ?? '').trim(),
                        banned: info?.banned === true,
                    };
                });
                return players;
            } catch {
                return {};
            }
        },
        (players) => Object.keys(players).length > 0,
    );
}

export function playerInfo(players, name) {
    return (
        players[String(name ?? '').trim().toLowerCase()] ?? {
            country: '',
            pfp: '',
            banned: false,
        }
    );
}

export async function fetchLeaderboard(mode = 'beaten') {
    const list =
        mode === 'created' ? await fetchCreated() : await fetchList();
    const players = await fetchPlayers();
    const total = list.length;

    const scoreMap = {};
    const errs = [];
    const levelPoints = {};
    const rawLevels = [];

    // Finds an existing leaderboard entry, ignoring upper/lower case
    const findUser = (name) =>
        Object.keys(scoreMap).find(
            (u) => u.toLowerCase() === name.toLowerCase(),
        );

    // Finds (or creates) a leaderboard entry
    const getEntry = (name) => {
        const user = findUser(name) || name;
        scoreMap[user] ??= { verified: [], completed: [], created: [] };
        return scoreMap[user];
    };

    // Verifications and records
    list.forEach(([level, err], rank) => {
        if (err) {
            errs.push(err);
            return;
        }

        const listRank = rank + 1;
        const points = score(listRank, total);
        levelPoints[level.path] = points;
        rawLevels.push({
            ...level,
            listRank,
            points,
        });

        // Verification (blank verifiers are not on the leaderboard)
        const verifier = (level.verifier || '').trim();
        if (verifier && !playerInfo(players, verifier).banned) {
            getEntry(verifier).verified.push({
                rank: listRank,
                level: level.name,
                path: level.path,
                score: points,
                link: level.verification,
            });
        }

        // Records (every record counts as a 100% completion)
        level.records.forEach((record) => {
            const user = (record.user || '').trim();
            if (!user) {
                return;
            }
            getEntry(user).completed.push({
                rank: listRank,
                level: level.name,
                path: level.path,
                score: points,
                link: record.link,
                date: record.date,
            });
        });
    });

    // Include every non-banned player listed in players.json, even with 0 levels
    Object.values(players).forEach((info) => {
        if (info.banned || !info.name) return;
        const existingUser = findUser(info.name);
        if (!existingUser) {
            scoreMap[info.name] = {
                verified: [],
                completed: [],
                created: [],
            };
        }
    });

    // Created / published levels (for everyone in scoreMap, including 0-completion players from players.json)
        (mode === 'created' ? list : []).forEach(([level], rank) => {
        if (!level) {
            return;
        }

        // Only names in "creators" earn Creator Points, never the publisher
        const creators = (level.creators || [])
            .map((c) => c.trim())
            .filter((c) => c && c !== '-');
        const author = (level.author || '').trim();
        const publisher = author !== '-' ? author : '';
        const rating = RATINGS.includes(level.rating) ? level.rating : 'Unrated';
        const points = creatorPoints(rating);

        const names = new Set(
            [...creators, publisher]
                .filter(Boolean)
                .map((n) => n.toLowerCase()),
        );

        names.forEach((name) => {
            const user = findUser(name);
            if (!user) {
                return;
            }

            const isPublisher = publisher.toLowerCase() === name;
            const isCreator = creators.some((c) => c.toLowerCase() === name);
            const earned = isCreator ? points : 0;

            scoreMap[user].created.push({
                rank: rank + 1,
                level: level.name,
                path: level.path,
                role:
                    isCreator && isPublisher
                        ? 'Creator & Publisher'
                        : isCreator
                          ? 'Creator'
                          : 'Publisher',
                link: level.verification,
                rating,
                points: earned,
            });
            scoreMap[user].creatorPoints =
                (scoreMap[user].creatorPoints || 0) + earned;
        });
    });

    // ---- Pack completion ----
    // Load packs and compute which packs each player has completed or is working on.
    const packs = mode === 'created' ? [] : await fetchPacks();
    const legacyList = mode === 'created' ? [] : await fetchLegacy();

    // Build a set of completed level paths per user (verified OR recorded).
    // list[i][0].path is the file name (e.g. "acheron") set by loadLevels.
    const userCompletedPaths = {}; // { lowerUsername -> Set<filePath> }
    const allRankedAndLegacy = [...(list || []), ...(legacyList || [])];
    allRankedAndLegacy.forEach(([level]) => {
        if (!level) return;
        const path = level.path;

        const verifier = (level.verifier || '').trim();
        if (verifier && !playerInfo(players, verifier).banned) {
            const key = verifier.toLowerCase();
            userCompletedPaths[key] ??= new Set();
            userCompletedPaths[key].add(path);
        }
        (level.records || []).forEach((record) => {
            const user = (record.user || '').trim();
            if (!user) return;
            const key = user.toLowerCase();
            userCompletedPaths[key] ??= new Set();
            userCompletedPaths[key].add(path);
        });
    });

    // For each user in scoreMap, compute pack progress
    Object.keys(scoreMap).forEach((user) => {
        const lowerUser = user.toLowerCase();
        const myPaths = userCompletedPaths[lowerUser] ?? new Set();

        const completedPacks  = [];
        const inProgressPacks = [];

        packs.forEach((pack) => {
            const packLevels = [...new Set(pack.levels || [])];
            if (packLevels.length === 0) return;

            const doneCount = packLevels.filter((lvl) => myPaths.has(lvl)).length;

            // Calculate the total points of all ranked levels in this pack
            const basePoints = packLevels.reduce(
                (sum, lvl) => sum + (levelPoints[lvl] || 0),
                0,
            );

            // Apply the pack's configurable multiplier
            const multiplier = Number(pack.multiplier) || 0;
            const bonusPoints = basePoints * multiplier;

            if (doneCount === packLevels.length) {
                // Fully completed - award bonus points
                completedPacks.push({
                    id:          pack.id,
                    name:        pack.name,
                    tier:        pack.tier || '',
                    thumbnail:   pack.thumbnail || '',
                    bonusPoints,
                    total:       packLevels.length,
                    done:        doneCount,
                });
            } else if (doneCount > 0) {
                // In progress
                inProgressPacks.push({
                    id:          pack.id,
                    name:        pack.name,
                    tier:        pack.tier || '',
                    thumbnail:   pack.thumbnail || '',
                    bonusPoints,
                    total:       packLevels.length,
                    done:        doneCount,
                });
            }
        });

        const packPoints = completedPacks.reduce((sum, p) => sum + p.bonusPoints, 0);
        scoreMap[user].completedPacks  = completedPacks;
        scoreMap[user].inProgressPacks = inProgressPacks;
        scoreMap[user].packPoints      = packPoints;
    });

    // Wrap in extra Object containing the user and total score
    const res = Object.entries(scoreMap).map(([user, scores]) => {
        const { verified, completed } = scores;
        const beaten = [...verified, ...completed];
        const sum = beaten.reduce((prev, cur) => prev + cur.score, 0);
        const packPoints = scores.packPoints || 0;

        // Hardest level = the highest ranked level they verified or beat
        const hardest = beaten.reduce(
            (best, cur) => (!best || cur.rank < best.rank ? cur : best),
            null,
        );

        const info = playerInfo(players, user);

        return {
            user,
            country: info.country,
            pfp: info.pfp,
            total: round(sum + packPoints),
            beaten: beaten.length,
            hardest: hardest
                ? {
                      rank: hardest.rank,
                      level: hardest.level,
                      path: hardest.path,
                      link: hardest.link,
                  }
                : null,
            packPoints,
            completedPacks:  scores.completedPacks  || [],
            inProgressPacks: scores.inProgressPacks || [],
            creatorPoints: scores.creatorPoints || 0,
            ...scores,
        };
    });

    // Sort by total score (ties: hardest level, then name)
    res.sort(
        (a, b) =>
            b.total - a.total ||
            (a.hardest?.rank ?? Infinity) - (b.hardest?.rank ?? Infinity) ||
            a.user.localeCompare(b.user),
    );

    // Fixed leaderboard position (by points), unaffected by search/sorting
    res.forEach((entry, i) => {
        entry.rank = i + 1;
    });

    // Attach level & player metadata for country completions & creations
    res._meta = { levels: rawLevels, players };

    return [res, errs];
}

function compareCompletionOrder(a, b) {
    const dateA = parseDate(a.date);
    const dateB = parseDate(b.date);

    if (dateA !== null && dateB !== null && dateA !== dateB) {
        return dateA - dateB;
    }
    if (dateA !== null && dateB === null) return -1;
    if (dateA === null && dateB !== null) return 1;

    return a.seq - b.seq;
}

/**
 * Groups the player leaderboard into a country leaderboard.
 * A country's points and levels are the sum of its players' points and levels.
 * Players without a country are left out.
 */
export function groupByCountry(leaderboard) {
    const groups = {};
    leaderboard.forEach((player) => {
        if (player.country) {
            (groups[player.country] ??= []).push(player);
        }
    });

    const levels = leaderboard._meta?.levels || [];
    const players = leaderboard._meta?.players || {};

    // Ensure every non-banned player in players.json with a country has a group
    Object.values(players).forEach((info) => {
        if (!info.banned && info.country) {
            groups[info.country] ??= [];
        }
    });

    const res = Object.entries(groups).map(([code, members]) => {
        // Hardest level = the highest ranked level any of its players beat
        const hardest = members.reduce((best, p) => {
            if (!p.hardest || (best && best.rank <= p.hardest.rank)) {
                return best;
            }
            return { ...p.hardest, user: p.user };
        }, null);

        // ---- Country Completions & Verifications (one row per unique level) ----
        const completions = [];

        levels.forEach((level) => {
            const countryAttempts = [];
            let seq = 0;

            const verifier = (level.verifier || '').trim();
            if (verifier) {
                const vInfo = playerInfo(players, verifier);
                if (!vInfo.banned && vInfo.country === code) {
                    countryAttempts.push({
                        kind: 'verified',
                        user: verifier,
                        date: level.date || '',
                        link: level.verification || '',
                        seq: seq++,
                    });
                }
            }

            (level.records || []).forEach((record) => {
                const recUser = (record.user || '').trim();
                if (!recUser) return;
                const rInfo = playerInfo(players, recUser);
                if (!rInfo.banned && rInfo.country === code) {
                    countryAttempts.push({
                        kind: 'completed',
                        user: recUser,
                        date: record.date || '',
                        link: record.link || level.verification || '',
                        seq: seq++,
                    });
                }
            });

            if (countryAttempts.length === 0) return;

            const firstAttempt = [...countryAttempts].sort(compareCompletionOrder)[0];
            const isVerified = firstAttempt.kind === 'verified';

            completions.push({
                rank: level.listRank,
                level: level.name,
                path: level.path,
                score: level.points,
                user: firstAttempt.user,
                date: firstAttempt.date,
                link: firstAttempt.link,
                verificationLink: level.verification || '',
                isVerified,
                statusLabel: isVerified ? 'Verified' : 'First Completed',
            });
        });

        completions.sort((a, b) => a.rank - b.rank);

        // ---- Country Created / Published Levels (any player in players.json with country) ----
        const createdLevels = [];

        levels.forEach((level) => {
            const rawCreators = level.creators || [];
            const creators = rawCreators
                .map((c) => c.trim())
                .filter((c) => c && c !== '-');
            const author = (level.author || '').trim();
            const publisher = author !== '-' ? author : '';

            const countryCreators = [];
            const seenCreators = new Set();

            creators.forEach((c) => {
                const info = playerInfo(players, c);
                if (!info.banned && info.country === code) {
                    const key = c.toLowerCase();
                    if (!seenCreators.has(key)) {
                        seenCreators.add(key);
                        countryCreators.push(c);
                    }
                }
            });

            let hasCountryPublisher = false;
            if (publisher) {
                const pInfo = playerInfo(players, publisher);
                if (!pInfo.banned && pInfo.country === code) {
                    hasCountryPublisher = true;
                    if (creators.length === 0) {
                        const key = publisher.toLowerCase();
                        if (!seenCreators.has(key)) {
                            seenCreators.add(key);
                            countryCreators.push(publisher);
                        }
                    }
                }
            }

            const hasCountryCreator = countryCreators.length > 0;
            if (!hasCountryCreator && !hasCountryPublisher) return;

            let roleLabel = 'Creator(s)';
            if (hasCountryPublisher && hasCountryCreator) {
                roleLabel = 'Publisher & Creator(s)';
            } else if (hasCountryPublisher) {
                roleLabel = 'Publisher';
            }

            const displayValue =
                countryCreators.length > 1
                    ? `${countryCreators.length} people`
                    : countryCreators[0] || publisher;

            createdLevels.push({
                rank: level.listRank,
                level: level.name,
                path: level.path,
                link: level.verification || '',
                verificationLink: level.verification || '',
                roleLabel,
                displayValue,
                countryCreators,
                hasMultipleCreators: countryCreators.length > 1,
            });
        });

        createdLevels.sort((a, b) => a.rank - b.rank);

        return {
            code,
            name: countryName(code),
            total: round(members.reduce((sum, p) => sum + p.total, 0)),
            creatorPoints: members.reduce((sum, p) => sum + (p.creatorPoints || 0), 0),
            beaten: members.reduce((sum, p) => sum + p.beaten, 0),
            playerCount: members.length,
            hardest,
            // Already in leaderboard (points) order
            players: members,
            completions,
            createdLevels,
        };
    });

    // Sort by total score (ties: hardest level, then name)
    res.sort(
        (a, b) =>
            b.total - a.total ||
            (a.hardest?.rank ?? Infinity) - (b.hardest?.rank ?? Infinity) ||
            a.name.localeCompare(b.name),
    );
    res.forEach((entry, i) => {
        entry.rank = i + 1;
    });

    return res;
}