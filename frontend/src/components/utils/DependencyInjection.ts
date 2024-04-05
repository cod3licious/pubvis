import { inject, type InjectionKey } from "vue";
import type { VueCookies } from "vue-cookies";
import { HistoryStore } from "@/components/utils/HistoryStore";

export const hostnameKey = Symbol() as InjectionKey<string>;

export function useHostname(): string {
    return inject(hostnameKey)!;
}

export const historyStoreKey = Symbol() as InjectionKey<HistoryStore>;

export function useHistoryStore(): HistoryStore {
    return inject(historyStoreKey)!;
}

export function useCookies(): VueCookies {
    return inject("$cookies")!;
}
