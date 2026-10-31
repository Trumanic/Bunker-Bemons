import { round, score } from './score.js';
import { countryName, normalizeCountry } from './util.js';

/**
 * Path to directory containing `_list.json` and all levels
 */
const dir = '/data';

export async function fetchList() {
    // Banned players are hidden: their records are left out everywhere
    const players = await fetchPlayers();
    const listResult = await fetch(`${dir}/_list.json`);
    try {
        const list = await listResult.json();
        return await Promise.all(
            list.map(async (path, rank) => {
                const levelResult = await fetch(`${dir}/${path}.json`);
                try {
                    const level = await levelResult.json();
                    return [
                        {
                            ...level,
                            path,
                                                        records: level.records
                                .filter((r) => !playerInfo(players, r.user).banned)
                                .sort(
                                    (a, b) =>
                                        (b.date || '').localeCompare(a.date || ''),
                                ),
                        },
                        null,
                    ];
                } catch {
                    console.error(`Failed to load level #${rank + 1} ${path}.`);
                    return [null, path];
                }
            }),
        );
    } catch {
        console.error(`Failed to load list.`);
        return null;
    }
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
 * { amine: { country: 'ma', pfp: 'amine.png' } }
 */
export async function fetchPlayers() {
    try {
        const result = await fetch(`${dir}/players.json`);
        const raw = await result.json();
        const players = {};
        Object.entries(raw).forEach(([name, info]) => {
            const country = normalizeCountry(info?.country);
            if (String(info?.country ?? '').trim() && !country) {
                console.warn(
                    `players.json: "${info.country}" (${name}) is not a valid country code.`,
                );
            }
            players[name.trim().toLowerCase()] = {
                country,
                                pfp: String(info?.pfp ?? '').trim(),
                banned: info?.banned === true,
            };
        });
        return players;
    } catch {
        return {};
    }
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

export async function fetchLeaderboard() {
    const list = await fetchList();
    const players = await fetchPlayers();
    const total = list.length;

    const scoreMap = {};
    const errs = [];

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

        const points = score(rank + 1, total);

        // Verification (blank verifiers are not on the leaderboard)
        const verifier = (level.verifier || '').trim();
                if (verifier && !playerInfo(players, verifier).banned) {
            getEntry(verifier).verified.push({
                rank: rank + 1,
                level: level.name,
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
                rank: rank + 1,
                level: level.name,
                score: points,
                link: record.link,
                date: record.date,
            });
        });
    });

    // Created / published levels (only for people already on the leaderboard)
    list.forEach(([level], rank) => {
        if (!level) {
            return;
        }

        const rawCreators = level.creators || [];
        const creators = rawCreators
            .map((c) => c.trim())
            .filter((c) => c && c !== '-');
        const author = (level.author || '').trim();
        const publisher = author !== '-' ? author : '';

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
            // Same rule as the level page: with no creators listed,
            // the author counts as the creator too
            const isCreator =
                creators.some((c) => c.toLowerCase() === name) ||
                (rawCreators.length === 0 && isPublisher);

            scoreMap[user].created.push({
                rank: rank + 1,
                level: level.name,
                role:
                    isCreator && isPublisher
                        ? 'Creator & Publisher'
                        : isCreator
                          ? 'Creator'
                          : 'Publisher',
                link: level.verification,
            });
        });
    });

    // Wrap in extra Object containing the user and total score
    const res = Object.entries(scoreMap).map(([user, scores]) => {
        const { verified, completed } = scores;
        const beaten = [...verified, ...completed];
        const sum = beaten.reduce((prev, cur) => prev + cur.score, 0);

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
            total: round(sum),
            beaten: beaten.length,
            hardest: hardest
                ? {
                      rank: hardest.rank,
                      level: hardest.level,
                      link: hardest.link,
                  }
                : null,
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

    return [res, errs];
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

    const res = Object.entries(groups).map(([code, members]) => {
        // Hardest level = the highest ranked level any of its players beat
        const hardest = members.reduce((best, p) => {
            if (!p.hardest || (best && best.rank <= p.hardest.rank)) {
                return best;
            }
            return { ...p.hardest, user: p.user };
        }, null);

        return {
            code,
            name: countryName(code),
            total: round(members.reduce((sum, p) => sum + p.total, 0)),
            beaten: members.reduce((sum, p) => sum + p.beaten, 0),
            playerCount: members.length,
            hardest,
            // Already in leaderboard (points) order
            players: members,
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
