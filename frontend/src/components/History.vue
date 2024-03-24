<script setup lang="ts">
import ItemDetail from "@/components/ItemDetail.vue";
import { onMounted, ref } from "vue";
import { useHistoryStore } from "@/main";

const historyStore = useHistoryStore();
const itemId = ref<string>();

onMounted(() => {
    const history = historyStore.get();
    itemId.value! = history[history.length - 1]?.item_id;
});
</script>

<template>
    <ItemDetail :item-id="itemId" v-if="itemId"></ItemDetail>
</template>

<style scoped></style>
