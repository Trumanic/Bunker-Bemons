
export default {
    props: {
        author: {
            type: String,
            required: true,
        },
        creators: {
            type: Array,
            required: true,
        },
        verifier: {
            type: String,
            default: '',
        },
        tags: {
            type: Array,
            default: () => [],
        },
    },

    emits: ['tag'],

    template: `
        <div class="level-authors">
            <template v-for="group in authorGroups" :key="group.label">
                <div class="type-title-sm">{{ group.label }}</div>
                <p class="type-body">
                    <template v-for="(person, index) in group.people" :key="person">
                        <span>{{ person }}</span><span v-if="index < group.people.length - 1">, </span>
                    </template>
                </p>
            </template>

            <template v-if="tags.length > 0">
                <div class="type-title-sm">Tags</div>
                <div class="tags">
                    <button
                        v-for="tag in tags"
                        :key="tag"
                        type="button"
                        class="tag type-label-md"
                        title="Show levels with this tag"
                        @click="$emit('tag', tag)"
                    >{{ tag }}</button>
                </div>
            </template>
        </div>
    `,

    computed: {
        authorGroups() {
            const publisher = this.author;
            const creators = this.creators.length > 0
                ? this.creators
                : [this.author];
            const verifier = this.verifier;

            // Determine whether the publisher and verifier
            // are the same person.
            const publisherIsVerifier =
                !!verifier && publisher === verifier;

            // A level with no separate creators is treated as
            // having the publisher as its creator.
            const creatorIsPublisher =
                creators.length === 1 && creators[0] === publisher;

            const creatorIsVerifier =
                !!verifier &&
                creators.length === 1 &&
                creators[0] === verifier;

            // All three roles belong to the same person.
            if (
                publisherIsVerifier &&
                creatorIsPublisher &&
                creatorIsVerifier
            ) {
                return [
                    {
                        label: 'Publisher, Creator, & Verifier',
                        people: [publisher],
                    },
                ];
            }

            // Publisher and verifier are the same person.
            if (publisherIsVerifier) {
                const groups = [
                    {
                        label: 'Publisher & Verifier',
                        people: [publisher],
                    },
                ];

                if (!creatorIsPublisher) {
                    groups.push({
                        label: creators.length > 1 ? 'Creators' : 'Creator',
                        people: creators,
                    });
                }

                return groups;
            }

            // Publisher and creator are the same person.
            if (creatorIsPublisher) {
                const groups = [
                    {
                        label: 'Publisher & Creator',
                        people: [publisher],
                    },
                ];

                if (verifier && verifier !== publisher) {
                    groups.push({
                        label: 'Verifier',
                        people: [verifier],
                    });
                }

                return groups;
            }

            // Creator and verifier are the same person.
            if (creatorIsVerifier) {
                return [
                    ...(publisher ? [{
                        label: 'Publisher',
                        people: [publisher],
                    }] : []),
                    {
                        label: 'Creator & Verifier',
                        people: [creators[0]],
                    },
                ];
            }

            // All roles are handled separately.
            return [
                ...(publisher ? [{
                    label: 'Publisher',
                    people: [publisher],
                }] : []),
                {
                    label: creators.length > 1 ? 'Creators' : 'Creator',
                    people: creators,
                },
                ...(verifier ? [{
                    label: 'Verifier',
                    people: [verifier],
                }] : []),
            ];
        },
    },
};
