<script lang="ts">
    import type { ModelInsight } from "$lib/optimizer.svelte";
    import { Plot, BarY } from "svelteplot"

    let { next, insight }: { next: () => void, insight: ModelInsight } = $props()

    let hhIds = []
    for (let i = 0; i < 18; i++) {
        hhIds.push(i)
    }

</script>

<div class="max-w-300 mx-auto px-4 grid grid-cols-[1fr_1fr] grid-rows-[1fr_1fr] gap-8">
    <div>
        <div class="text-center text-2xl mb-4">Financial insight</div>
        <div class="grid grid-cols-[auto_1fr] gap-y-1 gap-x-4">
            <p>Monthly membership fee:</p><p class="text-right">{insight.baseFee.toFixed(2)} €</p>
            <p>Maximum simulated monthly overshoot (revenue - costs):</p><p class="text-right">{Array.from(Object.values(insight.overshoots)).reduce((prev, curr) => Math.max(prev, curr)).toFixed(2)} €</p>
        </div>
    </div>
    <div>
        <div class="text-center text-2xl">Mean Monthly Costs by Household</div>
        <Plot grid x={{ label: "Household ID" }} y={{ label: "Monthly Cost (€)" }}>
            <BarY data={
                hhIds.map(id => Math.max(insight.costsMean[id], 25))
            }></BarY>
        </Plot>
    </div>
    <div>
        <div class="text-center text-2xl">Mean Monthly Driven Hours by Household</div>
        <Plot grid x={{ label: "Household ID" }} y={{ label: "Monthly Driven Hours" }}>
            <BarY data={
                hhIds.map(id => insight.hoursMean[id])
            }></BarY>
        </Plot>
    </div>
    <div>
        <div class="text-center text-2xl">Mean Monthly Driven Kilometers by Household</div>
        <Plot grid x={{ label: "Household ID" }} y={{ label: "Monthly Driven Kilometers" }}>
            <BarY data={
                hhIds.map(id => insight.kmsMean[id])
            }></BarY>
        </Plot>
    </div>
</div>