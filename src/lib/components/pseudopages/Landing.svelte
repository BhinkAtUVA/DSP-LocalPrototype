<script lang="ts">
    import Button from '../ui/button/button.svelte';

    let { next }: { next: () => void } = $props()
</script>

<div class="container max-w-300 mx-auto px-4 flex flex-col items-center">
    <h1 class="text-4xl text-center mb-4">WijZijnDEEL Pricing Optimizer</h1>
    <p class="text-center max-w-80 mb-4">This tool can be used to improve the pricing structure in your cooperative. Press Start to begin!</p>
    <Button onclick={next}>Start</Button>
</div>