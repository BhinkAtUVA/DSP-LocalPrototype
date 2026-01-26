import { get } from "svelte/store"

let currentOptimizationResult = $state<any>({})
let hasResult = $state(false)

export function clearResult() {
    currentOptimizationResult = {}
    hasResult = false
}
export async function optimize(objective: "heavy" | "proportional") {
    console.log(`Objective: ${objective}`)
    let result = await fetch("http://127.0.0.1:7999/month?" + new URLSearchParams({
        heavy: objective == "heavy" ? "1" : "0",
        proportionality: objective == "proportional" ? "1": "0",
        overall: "5"
    }).toString())
    currentOptimizationResult = await result.json()
    hasResult = true
}

export let optimizationInfo = {
    get hasResult() { return hasResult },
    get currentResult() { return currentOptimizationResult }
}

export type ModelInsight = {
    ids: Record<number, number>,
    costs: Record<number, number>,
    hours: Record<number, number>,
    kms: Record<number, number>,
    overshoot: number,
    baseFee: number
}