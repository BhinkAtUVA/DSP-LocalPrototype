import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple
from scipy.optimize import minimize
from Cooperative import Cooperative

LEASE_PER_CAR_PER_MONTH = 926.0
FIXED_MONTHLY_FEE = 25.0

COOP_LEASED_CARS = {
    "Simulated": 3,
}
DEFAULT_LEASED_CARS = 1

# Options:
# "BASE", "HEAVY", "WEEKEND", "OFFPEAK",
# "HEAVY_WEEKEND", "HEAVY_OFFPEAK", "WEEKEND_OFFPEAK"
MODEL_VARIANT = "BASE"


# 1) Load rides (real OR simulated)

SIM_COOPERATIVE_NAME = "Simulated"
SIM_NUM_MONTHS = 10

def load_rides() -> pd.DataFrame:
    rides = Cooperative().simulate(SIM_NUM_MONTHS)

    required = {
        "Month", "Cooperative", "ID_hh",
        "hours", "km", "is_weekend_ride", "is_offpeak_ride"
    }
    
    missing = required - set(rides.columns)
    if missing:
        raise ValueError(f"Simulated rides missing columns: {missing}")

    rides = rides.copy()

    # Convert month index to readable labels
    rides["Month"] = rides["Month"].apply(lambda m: f"sim-{int(m):02d}")

    # 0/1 
    rides["is_weekend_ride"] = rides["is_weekend_ride"].astype(int)
    rides["is_offpeak_ride"] = rides["is_offpeak_ride"].astype(int)

    # Force cooperative name to match lease map
    rides["Cooperative"] = SIM_COOPERATIVE_NAME

    return rides[
        [
            "Month",
            "Cooperative",
            "ID_hh",
            "hours",
            "km",
            "is_weekend_ride",
            "is_offpeak_ride",
        ]
    ].copy()


# 2) Pricing model

@dataclass
class PricingParamsV1:
    hour_rate: float
    km_rate: float
    heavy_threshold_hours: float
    heavy_discount_pct: float
    offpeak_discount_pct: float
    weekend_discount_pct: float


def household_monthly_usage(rides: pd.DataFrame) -> pd.DataFrame:
    rides = rides.copy()

    rides["hours_weekend"] = rides["hours"] * rides["is_weekend_ride"]
    rides["hours_offpeak"] = rides["hours"] * rides["is_offpeak_ride"]

    rides["hours_regular"] = rides["hours"] - rides["hours_weekend"] - rides["hours_offpeak"]
    rides["hours_regular"] = rides["hours_regular"].clip(lower=0.0)

    g = rides.groupby(["Cooperative", "Month", "ID_hh"], as_index=False).agg(
        hours=("hours", "sum"),
        km=("km", "sum"),
        rides=("hours", "count"),
        hours_regular=("hours_regular", "sum"),
        hours_offpeak=("hours_offpeak", "sum"),
        hours_weekend=("hours_weekend", "sum"),
    )
    return g


def compute_costs_v1(usage: pd.DataFrame, p: PricingParamsV1) -> pd.DataFrame:
    hours = usage["hours"].values
    km = usage["km"].values

    h_reg = usage["hours_regular"].values
    h_off = usage["hours_offpeak"].values
    h_wknd = usage["hours_weekend"].values

    hour_cost = (
        p.hour_rate * h_reg
        + p.hour_rate * (1 - p.offpeak_discount_pct) * h_off
        + p.hour_rate * (1 - p.weekend_discount_pct) * h_wknd
    )

    km_cost = p.km_rate * km

    avg_eff_hour_rate = np.where(hours > 1e-9, hour_cost / hours, 0.0)
    above = np.clip(hours - p.heavy_threshold_hours, 0, None)
    heavy_discount = p.heavy_discount_pct * avg_eff_hour_rate * above

    out = usage.copy()
    out["cost"] = FIXED_MONTHLY_FEE + hour_cost + km_cost - heavy_discount
    return out


def enabled_discounts(variant: str) -> Dict[str, bool]:
    variant = variant.upper()
    return {
        "heavy": variant in {"HEAVY", "HEAVY_WEEKEND", "HEAVY_OFFPEAK"},
        "weekend": variant in {"WEEKEND", "HEAVY_WEEKEND", "WEEKEND_OFFPEAK"},
        "offpeak": variant in {"OFFPEAK", "HEAVY_OFFPEAK", "WEEKEND_OFFPEAK"},
    }


# 3) Objectives

def effective_price(costs: pd.DataFrame, alpha_hour_to_km: float = 10.0) -> np.ndarray:
    denom = costs["km"].values + alpha_hour_to_km * costs["hours"].values
    denom = np.where(denom <= 1e-9, 1e-9, denom)
    return costs["cost"].values / denom


def objective_heavy_user_affordability(costs: pd.DataFrame, top_quantile: float = 0.2) -> float:
    usage_score = costs["km"].values + 10.0 * costs["hours"].values
    thr = np.quantile(usage_score, 1 - top_quantile)
    heavy = costs[usage_score >= thr]
    return float(np.mean(effective_price(heavy)))


def objective_proportionality(costs: pd.DataFrame) -> float:
    usage = costs["km"].values + 10.0 * costs["hours"].values
    usage_sum = usage.sum()
    cost_sum = costs["cost"].sum()
    if usage_sum <= 1e-9 or cost_sum <= 1e-9:
        return 0.0
    usage_share = usage / usage_sum
    cost_share = costs["cost"].values / cost_sum
    return float(np.mean((cost_share - usage_share) ** 2))


