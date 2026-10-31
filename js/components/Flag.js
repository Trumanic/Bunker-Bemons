import { countryName, normalizeCountry } from '../util.js';

/**
 * Country flag from /assets/flags/<code>.svg
 * Renders nothing when there is no code or the flag file doesn't exist.
 */
export default {
    props: {
        code: {
            type: String,
            default: '',
        },
    },
    data: () => ({
        failed: false,
    }),
    template: `
        <img
            v-if="src && !failed"
            class="flag"
            :src="src"
            :alt="name"
            :title="name"
            @error="failed = true"
        >
    `,
    computed: {
        normalized() {
            return normalizeCountry(this.code);
        },
        src() {
            return this.normalized ? `/assets/flags/${this.normalized}.svg` : null;
        },
        name() {
            return countryName(this.normalized);
        },
    },
    watch: {
        code() {
            this.failed = false;
        },
    },
};
