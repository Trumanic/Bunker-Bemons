export default {
    props: {
        search: {
            type: String,
            default: '',
        },
        sortKey: {
            type: String,
            required: true,
        },
        sortDir: {
            type: String,
            default: 'desc',
        },
        // [{ value, label, defaultDir }]
        options: {
            type: Array,
            required: true,
        },
        placeholder: {
            type: String,
            default: 'Search',
        },
        // Search box on its own row, sort + direction below it
        stacked: {
            type: Boolean,
            default: false,
        },
        // Keep the direction word ("Newest") visible even when stacked
        showLabel: {
            type: Boolean,
            default: false,
        },
        // Wording for the direction button (e.g. "Newest" / "Oldest")
        ascLabel: {
            type: String,
            default: 'Ascending',
        },
        descLabel: {
            type: String,
            default: 'Descending',
        },
    },
    emits: ['update:search', 'update:sortKey', 'update:sortDir'],
    template: `
        <div class="search-sort" :class="{ stacked, labelled: showLabel }">
            <input
                type="text"
                :value="search"
                :placeholder="placeholder"
                :aria-label="placeholder"
                @input="$emit('update:search', $event.target.value)"
            >
            <select aria-label="Sort by" @change="changeKey($event.target.value)">
                <option
                    v-for="option in options"
                    :key="option.value"
                    :value="option.value"
                    :selected="option.value === sortKey"
                >{{ option.label }}</option>
            </select>
            <button
                type="button"
                class="direction"
                :class="{ asc: sortDir === 'asc' }"
                :title="label"
                :aria-label="'Sort order: ' + label + '. Click to reverse.'"
                @click="$emit('update:sortDir', sortDir === 'asc' ? 'desc' : 'asc')"
            >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12 4v15m0 0l-6-6m6 6l6-6" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <span class="direction__label">{{ label }}</span>
            </button>
        </div>
    `,
    computed: {
        label() {
            return this.sortDir === 'asc' ? this.ascLabel : this.descLabel;
        },
    },
    methods: {
        changeKey(value) {
            this.$emit('update:sortKey', value);
            // Each sort option starts in the direction that makes sense for it
            const option = this.options.find((o) => o.value === value);
            if (option?.defaultDir) {
                this.$emit('update:sortDir', option.defaultDir);
            }
        },
    },
};
