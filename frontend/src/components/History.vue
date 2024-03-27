<script setup lang="ts">
import { onMounted, ref } from "vue";
import ItemDetail from "@/components/ItemDetail.vue";
import ItemList from "@/components/ItemList.vue";
import { useHistoryStore } from "@/components/utils/DependencyInjection";
import type { Article } from "@/components/models/types";

const historyStore = useHistoryStore();
const itemId = ref<string>();

onMounted(() => {
    const history = historyStore.get();
    itemId.value! = history[0]?.item_id;
});

function openItem(item: Article) {
    itemId.value = item.item_id;
}
</script>

<template>
    <div class="root-container">
        <ItemList header="History" :articles="historyStore.get()" @article-click="openItem($event)"></ItemList>
        <ItemDetail :item-id="itemId" v-if="itemId"></ItemDetail>
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
