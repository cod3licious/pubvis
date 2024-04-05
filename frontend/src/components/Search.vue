<script setup lang="ts">
import { ref } from "vue";
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
    // reset the other search field so that only one search is active at a time
    searchText.value = "";
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
    searchTerm.value = "";
    try {
        searchResults.value = (await (
            await fetch(`${hostname}/items/similar`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    q: searchText.value,
                }),
            })
        ).json()) as Article[];
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
        <div class="content-container" v-else>
            <div class="search-container">
                <div>
                    <label for="keyword-search">Match in title or authors:</label><br />
                    <input id="keyword-search" type="text" v-model="searchTerm" @input="keywordSearch" placeholder="Enter title or author" />
                </div>

                <div>
                    <label for="fulltext-comparison">Fulltext match in article abstract:</label><br />
                    <textarea
                        id="fulltext-comparison"
                        rows="20"
                        cols="60"
                        v-model="searchText"
                        @input="fulltextComparisonSearch"
                        placeholder="Enter an abstract for a fulltext search"
                    ></textarea>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped lang="scss">
.root-container {
    display: flex;
    flex-direction: row;
    height: 100vh;
    width: 100%;

    > aside {
        border: var(--color-border) solid;
        border-right-width: 1px;
    }

    > .content-container {
        flex-grow: 1;
        display: flex;
    }

    .search-container {
        display: flex;
        width: fit-content;
        flex-direction: column;
        margin: auto;
        justify-content: center;

        > div {
            margin: 0.5rem;
        }

        input,
        textarea {
            width: 100%;
        }
    }
}
</style>
