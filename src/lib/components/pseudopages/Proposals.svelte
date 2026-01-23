<script lang="ts">
    import { optimizationInfo } from '$lib/optimizer.svelte';
    import ModelCard from '../ModelCard.svelte';
    import Spinner from '../ui/spinner/spinner.svelte';

    let { next, options }: { next: () => void, options: number } = $props()

    const loadingPhrases = ["Simulating rides", "Reviewing cooperative information", "Testing discounts", "Analyzing costs"]
    let phraseIndex = $state(0)

    function cyclePhrase() {
        phraseIndex++
        if (phraseIndex >= loadingPhrases.length) phraseIndex = 0
    }
    
    let cycleHandle: number | undefined
    $effect(() => {
        if (optimizationInfo.loading) {
            cycleHandle = setInterval(cyclePhrase, 2000)
        }
        else if (cycleHandle != undefined) {
            clearInterval(cycleHandle)
            cycleHandle = undefined
        }
    })
</script>

{#if optimizationInfo.loading}
    <div class="mx-auto flex gap-2 justify-center items-center">
        <Spinner></Spinner>
        {loadingPhrases[phraseIndex]}
    </div>
{:else}
    <div class="mx-auto max-w-300 px-4 grid gap-4 grid-cols-1 md:grid-cols-3">
        {#each { length: options }}
            <ModelCard mainprice={2.50} discounts={[{
                description: "Off-peak hours (19:00-24:00)",
                amount: 30
            }, {
                description: "Weekend",
                amount: 50
            }]} characteristics={[{
                label: "Heavy user friendliness",
                score: 2
            }, {
                label: "Competitiveness",
                score: 5
            }]} onclick={next}></ModelCard>
        {/each}
    </div>
{/if}