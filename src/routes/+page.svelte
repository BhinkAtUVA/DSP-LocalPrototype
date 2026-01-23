<script lang="ts">
    import Pseudopages from "$lib/components/layout/Pseudopages.svelte";
    import Cooperative from "$lib/components/pseudopages/Cooperative.svelte";
    import Details from "$lib/components/pseudopages/Details.svelte";
    import Landing from "$lib/components/pseudopages/Landing.svelte";
    import Preferences from "$lib/components/pseudopages/Preferences.svelte";
    import Proposals from "$lib/components/pseudopages/Proposals.svelte";

    let optionAmount: number = $state(3)

</script>

{#snippet landing(next: () => void)}
    <Landing {next}></Landing>
{/snippet}
{#snippet cooperative(next: () => void)}
    <Cooperative {next}></Cooperative>
{/snippet}
{#snippet preferences(next: () => void)}
    <Preferences {next} bind:options={optionAmount}></Preferences>
{/snippet}
{#snippet proposals(next: () => void)}
    <Proposals {next} options={optionAmount}></Proposals>
{/snippet}
{#snippet details(next: () => void)}
    <Details {next}></Details>
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