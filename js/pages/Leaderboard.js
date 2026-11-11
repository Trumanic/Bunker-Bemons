import { store } from '../main.js';
import { fetchLeaderboard, groupByCountry } from '../content.js';
import {
    localize,
    countryName,
    formatDate,
    getYoutubeIdFromUrl,
    getThumbnailFromId,
    parseDate,
} from '../util.js';

import Spinner from '../components/Spinner.js';
import Avatar from '../components/Leaderboard/Avatar.js';
import Flag from '../components/Flag.js';
import SearchSort from '../components/Leaderboard/SearchSort.js';

const playerSortOptions = [
    { value: 'points', label: 'Points', defaultDir: 'desc' },
    { value: 'levels', label: 'Levels Count', defaultDir: 'desc' },
    { value: 'hardest', label: 'Hardest Level', defaultDir: 'desc' },
];

const countrySortOptions = [
    ...playerSortOptions,
    { value: 'players', label: 'Players', defaultDir: 'desc' },
];

const levelSortOptions = [
    { value: 'rank', label: 'Rank', defaultDir: 'asc' },
    { value: 'date', label: 'Date', defaultDir: 'desc' },
    { value: 'name', label: 'A-Z', defaultDir: 'asc' },
];

function filterAndSortLevels(levels, query, key, dir) {
    const q = query.trim().toLowerCase();
    const sign = dir === 'asc' ? 1 : -1;

    return levels
        .filter((l) => l.level.toLowerCase().includes(q))
        .sort((a, b) => {
            let result = 0;
            if (key === 'rank') {
                result = (a.rank - b.rank) * sign;
            } else if (key === 'name') {
                result =
                    a.level.localeCompare(b.level, undefined, {
                        sensitivity: 'base',
                        numeric: true,
                    }) * sign;
            } else if (key === 'date') {
                if (!a.date && b.date) return 1;
                if (a.date && !b.date) return -1;
                const dateA = parseDate(a.date);
                const dateB = parseDate(b.date);

                result = (dateA ?? -Infinity) - (dateB ?? -Infinity);
                result *= sign;
            }
            return result || a.rank - b.rank;
        });
}

function filterAndSortBoard(items, query, key, dir, matches) {
    const q = query.trim().toLowerCase();
    const sign = dir === 'asc' ? 1 : -1;

    const value = (p) => {
        if (key === 'levels') return p.beaten;
        if (key === 'players') return p.playerCount;
        if (key === 'hardest') return p.hardest ? -p.hardest.rank : null;
        return p.total;
    };

    return items
        .filter((p) => matches(p, q))
        .sort((a, b) => {
            const va = value(a);
            const vb = value(b);
            if (va === null && vb !== null) return 1;
            if (va !== null && vb === null) return -1;
            return (va - vb) * sign || a.rank - b.rank;
        });
}

