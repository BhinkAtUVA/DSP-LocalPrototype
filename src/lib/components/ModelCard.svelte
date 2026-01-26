<script lang="ts">
  import { Button } from "./ui/button";

    let { hourprice, kmprice, baseprice, discounts, characteristics, onclick }: {
        hourprice: number,
        kmprice: number,
        baseprice: number,
        discounts: {
            description: string,
            amount: number
        }[],
        characteristics: {
            label: string,
            score: number
        }[],
        onclick: () => void
    } = $props()
</script>

<div class="bg-stone-200 px-6 py-8 rounded-2xl">
    <h3 class="font-bold text-sm uppercase">Price</h3>
    <p><span class="3xl">{hourprice.toFixed(2)} €</span> per hour</p>
    <p><span class="3xl">{kmprice.toFixed(2)} €</span> per kilometer</p>
    <p><span class="3xl">{baseprice.toFixed(2)} €</span> membership fee</p>
    <h3 class="mt-4 font-bold text-sm uppercase">Discounts</h3>
    <div class="grid grid-cols-[2fr_1fr] gap-x-4 gap-y-2">
        {#each discounts as d}
            <p>{d.description}</p>
            <p>{d.amount} %</p>
        {/each}
    </div>
    <h3 class="mt-4 font-bold text-sm uppercase">Characteristics</h3>
    <div class="grid grid-cols-[2fr_1fr] gap-x-4 gap-y-2">
        {#each characteristics as c}
            <p>{c.label}</p>
            <div class="flex gap-2 items-center">
                {#each { length: 5 }, i}
                    {#if i < c.score}
                        <div class="rounded-full bg-black w-2 h-2"></div>
                    {:else}
                        <div class="rounded-full border-2 border-black w-2 h-2"></div>
                    {/if}
                {/each}
            </div>
        {/each}
    </div>
    <Button class="mt-4 w-full" {onclick}>Details</Button>
</div>