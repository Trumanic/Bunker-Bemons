const extensions = ['png', 'jpg', 'jpeg', 'webp'];

// "assets/pfps/amine.png" and "amine.png" -> /assets/pfps/amine.png
// Full links, /paths and data: URIs are kept as they are
function resolvePfp(value) {
    const v = String(value ?? '').trim();
    if (!v) {
        return null;
    }
    if (/^(https?:)?\/\/|^data:/i.test(v) || v.startsWith('/')) {
        return v;
    }
    const path = v.includes('/') ? v : `assets/pfps/${v}`;
    return '/' + path.split('/').map(encodeURIComponent).join('/');
}

export default {
    props: {
        name: {
            type: String,
            required: true,
        },
        // Picture set for this player in data/players.json (optional)
        pfp: {
            type: String,
            default: '',
        },
    },
    data: () => ({
        attempt: 0,
        loaded: false,
    }),
    template: `
        <div class="avatar">
            <span class="avatar__initial">{{ initial }}</span>
            <img
                v-if="src"
                v-show="loaded"
                :key="src"
                :src="src"
                :alt="name + ' profile picture'"
                @load="loaded = true"
                @error="onError"
            >
        </div>
    `,
    computed: {
        // 1. the picture from players.json
        // 2. /assets/pfps/<lowercase name>.<png|jpg|jpeg|webp>
        candidates() {
            const file = encodeURIComponent(this.name);
            return [
                resolvePfp(this.pfp),
                ...extensions.map((ext) => `/assets/pfps/${file}.${ext}`),
            ].filter(Boolean);
        },
        src() {
            return this.candidates[this.attempt] ?? null;
        },
        initial() {
            return [...this.name.trim()][0]?.toUpperCase() ?? '?';
        },
    },
    watch: {
        name() {
            this.attempt = 0;
            this.loaded = false;
        },
        pfp() {
            this.attempt = 0;
            this.loaded = false;
        },
    },
    methods: {
        onError() {
            this.loaded = false;
            this.attempt++;
        },
    },
};
