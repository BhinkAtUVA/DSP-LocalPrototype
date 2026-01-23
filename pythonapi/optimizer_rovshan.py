import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple
from scipy.optimize import minimize

RIDES_PATH = "rides_filtered.csv"
LEASE_PER_CAR_PER_MONTH = 660.0 
FIXED_MONTHLY_FEE = 25.0           

COOP_LEASED_CARS = {
    "Bloemenbuurt DEELt": 1,
    "Spaarndammerbuurt DEELt": 1,
    "FlexDeel": 1,
    "Bezuidenhout": 3,
}

DEFAULT_LEASED_CARS = 1  # fallback if a coop is missing in the dic

# 1) Load + preprocessing

def load_rides(path: str = RIDES_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)

    # keep only finished rides
    if "Status" in df.columns:
        df = df[df["Status"].isin(["FINISHED", "Finished", "finished"])].copy()

    for col in ["Reserved hours", "Kilometers", "Duration"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["ID_hh", "Cooperative", "Month"])

    # Parse timestamps 
    df["Start timestamp"] = pd.to_datetime(
        df["Start timestamp"],
        format="%d-%m-%y %H:%M",
        errors="coerce"
    )

    # Monday = 0, Sunday = 6
    df["weekday_flag"] = (df["Start timestamp"].dt.weekday < 5).astype(int)
    df["weekend_flag"] = (df["Start timestamp"].dt.weekday >= 5).astype(int)

    if "Duration" in df.columns and df["Duration"].notna().any():
        df["hours"] = df["Duration"].fillna(df.get("Reserved hours"))
    else:
        df["hours"] = df["Reserved hours"]

    df["km"] = df["Kilometers"].fillna(0.0)

    return df[
        [
            "Month",
            "Cooperative",
            "ID_hh",
            "hours",
            "km",
            "weekday_flag",
            "weekend_flag",
        ]
    ].copy()


# 2) Pricing model (simple v1)

@dataclass
class PricingParamsV1:
    hour_rate: float
    km_rate: float
    heavy_threshold_hours: float
    heavy_discount_pct: float  # 0..0.5 % discount 
    
def household_monthly_usage(rides):
    g = rides.groupby(["Cooperative", "Month", "ID_hh"], as_index=False).agg(
        hours=("hours", "sum"),
        km=("km", "sum"),
        weekday_hours=("hours", lambda x: x[rides.loc[x.index, "weekday_flag"] == 1].sum()),
        weekend_hours=("hours", lambda x: x[rides.loc[x.index, "weekend_flag"] == 1].sum()),
    )
    return g

def compute_costs_v1(usage: pd.DataFrame, p: PricingParamsV1) -> pd.DataFrame:
    """
    Total household-month cost:
      FIXED_MONTHLY_FEE
    + hour_rate*hours + km_rate*km
    - heavy-user discount on hour charges above heavy_threshold_hours
    """
    hours = usage["hours"].values
    km = usage["km"].values

    base_hour_cost = p.hour_rate * hours
    base_km_cost = p.km_rate * km

    above = np.clip(hours - p.heavy_threshold_hours, 0, None)
    discount = p.heavy_discount_pct * p.hour_rate * above

    out = usage.copy()
    out["cost"] = FIXED_MONTHLY_FEE + base_hour_cost + base_km_cost - discount
    return out


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


