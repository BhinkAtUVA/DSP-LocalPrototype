import { get } from "svelte/store"

let currentOptimizationResult = $state<any>({})
let hasResult = $state(false)

export function clearResult() {
    currentOptimizationResult = {}
    hasResult = false
}
export async function optimize(objective: "heavy" | "proportional") {
    console.log(`Objective: ${objective}`)
    let result = await fetch("http://127.0.0.1:7999/methods/all?" + new URLSearchParams({
        heavy: objective == "heavy" ? "1" : "0",
        proportionality: objective == "proportional" ? "1": "0",
        overall: "0.2"
    }).toString())
    currentOptimizationResult = await result.json()
    console.log(currentOptimizationResult)
    hasResult = true
}

export let optimizationInfo = {
    get hasResult() { return hasResult },
    get currentResult() { return currentOptimizationResult }
}

export type ModelInsight = {
    ids: Record<number, number>,
    costsMean: Record<number, number>,
    hoursMean: Record<number, number>,
    kmsMean: Record<number, number>,
    costsCIHalf: Record<number, number>,
    hoursCIHalf: Record<number, number>,
    kmsCIHalf: Record<number, number>,
    overshoots: Record<number, number>,
    baseFee: number
}