import { store } from '../main.js';
import { fetchPacks, fetchList, fetchLegacy, fetchLeaderboard } from '../content.js';
import { localize, parseDate } from '../util.js';
import { score } from '../score.js';

import Spinner from '../components/Spinner.js';

export default {
    components: { Spinner },
    template: `
        <main v-if="loading" :class="{ dark: store.dark }">
            <Spinner></Spinner>
        </main>
        <main v-else class="page-packs" :class="{ dark: store.dark }">

            <!-- Left sidebar: search, tier filters, stats -->
            <div class="packs-sidebar">
                <div class="packs-sidebar-inner">
                    <p class="packs-sidebar-intro">
                        Complete every demon in a pack to earn bonus points and have it
                        marked as completed on your leaderboard profile.
                    </p>

                    <!-- Search packs -->
                    <div class="packs-search-box">
                        <input
                            type="text"
                            class="packs-search-input"
                            v-model="searchQuery"
                            placeholder="Search packs..."
                        />
                    </div>

                    <!-- Layout View Mode Toggle -->
                    <div class="packs-filter-section">
                        <span class="packs-filter-label">View Layout</span>
                        <div class="packs-tier-filter">
                            <button
                                class="tier-filter-btn"
                                :class="{ active: groupByTier }"
                                @click="groupByTier = true"
                            ><svg viewBox="0 0 24 24" aria-hidden="true" width="18" height="18">
    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg></button>
                            <button
                                class="tier-filter-btn"
                                :class="{ active: !groupByTier }"
                                @click="groupByTier = false"
                            ><svg viewBox="0 0 24 24" aria-hidden="true" width="18" height="18">
    <rect x="3" y="3" width="7" height="7" rx="1" fill="none" stroke="currentColor" stroke-width="2"/>
    <rect x="14" y="3" width="7" height="7" rx="1" fill="none" stroke="currentColor" stroke-width="2"/>
    <rect x="3" y="14" width="7" height="7" rx="1" fill="none" stroke="currentColor" stroke-width="2"/>
    <rect x="14" y="14" width="7" height="7" rx="1" fill="none" stroke="currentColor" stroke-width="2"/>
</svg></button>
                        </div>
                    </div>

                    <!-- Tier filter buttons -->
                    <div class="packs-filter-section" v-if="tiers.length > 1">
                        <span class="packs-filter-label">Filter by Tier</span>
                        <div class="packs-tier-filter">
                            <button
                                class="tier-filter-btn"
                                :class="{ active: activeTier === null }"
                                @click="activeTier = null"
                            >All Tiers</button>
                            <button
                                v-for="tier in tiers"
                                :key="tier"
                                class="tier-filter-btn"
                                :class="['tier-filter-btn--' + getTierClass(tier), { active: activeTier === tier }]"
                                @click="activeTier = tier"
                            >{{ tier }}</button>
                        </div>
                    </div>

                    <!-- Overall pack stats -->
                    <div class="packs-stats">
                        <div class="pack-stat-box">
                            <span class="pack-stat-label">Total Packs</span>
                            <span class="pack-stat-val">{{ packs.length }}</span>
                        </div>
                        <div class="pack-stat-box">
                            <span class="pack-stat-label">Tiers</span>
                            <span class="pack-stat-val">{{ tiers.length }}</span>
                        </div>
                        <div class="pack-stat-box">
                            <span class="pack-stat-label">Total Bonus Available</span>
                            <span class="pack-stat-val">+{{ localize(totalBonusPoints) }} pts</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main scrollable area -->
            <div class="packs-main" ref="packsMain">

                <!-- No packs created yet -->
                <p class="packs-empty" v-if="packs.length === 0">
                    No packs have been created yet.
                </p>

                <!-- No packs matching filter -->
                <p class="packs-empty" v-else-if="filteredPacks.length === 0">
                    No packs match your current filters.
                </p>

                <!-- Pack Detail Panel (shown when a pack is open) -->
                <div v-else-if="selectedPack" class="pack-detail">
                    <button class="pack-detail-back type-label-md" @click="closePack">
                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                        Back to Packs
                    </button>

                    <!-- Pack Hero Banner -->
                    <div
                        class="pack-detail-hero"
                        :class="{ 'pack-detail-hero--no-thumb': !selectedPack.thumbnail }"
                        :style="getThumbnailStyle(selectedPack.thumbnail)"
                    >
                        <div class="pack-detail-hero-overlay">
                            <div class="pack-detail-hero-content">
                                <div class="pack-detail-top-badges">
                                    <span v-if="selectedPack.tier" class="pack-tier-badge" :class="'pack-tier-badge--' + getTierClass(selectedPack.tier)">
                                        {{ selectedPack.tier }}
                                    </span>
                                </div>
                                <h1 class="pack-detail-name">{{ selectedPack.name }}</h1>
                                <p v-if="selectedPack.description" class="pack-detail-desc">{{ selectedPack.description }}</p>
                                <div class="pack-detail-tags">
                                    <span class="pack-detail-tag">
                                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="currentColor"/></svg>
                                        +{{ localize(getPackBonusPoints(selectedPack)) }} bonus pts
                                    </span>
                                    <span class="pack-detail-tag">
                                        {{ selectedPack.levels.length }} {{ selectedPack.levels.length === 1 ? 'demon' : 'demons' }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Required Demons List -->
                    <div class="pack-detail-levels">
                        <div class="pack-detail-levels-header">
                            <h2 class="pack-detail-levels-heading">Required Demons</h2>
                        </div>

                        <div v-if="detailLevelsLoading" class="pack-detail-levels-loading">
                            <Spinner></Spinner>
                        </div>
                        <table v-else class="pack-levels-table">
                            <tbody>
                                <tr
                                    v-for="lvl in selectedPackLevels"
                                    :key="lvl.path"
                                    class="pack-level-row"
                                >
                                    <td class="pack-level-rank">
                                        <p v-if="lvl.rank">#{{ lvl.rank }}</p>
                                        <p v-else class="pack-level-not-ranked">Legacy</p>
                                    </td>
                                    <td class="pack-level-name">
                                        <a
                                            v-if="lvl.link"
                                            :href="lvl.link"
                                            target="_blank"
                                            class="type-label-lg"
                                        >{{ lvl.name }}</a>
                                        <span v-else class="type-label-lg">{{ lvl.name }}</span>
                                        <span v-if="lvl.missing" class="pack-level-badge-missing">Not on list</span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Unified Player Progress Section -->
                    <div class="pack-progress-container">
                        <!-- Victors Sub-section -->
                        <div class="pack-progress-sub-section">
                            <h3 class="pack-progress-sub-heading">
                                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 13l4 4L19 7" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                                Victors ({{ packVictors.length }})
                            </h3>
                            <p class="packs-empty" v-if="packVictors.length === 0">No players have completed this pack yet.</p>
                            <div v-else class="pack-victors-grid">
                                <router-link
                                    v-for="player in packVictors"
                                    :key="player.user"
                                    :to="{ path: '/leaderboard', query: { player: player.user } }"
                                    class="pack-victor-card"
                                >
                                    <div class="pack-victor-header">
                                        <div class="pack-victor-user-info">
                                            <div class="player-avatar-sm" :style="player.pfp ? { backgroundImage: 'url(' + player.pfp + ')' } : {}"></div>
                                            <span class="pack-victor-name">{{ player.user }}</span>
                                        </div>
                                        <span v-if="player.completionDate" class="pack-victor-date">{{ player.completionDate }}</span>
                                    </div>
                                    <div class="pack-victor-demons-list">
                                        <span v-for="dName in player.beatenDemonNames" :key="dName" class="pack-victor-demon-badge">
                                            {{ dName }}
                                        </span>
                                    </div>
                                </router-link>
                            </div>
                        </div>

                        <div class="pack-progress-divider"></div>

                        <!-- In Progress Sub-section -->
                        <div class="pack-progress-sub-section">
                            <h3 class="pack-progress-sub-heading">
                                <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2.5"/><path d="M12 7v5l3 3" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>
                                In Progress ({{ packInProgress.length }})
                            </h3>
                            <p class="packs-empty" v-if="packInProgress.length === 0">No players currently working on this pack.</p>
                            <div v-else class="pack-inprogress-grid">
                                <router-link
                                    v-for="player in packInProgress"
                                    :key="player.user"
                                    :to="{ path: '/leaderboard', query: { player: player.user } }"
                                    class="pack-inprogress-card"
                                >
                                    <div class="pack-inprogress-user-info">
                                        <div class="pack-inprogress-user-left">
                                            <div class="player-avatar-sm" :style="player.pfp ? { backgroundImage: 'url(' + player.pfp + ')' } : {}"></div>
                                            <span class="pack-inprogress-name">{{ player.user }}</span>
                                        </div>
                                        <span class="pack-inprogress-pct">{{ Math.round((player.done / selectedPack.levels.length) * 100) }}%</span>
                                    </div>
                                    <div class="pack-inprogress-bar-wrap">
                                        <div class="inprogress-track">
                                            <div class="inprogress-fill" :style="{ width: Math.round((player.done / selectedPack.levels.length) * 100) + '%' }"></div>
                                        </div>
                                        <span class="pack-inprogress-count-text">{{ player.done }} / {{ selectedPack.levels.length }} demons beaten</span>
                                    </div>
                                    <div class="pack-inprogress-demons-list">
                                        <span
                                            v-for="lvlObj in player.levelStatuses"
                                            :key="lvlObj.path"
                                            class="pack-inprogress-demon-pill"
                                            :class="{ 'is-beaten': lvlObj.beaten }"
                                            :title="lvlObj.name + (lvlObj.beaten ? ' (Beaten)' : ' (Incomplete)')"
                                        >
                                            {{ lvlObj.name }}
                                        </span>
                                    </div>
                                </router-link>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- View Mode: Grouped by Tier or Flat Gallery -->
                <template v-else>
                    <!-- Option A: Grouped by Tier -->
                    <template v-if="groupByTier">
                        <div
                            v-for="tier in visibleTiers"
                            :key="tier"
                            class="packs-tier-group"
                            :class="'packs-tier-group--' + getTierClass(tier)"
                        >
                            <div class="packs-tier-header">
                                <div class="packs-tier-title-wrap">
                                    <h2 class="packs-tier-heading">{{ tier }}</h2>
                                </div>
                                <span class="packs-tier-count-badge">
                                    {{ groupedPacks[tier].length }} {{ groupedPacks[tier].length === 1 ? 'pack' : 'packs' }}
                                </span>
                            </div>

                            <div class="packs-grid">
                                <div
                                    v-for="pack in groupedPacks[tier]"
                                    :key="pack.id"
                                    class="pack-card"
                                    role="button"
                                    tabindex="0"
                                    @click="openPack(pack)"
                                >
                                    <!-- Thumbnail background -->
                                    <div
                                        class="pack-card-thumb"
                                        :style="getThumbnailStyle(pack.thumbnail)"
                                    ></div>
                                    <div class="pack-card-overlay"></div>

                                    <!-- Card content -->
                                    <div class="pack-card-body">
                                        <div class="pack-card-top">
                                            <span v-if="pack.tier" class="pack-tier-badge pack-tier-badge--sm" :class="'pack-tier-badge--' + getTierClass(pack.tier)">
                                                {{ pack.tier }}
                                            </span>
                                        </div>
                                        <h3 class="pack-card-name">{{ pack.name }}</h3>
                                        <p v-if="pack.description" class="pack-card-desc">{{ pack.description }}</p>

                                        <div class="pack-card-footer">
                                            <span class="pack-card-pts">+{{ localize(getPackBonusPoints(pack)) }} pts</span>
                                            <span class="pack-card-count">
                                                {{ pack.levels.length }} {{ pack.levels.length === 1 ? 'demon' : 'demons' }}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </template>

                    <!-- Option B: Flat All-Packs Gallery -->
                    <div v-else class="packs-grid">
                        <div
                            v-for="pack in filteredPacks"
                            :key="pack.id"
                            class="pack-card"
                            role="button"
    tabindex="0"
                            @click="openPack(pack)"
                        >
                            <!-- Thumbnail background -->
                            <div
                                class="pack-card-thumb"
                                :style="getThumbnailStyle(pack.thumbnail)"
                            ></div>
                            <div class="pack-card-overlay"></div>

                            <!-- Card content -->
                            <div class="pack-card-body">
                                <div class="pack-card-top">
                                    <span v-if="pack.tier" class="pack-tier-badge pack-tier-badge--sm" :class="'pack-tier-badge--' + getTierClass(pack.tier)">
                                        {{ pack.tier }}
                                    </span>
                                </div>
                                <h3 class="pack-card-name">{{ pack.name }}</h3>
                                <p v-if="pack.description" class="pack-card-desc">{{ pack.description }}</p>

                                <div class="pack-card-footer">
                                    <span class="pack-card-pts">+{{ localize(getPackBonusPoints(pack)) }} pts</span>
                                    <span class="pack-card-count">
                                        {{ pack.levels.length }} {{ pack.levels.length === 1 ? 'demon' : 'demons' }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </template>
            </div>
        </main>
    `,
    data: () => ({
        store,
        loading: true,
        packs: [],
        leaderboard: [],
        activeTier: null,
        searchQuery: '',
        groupByTier: true, // Toggle state for view mode
        selectedPack: null,
        selectedPackLevels: [],
        detailLevelsLoading: false,
        levelInfoCache: null,
        levelPoints: {},
        playerCompletions: {},
        playerRecordDates: {},
    }),
    async mounted() {
        const [packsData, [leaderboardData]] = await Promise.all([
            fetchPacks(),
            fetchLeaderboard(),
        ]);
        this.packs = packsData;
        this.leaderboard = leaderboardData || [];

        await this.buildPlayerCompletionsAndDates();

        const queryPack = this.$route.query.pack;
        if (queryPack) {
            const packMatch = this.packs.find((p) => p.id === queryPack);
            if (packMatch) {
                this.openPack(packMatch, false);
            }
        }

        this.loading = false;
    },
    watch: {
        '$route.query'() {
            if (this.loading) return;
            const queryPack = this.$route.query.pack;
            if (queryPack && (!this.selectedPack || this.selectedPack.id !== queryPack)) {
                const packMatch = this.packs.find((p) => p.id === queryPack);
                if (packMatch) this.openPack(packMatch, false);
            } else if (!queryPack && this.selectedPack) {
                this.selectedPack = null;
                this.selectedPackLevels = [];
            }
        },
    },
    computed: {
        tiers() {
            const seen = new Set();
            const result = [];
            for (const pack of this.packs) {
                const t = (pack.tier || '').trim() || 'Other';
                if (!seen.has(t)) {
                    seen.add(t);
                    result.push(t);
                }
            }
            return result;
        },
        totalBonusPoints() {
            return this.packs.reduce(
                (sum, pack) => sum + this.getPackBonusPoints(pack),
                0,
            );
        },
        filteredPacks() {
            const query = this.searchQuery.trim().toLowerCase();
            return this.packs.filter((pack) => {
                if (query) {
                    const nameMatch = pack.name.toLowerCase().includes(query);
                    const descMatch = (pack.description || '').toLowerCase().includes(query);
                    const tierMatch = (pack.tier || '').toLowerCase().includes(query);
                    if (!nameMatch && !descMatch && !tierMatch) return false;
                }

                if (this.activeTier !== null) {
                    const tier = (pack.tier || '').trim() || 'Other';
                    if (tier !== this.activeTier) return false;
                }

                return true;
            });
        },
        visibleTiers() {
            const seen = new Set();
            const result = [];
            for (const pack of this.filteredPacks) {
                const t = (pack.tier || '').trim() || 'Other';
                if (!seen.has(t)) {
                    seen.add(t);
                    result.push(t);
                }
            }
            return result;
        },
        groupedPacks() {
            const groups = {};
            for (const tier of this.visibleTiers) {
                groups[tier] = this.filteredPacks.filter(
                    (p) => ((p.tier || '').trim() || 'Other') === tier,
                );
            }
            return groups;
        },
        packVictors() {
            if (!this.selectedPack || !this.levelInfoCache) return [];
            const packLevels = this.selectedPack.levels || [];
            const result = [];

            this.leaderboard.forEach((player) => {
                const lowerUser = player.user.toLowerCase();
                const beatenSet = this.playerCompletions[lowerUser] || new Set();
                const hasAll = packLevels.every((path) => beatenSet.has(path));

                if (hasAll) {
                    let latestTimestamp = -Infinity;
                    const beatenDemonNames = packLevels.map((path) => {
                        const info = this.levelInfoCache[path];
                        const name = info ? info.name : path;

                        const dateStr = this.playerRecordDates[lowerUser]?.[path];
                        if (dateStr) {
                            const parsed = parseDate(dateStr);
                            if (parsed !== null && parsed > latestTimestamp) {
                                latestTimestamp = parsed;
                            }
                        }
                        return name;
                    });

                    let completionDateStr = '';
                    if (latestTimestamp !== -Infinity) {
                        const d = new Date(latestTimestamp);
                        if (!isNaN(d.getTime())) {
                            completionDateStr = d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
                        }
                    }

                    result.push({
                        ...player,
                        beatenDemonNames,
                        completionDate: completionDateStr,
                        latestTimestamp,
                    });
                }
            });

            result.sort((a, b) => b.latestTimestamp - a.latestTimestamp || a.user.localeCompare(b.user));
            return result;
        },
        packInProgress() {
            if (!this.selectedPack || !this.levelInfoCache) return [];
            const packLevels = this.selectedPack.levels || [];
            const result = [];

            this.leaderboard.forEach((player) => {
                const lowerUser = player.user.toLowerCase();
                const beatenSet = this.playerCompletions[lowerUser] || new Set();

                const packLevelsCount = packLevels.length;
                const doneCount = packLevels.filter((path) => beatenSet.has(path)).length;

                if (doneCount > 0 && doneCount < packLevelsCount) {
                    const levelStatuses = packLevels.map((path) => {
                        const info = this.levelInfoCache[path];
                        return {
                            path,
                            name: info ? info.name : path,
                            beaten: beatenSet.has(path),
                        };
                    });

                    result.push({
                        ...player,
                        done: doneCount,
                        levelStatuses,
                    });
                }
            });

            result.sort((a, b) => b.done - a.done || a.user.localeCompare(b.user));
            return result;
        },
    },
    methods: {
        localize,
        getTierClass(tierName) {
            if (!tierName) return 'default';
            const lower = tierName.toLowerCase().trim();
            if (lower.includes('bronze')) return 'bronze';
            if (lower.includes('silver')) return 'silver';
            if (lower.includes('gold')) return 'gold';
            if (lower.includes('diamond')) return 'diamond';
            return 'default';
        },
        getThumbnailStyle(thumbnail) {
            if (!thumbnail || typeof thumbnail !== 'string') return {};
            const val = thumbnail.trim();
            if (!val) return {};

            if (val.includes('-gradient(')) {
                return { backgroundImage: val };
            }

            if (
                val.startsWith('http://') ||
                val.startsWith('https://') ||
                val.startsWith('/') ||
                val.startsWith('./') ||
                /\.(png|jpe?g|webp|gif|svg)(\?.*)?$/i.test(val)
            ) {
                return { backgroundImage: `url("${val}")` };
            }

            return { backgroundColor: val };
        },
        async buildPlayerCompletionsAndDates() {
            const [list, legacy] = await Promise.all([fetchList(), fetchLegacy()]);

            if (list) {
                const total = list.length;
                list.forEach(([level], rank) => {
                    if (level) {
                        this.levelPoints[level.path] = score(rank + 1, total);
                    }
                });
            }

            this.levelInfoCache = {};
            if (list) {
                list.forEach(([lvl], idx) => {
                    if (lvl) {
                        this.levelInfoCache[lvl.path] = {
                            rank: idx + 1,
                            name: lvl.name,
                            link: lvl.verification,
                        };
                    }
                });
            }
            if (legacy) {
                legacy.forEach(([lvl]) => {
                    if (lvl && !this.levelInfoCache[lvl.path]) {
                        this.levelInfoCache[lvl.path] = {
                            rank: null,
                            name: lvl.name,
                            link: lvl.verification,
                        };
                    }
                });
            }

            const allLevels = [...(list || []), ...(legacy || [])];
            const compMap = {};
            const dateMap = {};

            allLevels.forEach(([level]) => {
                if (!level) return;
                const path = level.path;

                const verifier = (level.verifier || '').trim();
                if (verifier) {
                    const key = verifier.toLowerCase();
                    compMap[key] ??= new Set();
                    compMap[key].add(path);
                }
                (level.records || []).forEach((record) => {
                    const user = (record.user || '').trim();
                    if (!user) return;
                    const key = user.toLowerCase();
                    compMap[key] ??= new Set();
                    compMap[key].add(path);

                    if (record.date) {
                        dateMap[key] ??= {};
                        dateMap[key][path] = record.date;
                    }
                });
            });

            this.playerCompletions = compMap;
            this.playerRecordDates = dateMap;
        },
        getPackBonusPoints(pack) {
            const levels = [...new Set(pack.levels || [])];
            const basePoints = levels.reduce(
                (sum, path) => sum + (this.levelPoints[path] || 0),
                0,
            );
            const multiplier = Number(pack.multiplier);
            return basePoints * (
                Number.isFinite(multiplier) && multiplier > 0
                    ? multiplier
                    : 0
            );
        },
        syncQueryRoute() {
            const query = {};
            if (this.selectedPack) query.pack = this.selectedPack.id;
            this.$router.replace({ path: '/packs', query });
        },
        openPack(pack, updateRoute = true) {
            this.selectedPack = pack;
            if (updateRoute) this.syncQueryRoute();
            this.loadDetailLevels(pack);
            this.$nextTick(() => {
                this.$refs.packsMain?.scrollTo({ top: 0, behavior: 'smooth' });
            });
        },
        closePack() {
            this.selectedPack = null;
            this.selectedPackLevels = [];
            this.syncQueryRoute();
        },
        async loadDetailLevels(pack) {
            this.detailLevelsLoading = true;
            this.selectedPackLevels = [];

            const cache = this.levelInfoCache || {};
            this.selectedPackLevels = (pack.levels || []).map((path) => {
                if (cache[path]) {
                    return { path, ...cache[path], missing: false };
                }
                return { path, rank: null, name: path, link: null, missing: true };
            });

            this.detailLevelsLoading = false;
        },
    },
};