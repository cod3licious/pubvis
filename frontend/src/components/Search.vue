<script setup lang="ts">
import { onMounted, ref } from "vue";
import ItemDetail from "@/components/ItemDetail.vue";
import ItemList from "@/components/ItemList.vue";
import type { Article, LoadingState } from "@/components/models/types";
import { fetchData } from "@/components/utils/helpers";
import { useHostname, useHistoryStore } from "@/components/utils/DependencyInjection";

const loadingState = ref<LoadingState>("idle");
const itemId = ref<string>();
const searchResults = ref<Article[]>([]);
const hostname = useHostname();
const historyStore = useHistoryStore();
const searchTerm = ref<string>();
const searchText = ref<string>();

function openItem(item: Article) {
    historyStore.push(item);
    itemId.value = item.item_id;
}

async function keywordSearch() {
    loadingState.value = "loading";
    try {
        [searchResults.value] = await Promise.all([fetchData<Article[]>(`${hostname}/items/search?q=${searchTerm.value}`)]);
        loadingState.value = "loaded";
    } catch (e) {
        console.error(e);
        loadingState.value = "error";
    }
}

async function fulltextComparisonSearch() {
    loadingState.value = "loading";
    try {
        searchResults.value = await (await fetch(`${hostname}/items/similar`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                q: searchText.value,
            }),
        })).json() as Article[];
        loadingState.value = "loaded";
    } catch (e) {
        console.error(e);
        loadingState.value = "error";
    }
}

</script>

<template>
    <div class="root-container">
        <ItemList header="Search Results" :articles="searchResults" @article-click="openItem($event)"></ItemList>
        <ItemDetail v-model="itemId" v-if="itemId"></ItemDetail>
        <div class="search-container" v-else>
            <input type="text" v-model="searchTerm" @input="keywordSearch" placeholder="Search for articles">
            <button @click="keywordSearch">Search</button>
            <input type="text" v-model="searchText" @input="fulltextComparisonSearch" placeholder="Fulltext comparions search for articles">
            <button @click="fulltextComparisonSearch">Fulltext Search</button>
        </div>
    </div>
</template>

<style scoped lang="scss">
.root-container {
    display: flex;
    flex-direction: row;
    height: 100vh;

    > aside {
        border: var(--color-border) solid;
        border-right-width: 1px;
    }
}
</style>
