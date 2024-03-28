<script setup lang="ts">
import { onMounted, ref } from "vue";
import ItemDetail from "@/components/ItemDetail.vue";
import ItemList from "@/components/ItemList.vue";
import { fetchData, getOrSetUserIdCookie } from "@/components/utils/helpers";
import { useHostname, useCookies, useHistoryStore } from "@/components/utils/DependencyInjection";
import type { Article, LoadingState } from "@/components/models/types";

const loadingState = ref<LoadingState>("loading");
const recommendedItems = ref<Article[]>([]);
const hostname = useHostname();
const cookies = useCookies();
const userId = getOrSetUserIdCookie(cookies);
const historyStore = useHistoryStore();
const itemId = ref<string>();

onMounted(() => {
    fetchItems();
});

async function fetchItems() {
    loadingState.value = "loading";
    try {
        [recommendedItems.value] = await Promise.all([fetchData<Article[]>(`${hostname}/users/${userId}/recommendations`)]);
        loadingState.value = "loaded";
    } catch (e) {
        console.error(e);
        loadingState.value = "error";
    }
}

function openItem(item: Article) {
    historyStore.push(item);
    itemId.value = item.item_id;
}
</script>

<template>
    <header v-if="loadingState != 'loaded'">loading...</header>
    <div class="root-container" v-else>
        <ItemList header="Recommendations" :articles="recommendedItems" @article-click="openItem($event)"></ItemList>
        <ItemDetail v-model="itemId" v-if="itemId"></ItemDetail>
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
