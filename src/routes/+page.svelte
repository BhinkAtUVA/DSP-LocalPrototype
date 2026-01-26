<script lang="ts">
    import Pseudopages from "$lib/components/layout/Pseudopages.svelte";
    import Cooperative from "$lib/components/pseudopages/Cooperative.svelte";
    import Details from "$lib/components/pseudopages/Details.svelte";
    import Landing from "$lib/components/pseudopages/Landing.svelte";
    import Preferences from "$lib/components/pseudopages/Preferences.svelte";
    import Proposals from "$lib/components/pseudopages/Proposals.svelte";
    import type { ModelInsight } from "$lib/optimizer.svelte";

    let optionAmount: number = $state(1)
    let optimizationResult: Promise<Response> = $state(new Promise((resolve, reject) => resolve(new Response())))
    let modelInsight: ModelInsight = $state({
        ids: {},
        costs: {},
        hours: {},
        kms: {},
        overshoot: 0,
        baseFee: 0
    });
</script>

{#snippet landing(next: () => void)}
    <Landing {next}></Landing>
{/snippet}
{#snippet cooperative(next: () => void)}
    <Cooperative {next}></Cooperative>
{/snippet}
{#snippet preferences(next: () => void)}
    <Preferences {next} bind:options={optionAmount} bind:result={optimizationResult}></Preferences>
{/snippet}
{#snippet proposals(next: () => void)}
    <Proposals {next} options={optionAmount} result={optimizationResult} bind:modelInsight></Proposals>
{/snippet}
{#snippet details(next: () => void)}
    <Details {next} insight={modelInsight}></Details>
{/snippet}


<Pseudopages pages={[{
    title: "Home",
    content: landing
}, {
    title: "Cooperative Info",
    content: cooperative
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