<script lang="ts">
    import { optimizationInfo, type ModelInsight } from '$lib/optimizer.svelte';
    import ModelCard from '../ModelCard.svelte';
    import Spinner from '../ui/spinner/spinner.svelte';

    let { next, options, discounts, modelInsights = $bindable(), selectedModel = $bindable() }: { next: () => void, options: number, discounts: number, modelInsights: ModelInsight[], selectedModel: number } = $props()

    const loadingPhrases = ["Simulating rides", "Reviewing cooperative information", "Testing discounts", "Analyzing costs"]
    let phraseIndex = $state(0)

    function cyclePhrase() {
        phraseIndex++
        if (phraseIndex >= loadingPhrases.length) phraseIndex = 0
    }
    
    let summaryData: any[] = $state([])
    
    let cycleHandle: number | undefined
    let data: any[] = []
    $effect(() => {
        if (!optimizationInfo.hasResult) {
            cycleHandle = setInterval(cyclePhrase, 2000)
        }
        else {
            if (cycleHandle == undefined) return
            clearInterval(cycleHandle)
            cycleHandle = undefined
            data = (optimizationInfo.currentResult as any[])
                .filter(r => r.summary.model_variant == "BASE" || (r.summary.model_variant as string).split("_").length <= discounts)
                .filter((r, i, arr) => {
                    let rparams = r.summary.params
                    for(let j = 0; j < arr.length; j++) {
                        let sparams = arr[j].summary.params
                        let equal = true
                        for(let key in rparams) {
                            if (key.includes("pct")) {
                                if (Math.round(rparams[key] * 100) != Math.round(sparams[key] * 100)) {
                                    equal = false
                                    break
                                }
                                continue
                            }
                            if (key.includes("hours")) {
                                if (Math.round(rparams[key]) != Math.round(sparams[key])) {
                                    equal = false
                                    break
                                }
                                continue
                            }
                            if (rparams[key].toFixed(2) != sparams[key].toFixed(2)) {
                                equal = false
                                break
                            }
                        }
                        if (equal) {
                            if (i == j) return true
                            return false
                        }
                    }
                    return false
                })
                .sort((a, b) => a.summary.objective_value - b.summary.objective_value)
                .slice(0, options)
            let ids = []
            for(let i = 0; i < 12; i++) {
                ids.push(i)
            }
            modelInsights = []
            summaryData = []
            data.forEach((modelResult, i) => {
                modelInsights.push({
                    ids: ids,
                    costsMean: modelResult.costsMean.cost,
                    hoursMean: modelResult.costsMean.hours,
                    kmsMean: modelResult.costsMean.km,
                    costsCIHalf: modelResult.costsCIHalf.cost,
                    hoursCIHalf: modelResult.costsCIHalf.hours,
                    kmsCIHalf: modelResult.costsCIHalf.km,
                    overshoots: modelResult.gaps.map((g: any) => g.Profit),
                    baseFee: 25
                })
                
                let heavy = modelResult.summary.obj_heavy
                let prop = modelResult.summary.obj_proportionality
                let csummaryData: any = {
                    heavyScore: Number(heavy < 1) + Number(heavy < 0.5) + Number(heavy < 0.1) + Number(heavy < 0.05) + Number(heavy < 0.01),
                    propScore: Number(prop < 1) + Number(prop < 0.5) + Number(prop < 0.1) + Number(prop < 0.05) + Number(prop < 0.01),

                    hourPrice: modelResult.summary.params.hour_rate,
                    kmPrice: modelResult.summary.params.km_rate,
                    baseFee: 25,
                    heavyDiscount: Math.round(modelResult.summary.params.heavy_discount_pct * 100),
                    heavyHours: Math.round(modelResult.summary.params.heavy_threshold_hours),
                    offpeakDiscount: Math.round(modelResult.summary.params.offpeak_discount_pct * 100),
                    weekendDiscount: Math.round(modelResult.summary.params.weekend_discount_pct * 100),
                    discounts: []
                }
                if (csummaryData.heavyDiscount > 0) csummaryData.discounts.push({
                    description: "Monthly hours > " + csummaryData.heavyHours.toString(),
                    amount: csummaryData.heavyDiscount
                })
                if (csummaryData.offpeakDiscount > 0) csummaryData.discounts.push({
                    description: "Driving between 9am and 4pm or after 6:30pm",
                    amount: csummaryData.offpeakDiscount
                })
                if (csummaryData.weekendDiscount > 0) csummaryData.discounts.push({
                    description: "Driving on the weekend",
                    amount: csummaryData.weekendDiscount
                })
                summaryData.push(csummaryData)
            })
        }
    })
</script>

{#if !optimizationInfo.hasResult}
    <div class="mx-auto flex gap-2 justify-center items-center">
        <Spinner></Spinner>
        {loadingPhrases[phraseIndex]}
    </div>
{:else}
    <div class="mx-auto max-w-300 px-4 grid gap-4 grid-cols-1 md:grid-cols-3">
        {#each summaryData as d, i}
            <ModelCard hourprice={d.hourPrice} kmprice={d.kmPrice} baseprice={d.baseFee} discounts={d.discounts} characteristics={[{
                label: "Heavy user friendly",
                score: d.heavyScore
            }, {
                label: "Proportional to usage",
                score: d.propScore
            }]} onclick={() => {
                selectedModel = i
                next()
            }}></ModelCard>
        {/each}
    </div>
{/if}