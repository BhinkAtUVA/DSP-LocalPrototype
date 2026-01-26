<script lang="ts">
    import WandSparkles from '@lucide/svelte/icons/wand-sparkles';
    import Button from '../ui/button/button.svelte';
    import Input from '../ui/input/input.svelte';
    import * as Select from '../ui/select';
    import { clearResult, optimize } from '$lib/optimizer.svelte';

    let { next, options = $bindable(), result = $bindable() }: { next: () => void, options: number, result: Promise<Response> } = $props()

    const objectiveOptions = [{
        value: "heavy",
        label: "Low costs for members using cars often"
    }, {
        value: "proportional",
        label: "Costs proportional to car usage"
    }]
    let objectiveValue: "heavy" | "proportional" = $state("proportional")
    let triggerContent = $derived(objectiveOptions.find(o => o.value == objectiveValue)?.label ?? "Select an objective")
</script>

<div class="container max-w-300 mx-auto px-4">
    <div class="grid grid-cols-1 md:grid-cols-[auto_1fr] gap-y-2 gap-x-6">
        <!-- <p>How many pricing model options would you like to generate?</p>
        <Input type="number" bind:value={options}></Input>
        <p>How many discounts should the options have at max?</p>
        <Input type="number"></Input> -->
        <p>What should your new pricing model achieve for the members?</p>
        <Select.Root type="single" bind:value={objectiveValue}>
            <Select.Trigger class="w-130">{triggerContent}</Select.Trigger>
            <Select.Content>
                {#each objectiveOptions as option (option.value)}
                    <Select.Item value={option.value} label={option.label}>
                        {option.label}
                    </Select.Item>
                {/each}
            </Select.Content>
        </Select.Root>
    </div>
    <Button class="mx-auto flex mt-4" onclick={() => {
        clearResult()
        optimize(objectiveValue)
        next()
    }}><WandSparkles></WandSparkles> Generate</Button>
</div>