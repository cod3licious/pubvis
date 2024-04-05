<script setup lang="ts">
import * as d3 from "d3";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import type { Article, LoadingState } from "@/components/models/types";
import { fetchData } from "@/components/utils/helpers";
import { useHistoryStore, useHostname } from "@/components/utils/DependencyInjection";

const router = useRouter();
const historyStore = useHistoryStore();
const hostname = useHostname();

type MapDataPoint = {
    item_id: string;
    x: number;
    y: number;
    color: string;
};

type TooltipInfo = {
    title: string;
    journal: string;
    authors: string;
};

const mapRef = ref<HTMLElement>();
const loadingState = ref<LoadingState>("idle");
const tooltipInfo = ref<TooltipInfo | null>(null);

onMounted(() => {
    fetchDataAndUpdateUI();
});

async function fetchDataAndUpdateUI() {
    loadingState.value = "loading";
    try {
        const [articleInfo, mapPoints] = await Promise.all([
            fetchData<Record<string, Article>>(`${hostname}/static_json_item_info`),
            fetchData<MapDataPoint[]>(`${hostname}/static_json_xyc`),
        ]);
        loadingState.value = "loaded";

        displayGraph(articleInfo, mapPoints);
    } catch (e) {
        console.error(e);
        loadingState.value = "error";
    }
}

function displayGraph(articleInfo: Record<string, Article>, mapPoints: MapDataPoint[]) {
    const mapRefValue = mapRef.value!;
    mapRefValue.innerHTML = "";

    // Width and height
    const mapWidth = mapRefValue.clientWidth;
    const mapHeight = mapRefValue.clientHeight;
    const circleRadius = 4;
    const offset = circleRadius;
    const xMin = d3.min(mapPoints, (d: MapDataPoint) => d.x)! - offset;
    const xMax = d3.max(mapPoints, (d: MapDataPoint) => d.x)! + offset;
    const xRange = xMax - xMin;

    const yMin = d3.min(mapPoints, (d: MapDataPoint) => d.y)! - offset;
    const yMax = d3.max(mapPoints, (d: MapDataPoint) => d.y)! + offset;
    const yRange = yMax - yMin;

    // Create SVG element
    const svg = d3.select(mapRefValue).append("svg").attr("preserveAspectRatio", "none").attr("viewBox", `0 0 ${mapWidth} ${mapHeight}`).append("g");

    // Add the data points
    const circles = svg
        .selectAll<SVGSVGElement, MapDataPoint>("circle")
        .data(mapPoints, (d) => d.item_id)
        .enter()
        .append("circle")
        .attr("cx", (d: MapDataPoint) => (mapWidth * (d.x - xMin)) / xRange)
        .attr("cy", (d: MapDataPoint) => (mapHeight * (d.y - yMin)) / yRange)
        .attr("r", circleRadius)
        .attr("fill", (d: MapDataPoint) => d.color)
        .attr("stroke", "black")
        .attr("stroke-width", 0.1)
        .attr("opacity", 0.4);

    // Include mouseover effects
    circles
        .on("mouseover", (_, d: MapDataPoint) => {
            // Update the tooltip
            const article = articleInfo[d.item_id]!;
            tooltipInfo.value = {
                title: article.title,
                authors: article.authors,
                journal: `${article.publisher} (${article.pub_year})`,
            };
        })
        .on("mouseout", () => {
            // Hide the tooltip
            tooltipInfo.value = null;
        })
        .on("click", (_, d: MapDataPoint) => {
            // add current item to history
            historyStore.push(articleInfo[d.item_id]!);
            // go to history page to show article details
            router.push(`history`);
        });
}
</script>

<template>
    <main>
        <div class="preloader" v-if="loadingState === 'loading'">loading...</div>
        <div class="preloader" v-if="loadingState === 'error'">
            <button @click="fetchDataAndUpdateUI()">reload</button>
        </div>

        <div class="map-container">
            <div class="map" ref="mapRef"></div>
        </div>

        <div id="tooltip" v-if="tooltipInfo">
            <p id="journal">{{ tooltipInfo.journal }}</p>
            <h4 id="title">{{ tooltipInfo.title }}</h4>
            <p id="authors">{{ tooltipInfo.authors }}</p>
        </div>
    </main>
</template>

<style scoped lang="scss">
main {
    width: 100%;
    height: 100vh;
    position: relative;
    background-color: var(--color-background);
}

.map-container {
    width: 100%;
    height: 100%;
    padding: 4rem 3rem 8rem 3rem;
}

.map {
    width: 100%;
    height: 100%;
    cursor: pointer;
}

::v-deep(svg) {
    width: 100%;
    height: 100%;
}

.preloader {
    position: absolute;
    left: 50%;
    top: 50%;
    color: var(--color-text);
}

#tooltip {
    background: var(--color-background-mute);
    font-size: 0.9rem;
    position: absolute;
    width: 100%;
    transition: bottom 0.5s;
    padding: 20px;
    bottom: 0;
    pointer-events: none;

    #journal {
        font-size: 0.65rem;
        font-style: italic;
    }

    h4 {
        max-width: 540px;
        margin: 0 auto 11px;
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--color-heading);
    }

    p {
        max-width: 540px;
        margin: 0 auto;
        font-size: 0.675rem;
    }
}
</style>
