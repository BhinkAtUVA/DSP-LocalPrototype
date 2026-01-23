<script lang="ts">
    import ChevronLeft from "@lucide/svelte/icons/chevron-left";
    import House from "@lucide/svelte/icons/house";
    import type { Component, ComponentProps, Snippet } from "svelte";
    import { Button } from "../ui/button";

    let { pages }: { pages: { title: string, content: Snippet<[() => void]> }[] } = $props()
    let currentPageIndex = $state(0)
    let currentPage = $derived(pages[currentPageIndex])

    function next() {
        if (currentPageIndex >= pages.length - 1) return
        currentPageIndex++
    }
    function previous() {
        if (currentPageIndex == 0) return
        currentPageIndex--
    }
    function home() {
        if (currentPageIndex == 0) return
        currentPageIndex = 0
    }
</script>

{#if pages.length > 0}
    <nav class="bg-stone-200 h-20 mb-6">
        <div class="h-full nav-container grid grid-cols-[1fr_auto_1fr] items-center gap-4 justify-between mx-auto px-4 max-w-300">
            <div>
                <Button variant="secondary" disabled={currentPageIndex == 0} onclick={previous}><ChevronLeft /> Back</Button>
            </div>
            <h1 class="w-full text-center text-4xl">{ currentPage.title }</h1>
            <div class="flex justify-end">
                <Button variant="secondary" onclick={home}><House /></Button>
            </div>
        </div>
    </nav>
    {@render currentPage.content(next)}
{/if}