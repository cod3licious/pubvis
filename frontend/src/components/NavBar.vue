<script setup lang="ts">
defineProps<{
    title?: string;
}>();
</script>

<template>
    <nav class="side-bar">
        <router-link to="/">Map</router-link>
        <router-link to="/search">Search</router-link>
        <router-link to="/recommended">Recommended</router-link>
        <router-link to="/history">History</router-link>
        <router-link to="/about">About</router-link>
    </nav>
</template>

<style scoped>
.side-bar {
    display: flex;
    flex-direction: column;
    background-color: darkgrey;
    padding: 1rem;
}
</style>
