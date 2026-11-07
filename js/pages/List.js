import { store } from "../main.js";
import { embed, formatDate, parseDate } from "../util.js";
import { score } from "../score.js";
import {
    fetchEditors,
    fetchLegacy,
    fetchList,
    fetchPlayers,
    playerInfo,
} from "../content.js";

import Spinner from "../components/Spinner.js";
import LevelAuthors from "../components/List/LevelAuthors.js";
import SearchSort from "../components/Leaderboard/SearchSort.js";
import Flag from "../components/Flag.js";

// The "List Editors" box is hidden for now. Set this to true to bring it back.
const showEditors = false;

const roleIconMap = {
    owner: "crown",
    admin: "user-gear",
    helper: "user-shield",
    dev: "code",
    trial: "user-lock",
};

const listSortOptions = [
    { value: "rank", label: "Rank", defaultDir: "asc" },
    { value: "name", label: "A-Z", defaultDir: "asc" },
    { value: "records", label: "Records", defaultDir: "desc" },
    { value: "latest", label: "Latest Record", defaultDir: "desc" },
];

// Wording for the direction button's tooltip, per sort option
const listSortLabels = {
    rank: ["Hardest first", "Easiest first"],
    name: ["A-Z", "Z-A"],
    records: ["Fewest records first", "Most records first"],
    latest: ["Oldest record first", "Newest record first"],
};

const recordSortOptions = [
    { value: "date", label: "Date", defaultDir: "desc" },
    { value: "name", label: "Player", defaultDir: "asc" },
];

const recordSortLabels = {
    date: ["Oldest", "Newest"],
    name: ["A-Z", "Z-A"],
};

const collator = new Intl.Collator(undefined, {
    sensitivity: "base",
    numeric: true,
});

// Removes duplicates ignoring upper/lower case, keeps the first spelling
function uniqueNames(names) {
    const seen = new Map();
    names.forEach((n) => {
        const name = String(n || "").trim();
        if (name && name !== "-" && !seen.has(name.toLowerCase())) {
            seen.set(name.toLowerCase(), name);
        }
    });
    return [...seen.values()].sort((a, b) => collator.compare(a, b));
}

