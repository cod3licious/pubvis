<script setup lang="ts">
import { onMounted, ref, defineProps, defineEmits } from "vue";
import type { Article } from "@/components/models/types";

const props = defineProps<{
    header: string;
    articles: Article[];
}>();

const emit = defineEmits<{
    articleClick: [article: Article]
}>();
</script>

<template>
        <aside class="item-list-container">
            <h2>{{ props.header }}</h2>
            <div class="scroll-container">
                <article v-for="item in props.articles" :key="item.item_id" @click="emit('articleClick', item)">
                    <!-- TODO: add donut for similarity score on the side is score is not undefined -->
                    <h4>{{ item.title }}</h4>
                    <p>{{ item.pub_year }}, {{ item.authors }}</p>
                </article>
            </div>
        </aside>
</template>

<style scoped lang="scss">

.item-list-container {
    display: flex;
    flex: 0 0 20rem;
    flex-direction: column;
    background-color: var(--color-background);

    h2 {
        background-color: var(--color-background-mute);
        padding: 0.5rem;
    }

    .scroll-container {
        height: 100%;
    }

    article {
        padding: 0.5rem;
        border: var(--color-border) solid;
        border-width: 0 0 1px 0;
    }
}
</style>
