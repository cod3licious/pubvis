<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { fetchData, getOrSetUserIdCookie } from "@/components/utils/helpers";
import { useHostname, useCookies, useHistoryStore } from "@/components/utils/DependencyInjection";
import type { Article, ArticleDetail, LoadingState } from "@/components/models/types";
import ItemList from "@/components/ItemList.vue";
import IconThumbsUp from "@/components/icons/IconThumbsUp.vue";
import IconThumbsDown from "@/components/icons/IconThumbsDown.vue";

const props = defineProps<{
    itemId: string;
}>();

const loadingState = ref<LoadingState>("loading");
const item = ref<ArticleDetail | null>(null);
const similarItems = ref<Article[]>([]);
const itemRated = ref<boolean>(false);
const hostname = useHostname();
const cookies = useCookies();
const router = useRouter();
const historyStore = useHistoryStore();

onMounted(() => {
    fetchItem(props.itemId);
});

watch(
    () => props.itemId,
    (newItemId) => {
        fetchItem(newItemId);
        itemRated.value = false;
    },
);

async function fetchItem(id: string) {
    loadingState.value = "loading";
    try {
        [item.value, similarItems.value] = await Promise.all([
            fetchData<ArticleDetail>(`${hostname}/items/${id}`),
            fetchData<Article[]>(`${hostname}/items/${id}/similar`),
        ]);
        loadingState.value = "loaded";
    } catch (e) {
        console.error(e);
        loadingState.value = "error";
    }
}

async function rateItem(rating: number) {
    // post request to /ratings endpoint with itemId, userId and rating
    const userId = getOrSetUserIdCookie(cookies);
    await fetch(`${hostname}/ratings`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            item_id: item.value?.item_id,
            user_id: userId,
            rating: rating,
        }),
    });
    itemRated.value = true;
}

async function rateYes() {
    rateItem(1.0);
}

async function rateNo() {
    rateItem(-1.0);
}

function openItem(newItem: Article) {
    // add new item to history and reload history page to show new item
    // TODO: conversion to Article doesn't really work as expected, still contains all fields
    historyStore.push(newItem!);
    router.go(0);
}
</script>

<template>
    <header v-if="loadingState != 'loaded'">loading...</header>
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
            <footer class="item-detail-footer flex-row x-space-1" v-if="!itemRated">
                <span>Is this article relevant for your research?</span>
                <div class="article-buttons flex-row x-space-1">
                    <button class="vote-button" @click="rateYes"><icon-thumbs-up></icon-thumbs-up> <span>Yes</span></button>
                    <button class="vote-button" @click="rateNo"><icon-thumbs-down></icon-thumbs-down> <span>No</span></button>
                </div>
            </footer>
            <footer class="item-detail-footer flex-row" v-if="itemRated">
                <span>Thank you, list of your recommended articles has been improved.</span>
            </footer>
        </div>
        <ItemList header="Similar articles" :articles="similarItems" @article-click="openItem($event)"></ItemList>
    </div>
</template>

<style scoped lang="scss">

.root-container {
    display: flex;
    flex-direction: row;
    height: 100vh;

    > aside {
        border: var(--color-border) solid;
        border-left-width: 1px;
    }
}

.item-container {
    display: flex;
    flex-direction: column;
    background-color: var(--color-background);

    main {
        flex: 1;
        padding: 1rem;

        .item-authors {
            text-align: center;
            font-style: italic;
        }

        .item-url {
            text-align: right;
        }

        *:not(:last-child) {
            margin-bottom: 1rem;
        }
    }

    footer {
        padding: 1em;
        width: 100%;
        justify-content: center;
        border-top: var(--color-border) solid 1px;

        .vote-button {
            background: none;
            padding: 0;
            border: none;
            color: var(--color-text);

            * {
                color: var(--color-text);
                fill: var(--color-text);
            }
        }
    }
}

header {
    font-size: 1.25rem;
}
</style>
