import "./assets/main.scss";

import { createApp } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import VueCookies from "vue-cookies";
import App from "./App.vue";
import Explore from "@/components/Explore.vue";
import About from "@/components/About.vue";
import Search from "@/components/Search.vue";
import Recommended from "@/components/Recommended.vue";
import History from "@/components/History.vue";
import ItemDetail from "@/components/ItemDetail.vue";
import { HistoryStore } from "@/components/utils/HistoryStore";
import { hostnameKey, historyStoreKey } from "@/components/utils/DependencyInjection";

const routes = [
    { path: "/", component: Explore },
    { path: "/search", component: Search },
    { path: "/recommended", component: Recommended },
    { path: "/history", component: History },
    { path: "/about", component: About },
    { path: "/items/:id", component: ItemDetail },
];

const router = createRouter({
    history: createWebHashHistory(),
    routes,
});

// TODO: try empty string for host to have relative links in dist folder
// hostname should be "http://127.0.0.1:8000" when running locally in dev mode while also running fastAPI
// live API is on "https://pubvis.onrender.com" or "https://arxvis.onrender.com"
createApp(App).provide(hostnameKey, "http://127.0.0.1:8000").provide(historyStoreKey, new HistoryStore()).use(router).use(VueCookies).mount("#app");
