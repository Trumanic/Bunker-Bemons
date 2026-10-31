import routes from './routes.js';

function updateDocumentTheme(dark) {
    if (dark) {
        document.documentElement.classList.add('dark');
        document.body.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
        document.body.classList.remove('dark');
    }
}

const initialDark = JSON.parse(localStorage.getItem('dark')) || false;
updateDocumentTheme(initialDark);

export const store = Vue.reactive({
    dark: initialDark,
    toggleDark() {
        this.dark = !this.dark;
        localStorage.setItem('dark', JSON.stringify(this.dark));
        updateDocumentTheme(this.dark);
    },
});

const app = Vue.createApp({
    data: () => ({ store }),
});
const router = VueRouter.createRouter({
    history: VueRouter.createWebHashHistory(),
    routes,
});

app.use(router);

app.mount('#app');
