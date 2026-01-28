<script lang="ts">
    import Button from '../ui/button/button.svelte';
    import Checkbox from '../ui/checkbox/checkbox.svelte';
    import Input from '../ui/input/input.svelte';
    import { Label } from '../ui/label';
    import * as Select from '../ui/select';

    let { next }: {next: () => void} = $props()

    let answer1 = $state<string | undefined>(undefined)
    let triggerContent1 = $derived(answer1 ? (answer1.charAt(0).toUpperCase() + answer1.slice(1)) : "Select an option")
    let answer21 = $state<string | undefined>(undefined)
    let triggerContent21 = $derived(answer21 ? (answer21.charAt(0).toUpperCase() + answer21.slice(1)) : "Select an option")
    let answer311 = $state<string | undefined>(undefined)
    let triggerContent311 = $derived(answer311 ? (answer311.charAt(0).toUpperCase() + answer311.slice(1)) : "Select an option")
    let answer312 = $state<string | undefined>(undefined)
    let triggerContent312 = $derived(answer312 ? (answer312.charAt(0).toUpperCase() + answer312.slice(1)) : "Select an option")
    let answer22 = $state<string | undefined>(undefined)
    let triggerContent22 = $derived(answer22 ? (answer22.charAt(0).toUpperCase() + answer22.slice(1)) : "Select an option")
    let answer32 = $state<string | undefined>(undefined)
    let triggerContent32 = $derived(answer32 ? (answer32.charAt(0).toUpperCase() + answer32.slice(1)) : "Select an option")

    let finished = $derived(answer311 || answer312 || (answer22 && answer32))
</script>

<div class="container max-w-300 mx-auto px-4">
    <div class="grid grid-cols-1 md:grid-cols-[auto_1fr] gap-y-2 gap-x-6">
        <p>Do you plan on using the cars on weekends more often for longer trips or short errands?</p>
        <Select.Root type="single" bind:value={answer1}>
            <Select.Trigger class="w-130">{triggerContent1}</Select.Trigger>
            <Select.Content>
                <Select.Item value={"trips"} label={"Trips"}>{"Trips"}</Select.Item>
                <Select.Item value={"errands"} label={"Errands"}>{"Errands"}</Select.Item>
            </Select.Content>
        </Select.Root>
        {#if answer1 == "errands"}
            <p>Do you plan on using the cars on weekends more often in the morning or in the afternoon?</p>
            <Select.Root type="single" bind:value={answer21}>
                <Select.Trigger class="w-130">{triggerContent21}</Select.Trigger>
                <Select.Content>
                    <Select.Item value={"morning"} label={"Morning"}>{"Morning"}</Select.Item>
                    <Select.Item value={"afternoon"} label={"Afternoon"}>{"Afternoon"}</Select.Item>
                </Select.Content>
            </Select.Root>
            {#if answer21 == "morning"}
                <p>Do you plan to regularly drive more than 120km with one roundtrip?</p>
                <Select.Root type="single" bind:value={answer311}>
                    <Select.Trigger class="w-130">{triggerContent311}</Select.Trigger>
                    <Select.Content>
                        <Select.Item value={"yes"} label={"Yes"}>{"Yes"}</Select.Item>
                        <Select.Item value={"no"} label={"No"}>{"No"}</Select.Item>
                    </Select.Content>
                </Select.Root>
            {:else if answer21 == "afternoon"}
                <p>Do you plan to drive mostly in the afternoon on weekdays?</p>
                <Select.Root type="single" bind:value={answer312}>
                    <Select.Trigger class="w-130">{triggerContent312}</Select.Trigger>
                    <Select.Content>
                        <Select.Item value={"yes"} label={"Yes"}>{"Yes"}</Select.Item>
                        <Select.Item value={"no"} label={"No"}>{"No"}</Select.Item>
                    </Select.Content>
                </Select.Root>
            {/if}
        {:else if answer1 == "trips"}
            <p>Do you plan on doing many trips shorter than 10km on weekdays?</p>
            <Select.Root type="single" bind:value={answer22}>
                <Select.Trigger class="w-130">{triggerContent22}</Select.Trigger>
                <Select.Content>
                    <Select.Item value={"yes"} label={"Yes"}>{"Yes"}</Select.Item>
                    <Select.Item value={"no"} label={"No"}>{"No"}</Select.Item>
                </Select.Content>
            </Select.Root>
            <p>Do you plan to use cars on weekdays regularly?</p>
            <Select.Root type="single" bind:value={answer32}>
                <Select.Trigger class="w-130">{triggerContent32}</Select.Trigger>
                <Select.Content>
                    <Select.Item value={"yes"} label={"Yes"}>{"Yes"}</Select.Item>
                    <Select.Item value={"no"} label={"No"}>{"No"}</Select.Item>
                </Select.Content>
            </Select.Root>
        {/if}
    </div>
    {#if finished}
        ✓ Thank you for your participation.
    {/if}
    <Button class="mx-auto flex mt-4" onclick={next} disabled={!finished}>Next</Button>
</div>