# 4) Lease constraint

def required_lease_for_coop(coop: str) -> float:
    n_cars = COOP_LEASED_CARS.get(coop, DEFAULT_LEASED_CARS)
    return float(n_cars * LEASE_PER_CAR_PER_MONTH)


def revenue_minus_lease_for_cm(costs: pd.DataFrame, coop: str, month: str) -> float:
    revenue = costs[(costs["Cooperative"] == coop) & (costs["Month"] == month)]["cost"].sum()
    lease_required = required_lease_for_coop(coop)
    return float(revenue - lease_required)


# 5) Optimizer

def optimize_pricing(
    rides: pd.DataFrame,
    weights: Dict[str, float],
    bounds: Dict[str, Tuple[float, float]],
    model_variant: str = MODEL_VARIANT,
    seed_params: PricingParamsV1 = PricingParamsV1(3.0, 0.30, 10.0, 0.10, 0.15, 0.10),
):
    usage = household_monthly_usage(rides)
    flags = enabled_discounts(model_variant)

    var_names = ["hour_rate", "km_rate"]
    if flags["heavy"]:
        var_names += ["heavy_threshold_hours", "heavy_discount_pct"]
    if flags["offpeak"]:
        var_names += ["offpeak_discount_pct"]
    if flags["weekend"]:
        var_names += ["weekend_discount_pct"]

    def get_seed(name: str) -> float:
        return float(getattr(seed_params, name))

    x0 = np.array([get_seed(n) for n in var_names], dtype=float)
    bnds = [bounds[n] for n in var_names]

    def pack_from_vars(x: np.ndarray) -> PricingParamsV1:
        p = PricingParamsV1(
            hour_rate=seed_params.hour_rate,
            km_rate=seed_params.km_rate,
            heavy_threshold_hours=seed_params.heavy_threshold_hours,
            heavy_discount_pct=seed_params.heavy_discount_pct,
            offpeak_discount_pct=seed_params.offpeak_discount_pct,
            weekend_discount_pct=seed_params.weekend_discount_pct,
        )

        for name, val in zip(var_names, x):
            setattr(p, name, float(val))

        if not flags["heavy"]:
            p.heavy_threshold_hours = 10.0
            p.heavy_discount_pct = 0.0
        if not flags["offpeak"]:
            p.offpeak_discount_pct = 0.0
        if not flags["weekend"]:
            p.weekend_discount_pct = 0.0

        return p

    coop_months = list(usage[["Cooperative", "Month"]].drop_duplicates().itertuples(index=False, name=None))

    def objective(x):
        p = pack_from_vars(x)
        costs = compute_costs_v1(usage, p)
        obj_heavy = objective_heavy_user_affordability(costs)
        obj_prop = objective_proportionality(costs)
        overall = float(np.mean(effective_price(costs)))
        return (
            weights.get("heavy", 1.0) * obj_heavy
            + weights.get("proportionality", 1.0) * obj_prop
            + weights.get("overall", 0.0) * overall
        )

    cons = []
    for coop, month in coop_months:
        cons.append({
            "type": "ineq",
            "fun": (lambda x, coop=coop, month=month:
                    revenue_minus_lease_for_cm(compute_costs_v1(usage, pack_from_vars(x)), coop, month))
        })

    res = minimize(objective, x0, method="SLSQP", bounds=bnds, constraints=cons, options={"maxiter": 1000})

    best = pack_from_vars(res.x)
    best_costs = compute_costs_v1(usage, best)

    gaps = {(coop, month): revenue_minus_lease_for_cm(best_costs, coop, month) for coop, month in coop_months}

    summary = {
        "success": res.success,
        "message": res.message,
        "model_variant": model_variant,
        "optimized_vars": var_names,
        "params": best,
        "objective_value": float(res.fun),
        "obj_heavy": objective_heavy_user_affordability(best_costs),
        "obj_proportionality": objective_proportionality(best_costs),
        "num_coop_months": len(gaps),
        "worst_revenue_minus_lease": float(min(gaps.values())) if gaps else float("nan"),
        "fraction_coop_months_meeting_lease": float(np.mean([g >= -1e-6 for g in gaps.values()])) if gaps else float("nan"),
    }
    return summary, best_costs, gaps


# 6) Run

if __name__ == "__main__":
    rides = load_rides()

    weights = {"heavy": 1.0, "proportionality": 1.0, "overall": 0.2}
    bounds = {
        "hour_rate": (1.5, 10.0),
        "km_rate": (0.10, 1.00),
        "heavy_threshold_hours": (0.0, 40.0),
        "heavy_discount_pct": (0.0, 0.40),
        "offpeak_discount_pct": (0.0, 0.40),
        "weekend_discount_pct": (0.0, 0.40),
    }

    summary, costs, gaps = optimize_pricing(rides, weights, bounds, model_variant=MODEL_VARIANT)

    print(summary)

    worst = sorted(gaps.items(), key=lambda kv: kv[1])[:10]
    print("\nWorst coop-month revenue gaps (revenue - lease):")
    for (coop, month), gap in worst:
        print(f"{coop} | {month} | gap={gap:.2f}")
