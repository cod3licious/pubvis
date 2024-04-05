<script setup lang="ts">
import { defineProps, defineEmits } from "vue";
import type { Article } from "@/components/models/types";
import DonutChart from "@/components/DonutChart.vue";

const props = defineProps<{
    header: string;
    articles: Article[];
}>();

const emit = defineEmits<{
    articleClick: [article: Article];
}>();
</script>

<template>
    <aside class="item-list-container">
        <h2>{{ props.header }}</h2>
        <div class="scroll-container">
            <article v-for="item in props.articles" :key="item.item_id" @click="emit('articleClick', item)">
                <div class="chart" v-if="item.score">
                    <donut-chart :percentage="item.score"></donut-chart>
                </div>
                <div class="item-text">
                    <h4>{{ item.title }}</h4>
                    <p>{{ item.pub_year }}, {{ item.authors }}</p>
                </div>
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
        display: flex;
        flex-direction: row;
        padding: 0.5rem;
        border: var(--color-border) solid;
        border-width: 0 0 1px 0;

        > .chart {
            margin-right: 0.5rem;
            flex: 0 0 4rem;
            align-self: center;
        }

        > .item-text {
            flex-grow: 1;
        }

        h4 {
            font-weight: 400;
            color: var(--color-text-link);
        }
        p {
            font-size: 0.75rem;
            font-style: italic;
        }
    }
}
</style>
