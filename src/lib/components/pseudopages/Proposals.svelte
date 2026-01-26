<script lang="ts">
    import { optimizationInfo, type ModelInsight } from '$lib/optimizer.svelte';
    import ModelCard from '../ModelCard.svelte';
    import Spinner from '../ui/spinner/spinner.svelte';

    let { next, options, result, modelInsight = $bindable() }: { next: () => void, options: number, result: Promise<Response>, modelInsight: ModelInsight } = $props()

    const loadingPhrases = ["Simulating rides", "Reviewing cooperative information", "Testing discounts", "Analyzing costs"]
    let phraseIndex = $state(0)

    function cyclePhrase() {
        phraseIndex++
        if (phraseIndex >= loadingPhrases.length) phraseIndex = 0
    }
    
    let heavy
    let prop
    let heavyScore = $state(0)
    let propScore = $state(0)

    let hourPrice = $state(0)
    let kmPrice = $state(0)
    let heavyDiscount = $state(0)
    let heavyHours = $state(0)
    
    let cycleHandle: number | undefined
    let data: any = {}
    $effect(() => {
        if (!optimizationInfo.hasResult) {
            cycleHandle = setInterval(cyclePhrase, 2000)
        }
        else {
            if (cycleHandle == undefined) return
            clearInterval(cycleHandle)
            cycleHandle = undefined
            data = optimizationInfo.currentResult
            modelInsight = {
                ids: data.costs.ID_hh,
                costs: data.costs.cost,
                hours: data.costs.hours,
                kms: data.costs.km,
                overshoot: data.gaps[0].Profit,
                baseFee: data.summary.fixed_monthly_fee_per_household
            }

            heavy = data.summary.heavy_obj
            prop = data.summary.proportionality_obj
            heavyScore = Number(heavy < 1) + Number(heavy < 0.5) + Number(heavy < 0.1) + Number(heavy < 0.05) + Number(heavy < 0.01)
            propScore = Number(prop < 1) + Number(prop < 0.5) + Number(prop < 0.1) + Number(prop < 0.05) + Number(prop < 0.01)

            hourPrice = data.summary.params.hour_rate
            kmPrice = data.summary.params.km_rate
            heavyDiscount = Math.round(data.summary.params.heavy_discount_pct * 100)
            heavyHours = Math.round(data.summary.params.heavy_threshold_hours)
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
        {#each { length: options }}
            <ModelCard hourprice={hourPrice} kmprice={kmPrice} baseprice={modelInsight.baseFee} discounts={[{
                description: "Monthly Hours > " + heavyHours.toString(),
                amount: heavyDiscount
            }]} characteristics={[{
                label: "Heavy user friendly",
                score: heavyScore
            }, {
                label: "Proportional to usage",
                score: propScore
            }]} onclick={next}></ModelCard>
        {/each}
    </div>
{/if}