# 4) Lease constraints per coop-month 

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
    seed_params: PricingParamsV1 = PricingParamsV1(3.0, 0.30, 10.0, 0.10), 
):
    usage = household_monthly_usage(rides)

    x0 = np.array([seed_params.hour_rate, seed_params.km_rate,
                   seed_params.heavy_threshold_hours, seed_params.heavy_discount_pct], dtype=float)

    bnds = [
        bounds["hour_rate"],
        bounds["km_rate"],
        bounds["heavy_threshold_hours"],
        bounds["heavy_discount_pct"],
    ]

    def pack(x) -> PricingParamsV1:
        return PricingParamsV1(float(x[0]), float(x[1]), float(x[2]), float(x[3]))

    coop_months = list(usage[["Cooperative", "Month"]].drop_duplicates().itertuples(index=False, name=None))

    def objective(x):
        p = pack(x)
        costs = compute_costs_v1(usage, p)
        obj_heavy = objective_heavy_user_affordability(costs)
        obj_prop = objective_proportionality(costs)
        overall = float(np.mean(effective_price(costs)))
        return (
            weights.get("heavy", 1.0) * obj_heavy +
            weights.get("proportionality", 1.0) * obj_prop +
            weights.get("overall", 0.0) * overall
        )

    # Constraint: revenue - lease >= 0 Might have to change to revenue == lease ?
    cons = []
    for coop, month in coop_months:
        cons.append({
            "type": "ineq",
            "fun": (lambda x, coop=coop, month=month:
                    revenue_minus_lease_for_cm(compute_costs_v1(usage, pack(x)), coop, month))
        })

    res = minimize(objective, x0, method="SLSQP", bounds=bnds, constraints=cons, options={"maxiter": 1000})

    best = pack(res.x)
    best_costs = compute_costs_v1(usage, best)

    gaps = {(coop, month): revenue_minus_lease_for_cm(best_costs, coop, month) for coop, month in coop_months}
    worst_gap = min(gaps.values()) if gaps else float("nan")
    frac_ok = float(np.mean([g >= -1e-6 for g in gaps.values()])) if gaps else float("nan")

    summary = {
        "success": res.success,
        "message": res.message,
        "params": best,
        "objective_value": float(res.fun),
        "lease_per_car_per_month": LEASE_PER_CAR_PER_MONTH,
        "default_leased_cars": DEFAULT_LEASED_CARS,
        "num_coops_in_car_map": len(COOP_LEASED_CARS),
        "fixed_monthly_fee_per_household": FIXED_MONTHLY_FEE,
        "num_coop_months": len(gaps),
        "worst_revenue_minus_lease": float(worst_gap),
        "fraction_coop_months_meeting_lease": float(frac_ok),
        "heavy_obj": objective_heavy_user_affordability(best_costs),
        "proportionality_obj": objective_proportionality(best_costs),
        "overall_effective_price_mean": float(np.mean(effective_price(best_costs))),
    }
    return summary, best_costs, gaps


# 6) Feasibility Check

def feasibility_check():
    
    rides = load_rides()
    usage = household_monthly_usage(rides)

    p_max = PricingParamsV1(hour_rate=6.0, km_rate=0.6, heavy_threshold_hours=0.0, heavy_discount_pct=0.0)
    costs_max = compute_costs_v1(usage, p_max)

    rev_by_cm = costs_max.groupby(["Cooperative", "Month"])["cost"].sum().reset_index()
    rev_by_cm["lease_required"] = rev_by_cm["Cooperative"].apply(required_lease_for_coop)
    rev_by_cm["gap"] = rev_by_cm["cost"] - rev_by_cm["lease_required"]


    print("Fraction feasible at max prices:", (rev_by_cm["gap"] >= 0).mean())
    print("Worst gap at max prices:", rev_by_cm["gap"].min())

    print("\n10 worst coop-months at max prices:")
    print(rev_by_cm.sort_values("gap").head(10))


# 7) Run

if __name__ == "__main__":

    # feasibility_check()

    rides = load_rides()

    weights = {"heavy": 1.0, "proportionality": 1.0, "overall": 0.2}

    bounds = {
        "hour_rate": (1.5, 6.0),
        "km_rate": (0.10, 0.60),
        "heavy_threshold_hours": (0.0, 40.0),
        "heavy_discount_pct": (0.0, 0.40),
    }

    summary, costs, gaps = optimize_pricing(rides, weights, bounds)

    print(summary)

    worst = sorted(gaps.items(), key=lambda kv: kv[1])[:10]
    print("\nWorst coop-month revenue gaps (revenue - lease):")
    for (coop, month), gap in worst:
        print(f"{coop} | {month} | gap={gap:.2f}")
