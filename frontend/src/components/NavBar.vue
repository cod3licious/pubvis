<script setup lang="ts">
import { useRoute } from "vue-router";

defineProps<{
    title?: string;
}>();

const route = useRoute();
</script>

<template>
    <nav class="side-bar">
        <router-link to="/" :class="{ selected: route.path == '/' }">Map</router-link>
        <router-link to="/search" :class="{ selected: route.path.startsWith('/search') }">Search</router-link>
        <router-link to="/recommended" :class="{ selected: route.path.startsWith('/recommended') }">Recommended</router-link>
        <router-link to="/history" :class="{ selected: route.path.startsWith('/history') }">History</router-link>
        <router-link to="/about" :class="{ selected: route.path.startsWith('/about') }">About</router-link>
    </nav>
</template>

<style scoped lang="scss">
.side-bar {
    display: flex;
    flex-direction: column;
    background-color: var(--color-background-soft);
    padding: 1rem;

    a,
    a:active {
        padding: 0.25em 0.5em;
        color: var(--color-text);
        margin-bottom: 0.25em;
        text-decoration: none;
    }

    a:hover {
        background-color: var(--color-background-mute);
        border-radius: 0.25em;
    }

    a.selected {
        background-color: var(--color-background-highlight);
        border-radius: 0.25em;
    }
}
</style>
