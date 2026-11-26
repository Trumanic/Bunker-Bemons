export default {
    props: {
        mode: {
            type: String,
            required: true,
        },
    },
    emits: ['change'],
    template: `
        <div class="mode-switch" role="group" aria-label="Leaderboard mode">
            <button type="button" :class="{ active: mode === 'beaten' }" :aria-pressed="mode === 'beaten'" @click="$emit('change', 'beaten')">Beaten</button>
            <button type="button" :class="{ active: mode === 'created' }" :aria-pressed="mode === 'created'" @click="$emit('change', 'created')">Created</button>
        </div>
    `,
};