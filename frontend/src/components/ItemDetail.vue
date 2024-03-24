<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { LoadingState } from "@/components/models/types";
import { fetchData } from "@/components/utils/helpers";
import { useHostname } from "@/main";
import IconThumbsUp from "@/components/icons/IconThumbsUp.vue";
import IconThumbsDown from "@/components/icons/IconThumbsDown.vue";

const props = defineProps<{
    itemId: string;
}>();

type Item = {
    item_id: string;
    title: string;
    description: string;
    pub_date: string;
    pub_year: number;
    keywords: string;
    authors: string;
    publisher: string;
    item_url: string;
};
type ScoredItem = Item & { score: number };

const loadingState = ref<LoadingState>("loading");
const item = ref<Item | null>(null);
const similarItems = ref<ScoredItem[] | null>(null);
const hostname = useHostname();

onMounted(() => {
    fetchItem(props.itemId);
});

async function fetchItem(id: string) {
    loadingState.value = "loading";
    try {
        [item.value, similarItems.value] = await Promise.all([
            fetchData<Item>(`${hostname}/items/${id}`),
            fetchData<ScoredItem[]>(`${hostname}/items/${id}/similar`),
        ]);
        loadingState.value = "loaded";
        console.log(item.value.item_url);
    } catch (e) {
        console.error(e);
        loadingState.value = "error";
    }
}
</script>

<template>
    <header v-if="loadingState != 'loaded'">item id is {{ itemId }} and state is {{ loadingState }}</header>
    <div class="root-container" v-else>
        <div class="item-container">
            <main class="scroll-container">
                <p>{{ item?.publisher }}, {{ item?.pub_year }}</p>
                <h2>
                    {{ item?.title }}
                </h2>
                <p class="item-authors">{{ item?.authors }}</p>
                <p>{{ item?.description }}</p>
                <p class="item-url"><a :href="item?.item_url" target="_blank">view original article</a></p>
            </main>
            <footer class="item-detail-footer flex-row">
                <span>Is this article relevant for your research?</span>
                <div class="article-buttons">
                    <button class="article-yes"><icon-thumbs-up></icon-thumbs-up> Yes</button>
                    <button class="article-no"><icon-thumbs-down></icon-thumbs-down> No</button>
                </div>
            </footer>
        </div>
        <aside class="similar-items-container">
            <h2>Similar articles</h2>
            <div class="scroll-container">
                <article v-for="simitem in similarItems" :key="simitem.item_id">
                    <h4>{{ simitem.title }}</h4>
                    <p>{{ simitem.pub_year }}, {{ simitem.authors }}</p>
                </article>
            </div>
        </aside>
    </div>
</template>

<style scoped lang="scss">
$bla-black: #11151d;

.root-container {
    display: flex;
    flex-direction: row;
    height: 100vh;
}

.item-container {
    display: flex;
    flex-direction: column;
    background-color: #2c3e50;
}

.item-container > main {
    flex: 1;
    padding: 1rem;
}

.item-container > main > .item-authors {
    text-align: center;
    font-style: italic;
}

.item-container > main > .item-url {
    text-align: right;
}

.item-container > main > *:not(:last-child) {
    margin-bottom: 1rem;
}

.item-detail-footer {
    border-top: $bla-black solid 1px;
}

.similar-items-container {
    display: flex;
    flex-direction: column;
    flex: 0 0 20rem;
    background-color: darkslategray;
}

.similar-items-container > h2 {
    background-color: $bla-black;
}

.similar-items-container > .scroll-container {
    flex-grow: 1;
}

.similar-items-container article {
    padding: 0.5rem;
    border: $bla-black solid;
    border-width: 0 0 1px 1px;
}

.scroll-container {
    overflow-y: scroll;
}

header {
    font-size: 1.25rem;
}
</style>
