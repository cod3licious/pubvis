import type { Article } from "@/components/models/types";

export class HistoryStore {
    private key = "history";
    private store = window.localStorage;

    get(): Article[] {
        const historyJson = this.store.getItem(this.key) ?? "[]";
        return JSON.parse(historyJson);
    }

    push(item: Article) {
        const history = this.get();
        history.push(item);
        this.store.setItem(this.key, JSON.stringify(history));
    }

    clear() {
        this.store.removeItem(this.key);
    }
}