export default {
    components: { Spinner, LevelAuthors, SearchSort, Flag },
    template: `
        <main v-if="loading" :class="{ dark: store.dark }">
            <Spinner></Spinner>
        </main>
        <main v-else class="page-list" :class="{ dark: store.dark, 'mobile-detail-open': mobileView === 'detail' }">
            <div class="list-container">
                <SearchSort
                    stacked
                    v-model:search="search"
                    v-model:sortKey="sortKey"
                    v-model:sortDir="sortDir"
                    :options="listSortOptions"
                    :asc-label="sortLabels[0]"
                    :desc-label="sortLabels[1]"
                    placeholder="Search levels"
                    @keydown.enter="onSearchEnter"
                />
                <div class="filters-bar">
                    <div class="filter-field">
                        <select id="filter-difficulty" v-model="filterDifficulty" title="Filter by difficulty">
                            <option value="">All Difficulties</option>
                            <option v-for="d in difficulties" :key="d" :value="d">{{ d }}</option>
                        </select>
                    </div>
                    <div class="filter-field">
                        <input id="filter-person" type="text" list="people-list" v-model="filterPerson" placeholder="Creator / Publisher">
                        <datalist id="people-list">
                            <option v-for="name in people" :key="name" :value="name"></option>
                        </datalist>
                    </div>
                    <div class="filter-field">
                        <select id="filter-records" v-model="filterRecords" title="Filter by records">
                            <option value="">All Records</option>
                            <option value="has">Has records</option>
                            <option value="none">No records</option>
                        </select>
                    </div>
                    <div class="filter-field" v-if="allTags.length > 0">
                        <select id="filter-tag" v-model="filterTag" title="Filter by tag">
                            <option value="">All Tags</option>
                            <option v-for="tag in allTags" :key="tag" :value="tag">{{ tag }}</option>
                        </select>
                    </div>
                    <div class="filter-actions">
                        <span class="result-count type-label-md">{{ resultCount }}</span>
                        <button v-if="isFiltering" type="button" class="clear-btn type-label-md" @click="clearAll">Clear</button>
                    </div>
                </div>
                <div class="list-scroll">
                                        <table class="list" v-if="visible.length > 0">
                        <template v-for="(entry, i) in visible" :key="entry.path">
                            <tr class="legacy-divider" v-if="entry.legacy && (i === 0 || !visible[i - 1].legacy)">
                                <td colspan="2">
                                    <div><span class="type-title-sm">Legacy</span></div>
                                </td>
                            </tr>
                            <tr>
                                <td class="rank" :class="{ 'legacy-rank': entry.legacy }">
                                    <p class="type-label-lg">{{ entry.legacy ? '-' : '#' + entry.rank }}</p>
                                </td>
                                <td class="level" :class="{ 'active': selectedPath === entry.path, 'error': !entry.level }">
                                    <button @click="selectLevel(entry.path, true)">
                                        <span class="type-label-lg">{{ rowLabel(entry) }}</span>
                                    </button>
                                </td>
                            </tr>
                        </template>
                    </table>
                    <p class="empty" v-else>No levels found.</p>
                </div>
            </div>
            <div class="level-container">
                <button type="button" class="mobile-back-btn type-label-md" @click="mobileView = 'list'">
                    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" /></svg>
                    <span>Back to List</span>
                </button>
                <div class="level" v-if="level">
                    <div class="level-sticky-header">
                        <div class="level-nav">
                            <button type="button" :disabled="!prevEntry" aria-label="Previous level" @click="selectLevel(prevEntry.path)">
                                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" /></svg>
                                <span class="type-label-lg">Previous</span>
                            </button>
                            <span class="position type-label-md">{{ positionLabel }}</span>
                            <button type="button" :disabled="!nextEntry" aria-label="Next level" @click="selectLevel(nextEntry.path)">
                                <span class="type-label-lg">Next</span>
                                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" /></svg>
                            </button>
                        </div>
                        <h1>{{ level.name }}</h1>
                        <div class="level-infobar">
                            <div class="infobar-item">
                                <span class="infobar-label">Rank</span>
                                <span class="infobar-value">{{ selectedEntry.legacy ? 'Legacy' : '#' + selectedEntry.rank }}</span>
                            </div>
                            <div class="infobar-item">
                                <span class="infobar-label">Points</span>
                                <span class="infobar-value">{{ selectedEntry.legacy ? '-' : score(selectedEntry.rank, rankedCount) }}</span>
                            </div>
                            <div class="infobar-item">
                                <span class="infobar-label">Difficulty</span>
                                <span class="infobar-value">{{ level.difficulty }}</span>
                            </div>
                            <div class="infobar-item">
                                <span class="infobar-label">ID</span>
                                <button type="button" class="copy-id-btn" :title="copied ? '' : 'Click to copy'" aria-label="Copy level ID" @click="copyId">
                                    {{ copied ? 'Copied!' : level.id }}
                                </button>
                            </div>
                        </div>
                    </div>
                    <LevelAuthors :author="level.author" :creators="level.creators" :verifier="level.verifier" :tags="level.tags || []" @tag="filterByTag"></LevelAuthors>
                    <iframe class="video" id="videoframe" :src="video" frameborder="0"></iframe>
                </div>
                <div v-else class="level" style="height: 100%; justify-content: center; align-items: center;">
                    <p>(ノಠ益ಠ)ノ彡┻━┻</p>
                </div>
            </div>
            <div class="meta-container">
                <div class="meta">
                    <div class="errors" v-show="errors.length > 0">
                        <p class="error" v-for="error of errors">{{ error }}</p>
                    </div>
                    <section class="records-section" v-if="level">
                        <h3>Records</h3>
                        <SearchSort
                            v-if="level.records.length > 1"
                            stacked
                            show-label
                            v-model:search="recordSearch"
                            v-model:sortKey="recordSortKey"
                            v-model:sortDir="recordSortDir"
                            :options="recordSortOptions"
                            :asc-label="recordLabels[0]"
                            :desc-label="recordLabels[1]"
                            placeholder="Search records"
                        />
                        <table class="records" v-if="records.length > 0">
                            <tr v-for="record in records" :key="record.user" class="record">
                                <td class="user">
                                    <div class="record-player" :class="{ 'has-flags': anyFlag }">
                                        <Flag v-if="countryOf(record.user)" class="flag--record" :code="countryOf(record.user)" />
                                        <span v-else-if="anyFlag" class="flag-spacer flag--record"></span>
                                        <router-link class="record-name type-label-lg" :to="{ path: '/leaderboard', query: { player: record.user } }">{{ record.user }}</router-link>
                                        <span class="record-date type-label-md">{{ formatDate(record.date) }}</span>
                                    </div>
                                </td>
                                <td class="watch">
                                    <a v-if="record.link" class="type-label-lg" :href="record.link" target="_blank">Watch</a>
                                    <p v-else class="none">-</p>
                                </td>
                            </tr>
                        </table>
                        <p class="empty" v-else-if="level.records.length === 0">No records yet.</p>
                        <p class="empty" v-else>No records match your search.</p>
                    </section>
                    <template v-if="showEditors && editors">
                        <h3>List Editors</h3>
                        <ol class="editors">
                            <li v-for="editor in editors">
                                <img :src="\`/assets/\${roleIconMap[editor.role]}\${store.dark ? '-dark' : ''}.svg\`" :alt="editor.role">
                                <a v-if="editor.link" class="type-label-lg link" target="_blank" :href="editor.link">{{ editor.name }}</a>
                                <p v-else>{{ editor.name }}</p>
                            </li>
                        </ol>
                    </template>
                </div>
            </div>
        </main>
    `,
    data: () => ({
        list: [],
        legacy: [],
        editors: [],
        players: {},
        loading: true,
        selectedPath: null,
        errors: [],
        roleIconMap,
        showEditors,
        store,
        // List controls
        search: "",
        sortKey: "rank",
        sortDir: "asc",
        listSortOptions,
        showFilters: false,
        filterDifficulty: "",
        filterPerson: "",
        filterRecords: "",
        filterTag: "",
        // Record controls (inside the level panel)
        recordSearch: "",
        recordSortKey: "date",
        recordSortDir: "desc",
        recordSortOptions,
        // "Copied!" feedback for the ID
        copied: false,
        mobileView: "list",
    }),
    computed: {
                // Every level: the ranked ones (with their real rank), then the legacy ones (no rank)
        entries() {
            const ranked = (this.list || []).map(([level, err], i) => ({
                level,
                rank: i + 1,
                legacy: false,
                order: i,
                path: level ? level.path : err,
            }));
            const taken = new Set(ranked.map((e) => e.path));
            const legacy = (this.legacy || [])
                .map(([level, err]) => ({
                    level,
                    rank: null,
                    legacy: true,
                    path: level ? level.path : err,
                }))
                // a level can't be both ranked and legacy: the ranked one wins
                .filter((e) => !taken.has(e.path))
                .map((e, i) => ({ ...e, order: ranked.length + i }));
            return [...ranked, ...legacy];
        },
        // Number of ranked levels (legacy levels don't count towards points)
        rankedCount() {
            return this.entries.filter((e) => !e.legacy).length;
        },
        selectedEntry() {
            return this.entries.find((e) => e.path === this.selectedPath) ?? null;
        },
        level() {
            return this.selectedEntry?.level ?? null;
        },
        video() {
            if (!this.level) {
                return "";
            }
            if (!this.level.showcase) {
                return embed(this.level.verification);
            }

            return embed(
                this.toggledShowcase
                    ? this.level.showcase
                    : this.level.verification
            );
        },

        // ----- Filters -----
        difficulties() {
            return [
                ...new Set(
                    this.entries
                        .map((e) => e.level?.difficulty)
                        .filter(Boolean)
                ),
            ].sort((a, b) => collator.compare(a, b));
        },
        people() {
            return uniqueNames(
                this.entries.flatMap((e) =>
                    e.level ? [e.level.author, ...(e.level.creators || [])] : []
                )
            );
        },
        allTags() {
            return uniqueNames(
                this.entries.flatMap((e) => e.level?.tags || [])
            );
        },
        activeFilters() {
            return [
                this.filterDifficulty,
                this.filterPerson.trim(),
                this.filterRecords,
                this.filterTag,
            ].filter(Boolean).length;
        },
        isFiltering() {
            return this.search.trim() !== "" || this.activeFilters > 0;
        },
        sortLabels() {
            return listSortLabels[this.sortKey] ?? ["Ascending", "Descending"];
        },

                // Levels shown in the list after searching, filtering and sorting
        visible() {
            const sign = this.sortDir === "asc" ? 1 : -1;

            let result = this.isFiltering
                ? this.entries.filter(this.matches)
                : [...this.entries];

            const compare = (a, b) => {
                // Levels that failed to load always go last
                if (!a.level || !b.level) {
                    return (!a.level ? 1 : 0) - (!b.level ? 1 : 0) || a.order - b.order;
                }

                let diff = 0;
                if (this.sortKey === "rank") {
                    diff = (a.order - b.order) * sign;
                } else if (this.sortKey === "name") {
                    diff = collator.compare(a.level.name, b.level.name) * sign;
                } else if (this.sortKey === "records") {
                    diff =
                        (a.level.records.length - b.level.records.length) * sign;
                } else if (this.sortKey === "latest") {
                    // Get the newest valid record date for each level
                    const getLatestDate = (entry) => {
                        const dates = (entry.level.records || [])
                            .map((record) => parseDate(record.date))
                            .filter((date) => date !== null);

                        return dates.length ? Math.max(...dates) : null;
                    };

                    const dateA = getLatestDate(a);
                    const dateB = getLatestDate(b);

                    // Levels without valid records always go last
                    if (dateA === null && dateB !== null) return 1;
                    if (dateA !== null && dateB === null) return -1;

                    if (dateA !== null && dateB !== null) {
                        diff = (dateA - dateB) * sign;
                    }
                }
                // Same value: keep the list order
                return diff || a.order - b.order;
            };

            // Ranked levels first; the legacy levels always stay below them
            return [
                ...result.filter((e) => !e.legacy).sort(compare),
                ...result.filter((e) => e.legacy).sort(compare),
            ];
        },
        resultCount() {
            const total = this.entries.length;
            if (this.isFiltering) {
                return `${this.visible.length} of ${total}`;
            }
            const legacy = total - this.rankedCount;
            return legacy > 0
                ? `${this.rankedCount} levels · ${legacy} legacy`
                : `${total} levels`;
        },

        // ----- Previous / next (follow the current search, filters and sort) -----
        visibleIndex() {
            return this.visible.findIndex((e) => e.path === this.selectedPath);
        },
        prevEntry() {
            return this.visibleIndex > 0
                ? this.visible[this.visibleIndex - 1]
                : null;
        },
        nextEntry() {
            // If the open level is hidden by the filters, "next" starts at the top
            return this.visibleIndex < this.visible.length - 1
                ? this.visible[this.visibleIndex + 1]
                : null;
        },
        positionLabel() {
            return this.visibleIndex >= 0
                ? `${this.visibleIndex + 1} of ${this.visible.length}`
                : `${this.visible.length} results`;
        },

        
// ----- Records -----
records() {
    if (!this.level) {
        return [];
    }

    const q = this.recordSearch.trim().toLowerCase();
    const sign = this.recordSortDir === "asc" ? 1 : -1;

    return this.level.records
        .filter((r) => r.user.toLowerCase().includes(q))
        .sort((a, b) => {
            if (this.recordSortKey === "name") {
                return collator.compare(a.user, b.user) * sign;
            }

            const dateA = parseDate(a.date);
            const dateB = parseDate(b.date);

            // Records without valid dates always go last
            if (dateA === null && dateB !== null) return 1;
            if (dateA !== null && dateB === null) return -1;

            return (
                ((dateA ?? 0) - (dateB ?? 0)) * sign ||
                collator.compare(a.user, b.user)
            );
        });
},

        // True when at least one player in this level's records has a country
        anyFlag() {
            return this.records.some((r) => this.countryOf(r.user));
        },
        recordCount() {
            const total = this.level?.records.length ?? 0;
            return this.records.length === total
                ? `${total}`
                : `${this.records.length} of ${total}`;
        },
        recordLabels() {
            return recordSortLabels[this.recordSortKey] ?? ["Ascending", "Descending"];
        },
    },
    watch: {
        selectedPath() {
            this.recordSearch = "";
            this.copied = false;
            this.$nextTick(this.scrollActiveIntoView);
        },
        // Browser back/forward or a link like /#/?level=acheron
        "$route.query.level"(value) {
            if (this.loading || this.$route.path !== "/") {
                return;
            }
            // A newer navigation wins over a pending URL update
            clearTimeout(this.urlTimer);
            const path = this.pathFromQuery(value);
            if (path !== this.selectedPath) {
                this.selectedPath = path;
            }
        },
    },
    async mounted() {
        // Hide loading spinner
        this.list = await fetchList();
        this.legacy = await fetchLegacy();
        this.editors = showEditors ? await fetchEditors() : [];
        this.players = await fetchPlayers();

        // Error handling
        if (!this.list) {
            this.errors = [
                "Failed to load list. Retry in a few minutes or notify list staff.",
            ];
        } else {
            this.errors.push(
                ...this.list
                    .filter(([_, err]) => err)
                    .map(([_, err]) => {
                        return `Failed to load level. (${err}.json)`;
                    })
            );
                        this.errors.push(
                ...this.legacy
                    .filter(([_, err]) => err)
                    .map(([_, err]) => {
                        return `Failed to load legacy level. (${err}.json)`;
                    })
            );
            if (showEditors && !this.editors) {
                this.errors.push("Failed to load list editors.");
            }
        }

        this.selectedPath = this.pathFromQuery(this.$route.query.level);
        this.loading = false;
        this.$nextTick(this.scrollActiveIntoView);

        window.addEventListener("keydown", this.onKeydown);
    },
    beforeUnmount() {
        window.removeEventListener("keydown", this.onKeydown);
        clearTimeout(this.urlTimer);
        clearTimeout(this.copyTimer);
    },
    methods: {
        embed,
        score,
        formatDate,
        countryOf(user) {
            return playerInfo(this.players, user).country;
        },
        rowLabel(entry) {
            return entry.level?.name || `Error (${entry.path}.json)`;
        },

        // The level named in the URL, or the #1 level
        pathFromQuery(value) {
            const wanted = Array.isArray(value) ? value[0] : value;
            return this.entries.some((e) => e.path === wanted)
                ? wanted
                : this.entries[0]?.path ?? null;
        },
        selectLevel(path, fromUserClick = false) {
            this.selectedPath = path;
            if (fromUserClick) {
                this.mobileView = "detail";
            }
            // Keep the URL in sync (delayed so holding an arrow key stays smooth)
            clearTimeout(this.urlTimer);
            this.urlTimer = setTimeout(() => {
                this.$router.replace({
                    path: "/",
                    query: { ...this.$route.query, level: path },
                });
            }, 250);
        },
        scrollActiveIntoView() {
            this.$el?.querySelector?.(".list .level.active")?.scrollIntoView({
                block: "nearest",
            });
        },

        // ----- Filters -----
        clearAll() {
            this.search = "";
            this.filterDifficulty = "";
            this.filterPerson = "";
            this.filterRecords = "";
            this.filterTag = "";
        },
        filterByTag(tag) {
            this.filterTag = tag;
            this.showFilters = true;
        },
        matches(entry) {
            const level = entry.level;
            if (!level) {
                return false;
            }
            const creators = level.creators || [];
            const lower = (v) => String(v ?? "").toLowerCase();

            // Search: name, creators, publisher, verifier, ID, tags, or "#12" for a rank
            const q = this.search.trim().toLowerCase();
            if (q) {
                if (/^#\d+$/.test(q)) {
                    if (entry.rank !== Number(q.slice(1))) return false;
                } else if (
                    ![
                        level.name,
                        level.author,
                        level.verifier,
                        level.id,
                        ...creators,
                        ...(level.tags || []),
                    ].some((v) => lower(v).includes(q))
                ) {
                    return false;
                }
            }

            if (this.filterDifficulty && level.difficulty !== this.filterDifficulty) {
                return false;
            }

            const person = this.filterPerson.trim().toLowerCase();
            if (
                person &&
                ![level.author, ...creators].some((n) => lower(n).includes(person))
            ) {
                return false;
            }

            if (this.filterRecords === "has" && level.records.length === 0) {
                return false;
            }
            if (this.filterRecords === "none" && level.records.length > 0) {
                return false;
            }

            if (
                this.filterTag &&
                !(level.tags || []).some((t) => lower(t) === lower(this.filterTag))
            ) {
                return false;
            }

            return true;
        },

        // ----- Keyboard -----
        // Enter in the search box opens the first result
        onSearchEnter(event) {
            if (event.target.tagName === "INPUT" && this.visible.length > 0) {
                this.selectLevel(this.visible[0].path);
            }
        },
        // Up/Down move through the list, Home/End jump to the first/last level
        onKeydown(event) {
            if (event.altKey || event.ctrlKey || event.metaKey || this.loading) {
                return;
            }
            const target = event.target;
            const tag = target.tagName;
            if (tag === "SELECT" || tag === "TEXTAREA" || target.isContentEditable) {
                return;
            }
            // In a text box only Up/Down are used, so typing and the cursor keep working
            if (tag === "INPUT" && !["ArrowUp", "ArrowDown"].includes(event.key)) {
                return;
            }

            let next = null;
            if (event.key === "ArrowDown") {
                next = this.visibleIndex === -1 ? this.visible[0] : this.nextEntry;
            } else if (event.key === "ArrowUp") {
                next = this.prevEntry;
            } else if (event.key === "Home" || event.key === "End") {
                next = event.key === "Home" ? this.visible[0] : this.visible.at(-1);
            } else {
                return;
            }

            // Stop the page from scrolling while navigating
            event.preventDefault();
            if (next && next.path !== this.selectedPath) {
                this.selectLevel(next.path);
                // Keep keyboard focus on the highlighted row when it started there
                if (target.closest?.(".list")) {
                    this.$nextTick(() =>
                        this.$el.querySelector(".list .level.active button")?.focus()
                    );
                }
            }
        },

        // ----- Copy ID -----
        async copyId() {
            const id = String(this.level.id);
            try {
                await navigator.clipboard.writeText(id);
            } catch {
                // Fallback for browsers/pages without clipboard access
                const box = document.createElement("textarea");
                box.value = id;
                box.style.position = "fixed";
                box.style.opacity = "0";
                document.body.appendChild(box);
                box.select();
                document.execCommand("copy");
                box.remove();
            }
            this.copied = true;
            clearTimeout(this.copyTimer);
            this.copyTimer = setTimeout(() => (this.copied = false), 1200);
        },
    },
};
