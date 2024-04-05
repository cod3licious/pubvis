<script setup lang="ts">
const props = defineProps<{
    percentage: number;
}>();
</script>

<template>
    <div class="svg-item">
        <svg width="100%" height="100%" viewBox="0 0 40 40" class="donut">
            <circle class="donut-ring" cx="20" cy="20" r="15.91549430918954" fill="transparent" stroke-width="3.5"></circle>
            <circle
                class="donut-segment"
                cx="20"
                cy="20"
                r="15.91549430918954"
                fill="transparent"
                stroke-width="3.5"
                :stroke-dasharray="`${props.percentage} ${100 - props.percentage}`"
                stroke-dashoffset="25"
                stroke-linecap="round"
            ></circle>
            <g class="donut-text">
                <text y="50%" transform="translate(0, 2)">
                    <tspan x="50%" text-anchor="middle" class="donut-percent">{{ percentage.toFixed(1) }}%</tspan>
                </text>
            </g>
        </svg>
    </div>
</template>

<style scoped lang="scss">
.svg-item {
    width: 100%;
    margin: 0 auto;
}

.donut-ring {
    stroke: var(--color-background-soft);
}

.donut-segment {
    transform-origin: center;
    stroke: var(--color-text-link);
}

.donut-text {
    fill: var(--color-text);
}

.donut-percent {
    font-size: 0.5em;
    line-height: 1;
    font-weight: bold;
}
</style>
