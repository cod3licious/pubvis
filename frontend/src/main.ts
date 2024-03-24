import "./assets/main.scss";

import { createApp, inject, type InjectionKey } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import App from "./App.vue";
import Explore from "@/components/Explore.vue";
import About from "@/components/About.vue";
import Search from "@/components/Search.vue";
import Recommended from "@/components/Recommended.vue";
import History from "@/components/History.vue";
import ItemDetail from "@/components/ItemDetail.vue";
import { HistoryStore } from "@/components/utils/HistoryStore";

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

const hostnameKey = Symbol() as InjectionKey<string>;

export function useHostname(): string {
    return inject(hostnameKey)!;
}

const historyStoreKey = Symbol() as InjectionKey<HistoryStore>;

export function useHistoryStore(): HistoryStore {
    return inject(historyStoreKey)!;
}

createApp(App).provide(hostnameKey, "http://127.0.0.1:8000").provide(historyStoreKey, new HistoryStore()).use(router).mount("#app");