export default {
    components: {
        Spinner,
        Avatar,
        Flag,
        SearchSort,
    },
    data: () => ({
        leaderboard: [],
        countries: [],
        view: 'players',
        loading: true,
        selectedUser: null,
        selectedCountry: null,
        err: [],
        search: '',
        sortKey: 'points',
        sortDir: 'desc',
        playerSortOptions,
        countrySortOptions,
        levelSearch: '',
        levelSortKey: 'rank',
        levelSortDir: 'asc',
        levelSortOptions,
        store,
        collapsedSections: {
            verified: false,
            completed: false,
            created: false,
        },
        thumbnailCache: {},
        mobileView: 'list',
    }),
    template: `
        <main v-if="loading" :class="{ dark: store.dark }">
            <Spinner></Spinner>
        </main>
        <main v-else class="page-leaderboard-container" :class="{ dark: store.dark, 'mobile-profile-open': mobileView === 'profile' }">
            <div class="page-leaderboard">
                <div class="error-container" v-if="err.length > 0">
                    <p class="error">
                        Leaderboard may be incorrect, as the following levels could not be loaded: {{ err.join(', ') }}
                    </p>
                </div>
                <div class="board-container">
                    <div class="tabs board-tabs" role="tablist">
                        <button type="button" role="tab" class="tab" :class="{ selected: view === 'players' }" :aria-selected="view === 'players'" @click="setView('players')">Players</button>
                        <button type="button" role="tab" class="tab" :class="{ selected: view === 'countries' }" :aria-selected="view === 'countries'" @click="setView('countries')">Countries</button>
                    </div>
                    <SearchSort
                        class="board-controls"
                        v-model:search="search"
                        v-model:sortKey="sortKey"
                        v-model:sortDir="sortDir"
                        :options="view === 'players' ? playerSortOptions : countrySortOptions"
                        :placeholder="view === 'players' ? 'Search players' : 'Search countries'"
                    />
                    <div class="board-list" v-if="view === 'players'">
                        <table class="board">
                            <tr v-for="player in players" :key="player.user">
                                <td class="rank">
                                    <p class="type-label-lg">#{{ player.rank }}</p>
                                </td>
                                <td class="total">
                                    <p class="type-label-lg">{{ localize(player.total) }}</p>
                                </td>
                                <td class="country">
                                    <p class="type-label-lg"><router-link v-if="player.country" class="flag-link" :title="countryName(player.country)" :to="{ path: '/leaderboard', query: { view: 'countries', country: player.country } }"><Flag class="flag--title" :code="player.country" /></router-link></p>
                                </td>
                                <td class="user" :class="{ 'active': selectedUser === player.user }">
                                    <button @click="selectPlayer(player.user, true)">
                                        <span class="type-label-lg">{{ player.user }}</span>
                                        <span v-if="detail(player)" class="detail type-label-md">{{ detail(player) }}</span>
                                    </button>
                                </td>
                            </tr>
                        </table>
                        <p class="empty" v-if="players.length === 0">No players found.</p>
                    </div>
                    <div class="board-list" v-else>
                        <table class="board">
                            <tr v-for="country in countryBoard" :key="country.code">
                                <td class="rank">
                                    <p class="type-label-lg">#{{ country.rank }}</p>
                                </td>
                                <td class="total">
                                    <p class="type-label-lg">{{ localize(country.total) }}</p>
                                </td>
                                <td class="country">
                                    <p class="type-label-lg"><Flag class="flag--title" :code="country.code" /></p>
                                </td>
                                <td class="user" :class="{ 'active': selectedCountry === country.code }">
                                    <button @click="selectCountry(country.code, true)">
                                        <span class="type-label-lg"> {{ country.name }}</span>
                                        <span v-if="countryDetail(country)" class="detail type-label-md">{{ countryDetail(country) }}</span>
                                    </button>
                                </td>
                            </tr>
                        </table>
                        <p class="empty" v-if="countries.length === 0">No countries yet. Add a country code for a player in data/players.json.</p>
                        <p class="empty" v-else-if="countryBoard.length === 0">No countries found.</p>
                    </div>
                </div>
                <div class="player-container" ref="playerContainer">
                    <button type="button" class="mobile-back-btn type-label-md" @click="mobileView = 'list'">
                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" /></svg>
                        <span>Back to Leaderboard</span>
                    </button>
                    <div class="player" v-if="view === 'countries' && countryEntry">
                        <div class="player-header">
                            <h1><Flag class="flag--title" :code="countryEntry.code" /> {{ countryEntry.name }}</h1>
                        </div>
                        <ul class="stats">
                            <li>
                                <div class="type-title-sm">Rank</div>
                                <p>#{{ countryEntry.rank }}</p>
                            </li>
                            <li>
                                <div class="type-title-sm">Points</div>
                                <p>{{ localize(countryEntry.total) }}</p>
                            </li>
                            <li>
                                <div class="type-title-sm">Players</div>
                                <p>{{ countryEntry.playerCount }}</p>
                            </li>
                            <li>
                                <div class="type-title-sm">Demons</div>
                                <p>{{ countryEntry.beaten }}</p>
                            </li>
                            <li>
                                <div class="type-title-sm">Hardest</div>
                                <p v-if="countryEntry.hardest">
                                    <a :href="countryEntry.hardest.link" target="_blank">{{ countryEntry.hardest.level }}</a>
                                </p>
                                <p v-else>-</p>
                            </li>
                        </ul>
                        <section>
                            <h2>Players</h2>
                            <table class="table">
                                <tr v-for="(member, i) in countryEntry.players" :key="member.user">
                                    <td class="rank">
                                        <p>#{{ i + 1 }}</p>
                                    </td>
                                    <td class="level">
                                        <router-link class="type-label-lg" :to="{ path: '/leaderboard', query: { player: member.user } }">{{ member.user }}</router-link>
                                    </td>
                                    <td class="count">
                                        <p>{{ member.beaten }} {{ member.beaten === 1 ? 'level' : 'levels' }}</p>
                                    </td>
                                    <td class="score">
                                        <p>{{ localize(member.total) }}</p>
                                    </td>
                                </tr>
                            </table>
                        </section>
                    </div>
                    <div class="player" v-else-if="view === 'players' && entry">
                        <div class="profile-header-card">
                            <div class="profile-identity">
                                <Avatar :name="entry.user" :pfp="entry.pfp" />
                                <div class="profile-title-box">
                                    <div class="profile-user-row">
                                        <router-link v-if="entry.country" class="flag-link" :title="countryName(entry.country)" :to="{ path: '/leaderboard', query: { view: 'countries', country: entry.country } }">
                                            <Flag class="flag--title" :code="entry.country" />
                                        </router-link>
                                        <h1>{{ entry.user }}</h1>
                                    </div>
                                    <span class="profile-rank-badge">Rank: #{{ entry.rank }}</span>
                                </div>
                            </div>
                            <div class="profile-stat-strip">
                                <div class="stat-box">
                                    <span class="stat-box-label">Points</span>
                                    <span class="stat-box-val">{{ localize(entry.total) }}</span>
                                </div>
                                <div class="stat-box">
                                    <span class="stat-box-label">Levels</span>
                                    <span class="stat-box-val">{{ entry.beaten }}</span>
                                </div>
                                <div class="stat-box">
                                    <span class="stat-box-label">Hardest</span>
                                    <span class="stat-box-val">
                                        <a v-if="entry.hardest" :href="entry.hardest.link" target="_blank">{{ entry.hardest.level }}</a>
                                        <template v-else>-</template>
                                    </span>
                                </div>
                            </div>
                        </div>

                        <!-- Compact Packs Sections Placed Above the Search Bar -->
                        <div v-if="(entry.completedPacks && entry.completedPacks.length > 0) || (entry.inProgressPacks && entry.inProgressPacks.length > 0)" class="profile-packs-wrapper">
                            <!-- Completed Packs -->
                            <div v-if="entry.completedPacks && entry.completedPacks.length > 0" class="profile-packs-category">
                                <div class="profile-packs-compact-grid">
                                    <router-link
                                        v-for="pack in entry.completedPacks"
                                        :key="'cp-' + pack.id"
                                        class="profile-pack-card-compact"
                                        :style="getThumbnailStyle(pack.thumbnail)"
                                        :to="{ path: '/packs', query: { pack: pack.id } }"
                                    >
                                        <div
                                            v-if="pack.thumbnail"
                                            class="profile-pack-card-thumb"
                                            :style="{ backgroundImage: 'url(' + pack.thumbnail + ')' }"
                                        ></div>
                                        <div class="profile-pack-card-overlay"></div>
                                        <div class="profile-pack-card-top">
                                            <p class="profile-pack-name">{{ pack.name }}</p>
                                        </div>
                                        <div class="profile-pack-card-bottom">
                                            <span class="profile-pack-pts">+{{ localize(pack.bonusPoints) }} pts</span>
                                            <span class="profile-pack-status"><svg viewBox="0 0 24 24" aria-hidden="true" width="14" height="14">
    <path d="M5 13l4 4L19 7" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg></span>
                                        </div>
                                    </router-link>
                                </div>
                            </div>

                            <!-- In Progress Packs -->
                            <div v-if="entry.inProgressPacks && entry.inProgressPacks.length > 0" class="profile-packs-category">
                                <div class="profile-packs-compact-grid">
                                    <router-link
                                        v-for="pack in entry.inProgressPacks"
                                        :key="'ip-' + pack.id"
                                        class="profile-pack-card-compact"
                                        :style="getThumbnailStyle(pack.thumbnail)"
                                        :to="{ path: '/packs', query: { pack: pack.id } }"
                                    >
                                        <div
                                            v-if="pack.thumbnail"
                                            class="profile-pack-card-thumb"
                                            :style="{ backgroundImage: 'url(' + pack.thumbnail + ')' }"
                                        ></div>
                                        <div class="profile-pack-card-overlay"></div>
                                        <div class="profile-pack-card-top">
                                            <p class="profile-pack-name">{{ pack.name }}</p>
                                        </div>
                                        <div class="profile-pack-card-bottom">
                                            <span class="profile-pack-status"><svg viewBox="0 0 24 24" aria-hidden="true" width="14" height="14">
    <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2.5"/>
    <path d="M12 7v5l3 3" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
</svg></span>
                                        </div>
                                    </router-link>
                                </div>
                            </div>
                        </div>

                        <SearchSort
                            v-if="entry.beaten > 0"
                            v-model:search="levelSearch"
                            v-model:sortKey="levelSortKey"
                            v-model:sortDir="levelSortDir"
                            :options="levelSortOptions"
                            placeholder="Search levels beaten"
                        />

                        <section v-if="entry.verified.length > 0" class="collapsible-section">
                            <h2 class="collapsible-header" @click="toggleSection('verified')">
                                <span>Verified ({{ countLabel(verified.length, entry.verified.length) }})</span>
                                <svg class="collapse-icon" :class="{ rotated: collapsedSections.verified }" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" /></svg>
                            </h2>
                            <div v-show="!collapsedSections.verified">
                                <table class="table" v-if="verified.length > 0">
                                    <tr
                                        v-for="level in verified"
                                        :key="'v-' + level.rank"
                                        class="level-card"
                                        :style="{ '--level-thumbnail': thumbnail(level.link) }"
                                    >
                                        <td class="rank">
                                            <p>#{{ level.rank }}</p>
                                        </td>
                                        <td class="level">
                                            <a class="type-label-lg" target="_blank" :href="level.link">{{ level.level }}</a>
                                        </td>
                                        <td class="score">
                                            <p>+{{ localize(level.score) }}</p>
                                        </td>
                                    </tr>
                                </table>
                                <p class="empty" v-else>No levels match your search.</p>
                            </div>
                        </section>

                        <section v-if="entry.completed.length > 0" class="collapsible-section">
                            <h2 class="collapsible-header" @click="toggleSection('completed')">
                                <span>Completed ({{ countLabel(completed.length, entry.completed.length) }})</span>
                                <svg class="collapse-icon" :class="{ rotated: collapsedSections.completed }" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" /></svg>
                            </h2>
                            <div v-show="!collapsedSections.completed">
                                <table class="table" v-if="completed.length > 0">
                                    <tr
                                        v-for="level in completed"
                                        :key="'c-' + level.rank"
                                        class="level-card"
                                        :style="{ '--level-thumbnail': thumbnail(level.link) }"
                                    >
                                        <td class="rank">
                                            <p>#{{ level.rank }}</p>
                                        </td>
                                        <td class="level">
                                            <a class="type-label-lg" target="_blank" :href="level.link">{{ level.level }}</a>
                                        </td>
                                        <td class="date">
                                            <p>{{ formatDate(level.date) }}</p>
                                        </td>
                                        <td class="score">
                                            <p>+{{ localize(level.score) }}</p>
                                        </td>
                                    </tr>
                                </table>
                                <p class="empty" v-else>No levels match your search.</p>
                            </div>
                        </section>

                        <section v-if="entry.created.length > 0" class="collapsible-section">
                            <h2 class="collapsible-header" @click="toggleSection('created')">
                                <span>Created &amp; Published ({{ entry.created.length }})</span>
                                <svg class="collapse-icon" :class="{ rotated: collapsedSections.created }" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" /></svg>
                            </h2>
                            <div v-show="!collapsedSections.created">
                                <table class="table">
                                    <tr
                                        v-for="level in created"
                                        :key="'m-' + level.rank"
                                        class="level-card"
                                        :style="{ '--level-thumbnail': thumbnail(level.link) }"
                                    >
                                        <td class="rank">
                                            <p>#{{ level.rank }}</p>
                                        </td>
                                        <td class="level">
                                            <a class="type-label-lg" target="_blank" :href="level.link">{{ level.level }}</a>
                                        </td>
                                        <td class="role">
                                            <p>{{ level.role }}</p>
                                        </td>
                                    </tr>
                                </table>
                            </div>
                        </section>

                    </div>
                    <p class="empty" v-else-if="view === 'countries'">Select a country to see its players.</p>
                    <p class="empty" v-else>Nobody is on the leaderboard yet.</p>
                </div>
            </div>
        </main>
    `,
    computed: {
        entry() {
            return (
                this.leaderboard.find((e) => e.user === this.selectedUser) ??
                null
            );
        },
        countryEntry() {
            return (
                this.countries.find((c) => c.code === this.selectedCountry) ??
                null
            );
        },
        players() {
            return filterAndSortBoard(
                this.leaderboard,
                this.search,
                this.sortKey,
                this.sortDir,
                (p, q) => p.user.toLowerCase().includes(q),
            );
        },
        countryBoard() {
            return filterAndSortBoard(
                this.countries,
                this.search,
                this.sortKey,
                this.sortDir,
                (c, q) =>
                    c.name.toLowerCase().includes(q) ||
                    c.code.toLowerCase() === q,
            );
        },
        verified() {
            return filterAndSortLevels(
                this.entry?.verified ?? [],
                this.levelSearch,
                this.levelSortKey,
                this.levelSortDir,
            );
        },
        completed() {
            return filterAndSortLevels(
                this.entry?.completed ?? [],
                this.levelSearch,
                this.levelSortKey,
                this.levelSortDir,
            );
        },
        created() {
            return [...(this.entry?.created ?? [])].sort(
                (a, b) => a.rank - b.rank,
            );
        },
    },
    watch: {
        '$route.fullPath'() {
            if (this.loading || this.$route.path !== '/leaderboard') {
                return;
            }
            this.syncFromRoute();
        },
        selectedUser() {
            this.levelSearch = '';
            this.resetProfileScroll();
        },
        selectedCountry() {
            this.resetProfileScroll();
        },
    },
    async mounted() {
        const [leaderboard, err] = await fetchLeaderboard();
        this.leaderboard = leaderboard;
        this.countries = groupByCountry(leaderboard);
        this.err = err;
        this.syncFromRoute();
        this.loading = false;
        const query = this.$route.query;
        if (query.player || query.country) {
            this.$nextTick(() =>
                this.$el
                    ?.querySelector?.('.board-list .user.active')
                    ?.scrollIntoView({ block: 'center' }),
            );
        }
    },
    methods: {
        localize,
        userFromQuery(value) {
            const wanted = (Array.isArray(value) ? value[0] : value) ?? '';
            return (
                this.leaderboard.find(
                    (e) => e.user.toLowerCase() === wanted.toLowerCase(),
                )?.user ??
                this.leaderboard[0]?.user ??
                null
            );
        },
        countryFromQuery(value) {
            const wanted = (Array.isArray(value) ? value[0] : value) ?? '';
            return (
                this.countries.find(
                    (c) => c.code === String(wanted).trim().toLowerCase(),
                )?.code ??
                this.countries[0]?.code ??
                null
            );
        },
        thumbnail(link) {
            const id = getYoutubeIdFromUrl(link || '');
            if (!id) return 'none';

            if (this.thumbnailCache[id]) {
                return `url("${this.thumbnailCache[id]}")`;
            }

            const maxresUrl = `https://img.youtube.com/vi/${id}/maxresdefault.jpg`;
            const hqUrl = `https://img.youtube.com/vi/${id}/hqdefault.jpg`;

            this.thumbnailCache[id] = maxresUrl;

            const img = new Image();
            img.onload = () => {
                if (img.naturalWidth <= 120 || img.naturalHeight <= 90) {
                    this.thumbnailCache[id] = hqUrl;
                    this.$forceUpdate?.();
                }
            };
            img.src = maxresUrl;

            return `url("${this.thumbnailCache[id]}")`;
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
        syncFromRoute() {
            const query = this.$route.query;
            const view =
                query.view === 'countries' || query.country
                    ? 'countries'
                    : 'players';
            if (view !== this.view) {
                this.view = view;
                this.search = '';
                this.sortKey = 'points';
                this.sortDir = 'desc';
            }
            if (view === 'countries') {
                this.selectedCountry = this.countryFromQuery(query.country);
            } else {
                this.selectedUser = this.userFromQuery(query.player);
            }
        },
        setView(view) {
            if (view === this.view) {
                return;
            }
            this.view = view;
            this.search = '';
            this.sortKey = 'points';
            this.sortDir = 'desc';
            if (view === 'countries') {
                this.selectedCountry =
                    this.countryEntry?.code ?? this.countries[0]?.code ?? null;
                this.$router.replace({
                    path: '/leaderboard',
                    query: this.selectedCountry
                        ? { view: 'countries', country: this.selectedCountry }
                        : { view: 'countries' },
                });
            } else {
                this.$router.replace({
                    path: '/leaderboard',
                    query: this.selectedUser ? { player: this.selectedUser } : {},
                });
            }
        },
        selectPlayer(user, fromUserClick = false) {
            this.selectedUser = user;
            if (fromUserClick) {
                this.mobileView = 'profile';
            }
            this.$router.replace({
                path: '/leaderboard',
                query: { player: user },
            });
        },
        selectCountry(code, fromUserClick = false) {
            this.selectedCountry = code;
            if (fromUserClick) {
                this.mobileView = 'profile';
            }
            this.$router.replace({
                path: '/leaderboard',
                query: { view: 'countries', country: code },
            });
        },
        toggleSection(section) {
            this.collapsedSections[section] = !this.collapsedSections[section];
        },
        resetProfileScroll() {
            this.$nextTick(() => {
                if (this.$refs.playerContainer) {
                    this.$refs.playerContainer.scrollTop = 0;
                }
            });
        },
        countryName,
        formatDate,
        detail(player) {
            if (this.sortKey === 'levels') {
                return `${player.beaten} ${player.beaten === 1 ? 'level' : 'levels'}`;
            }
            if (this.sortKey === 'hardest') {
                return player.hardest
                    ? `#${player.hardest.rank} ${player.hardest.level}`
                    : 'No levels beaten';
            }
            return '';
        },
        countryDetail(country) {
            if (this.sortKey === 'levels') {
                return `${country.beaten} ${country.beaten === 1 ? 'level' : 'levels'}`;
            }
            if (this.sortKey === 'players') {
                return `${country.playerCount} ${country.playerCount === 1 ? 'player' : 'players'}`;
            }
            if (this.sortKey === 'hardest') {
                return country.hardest
                    ? `#${country.hardest.rank} ${country.hardest.level} (${country.hardest.user})`
                    : 'No levels beaten';
            }
            return '';
        },
        countLabel(shown, total) {
            return shown === total ? `${total}` : `${shown} of ${total}`;
        },
    },
};