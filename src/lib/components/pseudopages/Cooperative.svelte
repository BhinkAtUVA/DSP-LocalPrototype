<script lang="ts">
    import Button from '../ui/button/button.svelte';
  import Checkbox from '../ui/checkbox/checkbox.svelte';
    import Input from '../ui/input/input.svelte';
  import { Label } from '../ui/label';

    let { next }: {next: () => void} = $props()

    let consented: boolean = $state(false)
</script>

<div class="container max-w-300 mx-auto px-4">
    <div class="grid grid-cols-1 md:grid-cols-[auto_1fr] gap-y-2 gap-x-6">
        <p>How many people in your cooperative drive a lot?</p>
        <Input type="number"></Input>
        <p>How many people in your cooperative drive a medium amount?</p>
        <Input type="number"></Input>
        <p>How many people in your cooperative drive rarely?</p>
        <Input type="number"></Input>
        <div class="flex gap-4">
            <Checkbox id="consent" bind:checked={consented}></Checkbox>
            <Label for="consent">I understand that the answers to the above questions will be used only during this session to derive options for a new pricing model</Label>
        </div>
    </div>
    <Button class="mx-auto flex mt-4" onclick={next} disabled={!consented}>Next</Button>
</div>