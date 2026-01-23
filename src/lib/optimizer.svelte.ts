let loading = $state(false)

export function optimize() {
    loading = true
    setTimeout(() => loading = false, 5000)
}

export const optimizationInfo = {
    get loading() { return loading},
}