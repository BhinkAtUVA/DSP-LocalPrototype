<script lang="ts">
    import Pseudopages from "$lib/components/layout/Pseudopages.svelte";
    import Details from "$lib/components/pseudopages/Details.svelte";
    import Landing from "$lib/components/pseudopages/Landing.svelte";
    import Preferences from "$lib/components/pseudopages/Preferences.svelte";
    import Proposals from "$lib/components/pseudopages/Proposals.svelte";
    import type { ModelInsight } from "$lib/optimizer.svelte";

    let optionAmount: number = $state(3)
    let discountMax: number = $state(2)
    let optimizationResult: Promise<Response> = $state(new Promise((resolve, reject) => resolve(new Response())))
    let modelInsights: ModelInsight[] = $state([])
    let selectedModel: number = $state(0)
</script>

{#snippet landing(next: () => void)}
    <Landing {next}></Landing>
{/snippet}
{#snippet preferences(next: () => void)}
    <Preferences {next} bind:options={optionAmount} bind:discounts={discountMax} bind:result={optimizationResult}></Preferences>
{/snippet}
{#snippet proposals(next: () => void)}
    <Proposals {next} options={optionAmount} discounts={discountMax} bind:modelInsights bind:selectedModel></Proposals>
{/snippet}
{#snippet details(next: () => void)}
    <Details {next} insight={modelInsights[selectedModel]}></Details>
{/snippet}


<Pseudopages pages={[{
    title: "Home",
    content: landing
}, {
    title: "Preferences",
    content: preferences,
}, {
    title: "Pricing structure",
    content: proposals
}, {
    title: "Details",
    content: details
}]}></Pseudopages>