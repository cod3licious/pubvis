import type { Article } from "@/components/models/types";

export class HistoryStore {
    private key = "history";
    private store = window.localStorage;

    get(): Article[] {
        const historyJson = this.store.getItem(this.key) ?? "[]";
        return JSON.parse(historyJson);
    }

    push(item: Article) {
        const history = this.get().filter((article: Article) => article.item_id !== item.item_id);
        var itemCopy = Object.assign({}, item);
        itemCopy.score = undefined;
        history.unshift(itemCopy);
        this.store.setItem(this.key, JSON.stringify(history));
    }

    clear() {
        this.store.removeItem(this.key);
    }
}
