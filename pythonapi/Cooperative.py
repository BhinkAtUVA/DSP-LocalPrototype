import json
from pathlib import Path
import numpy as np
import pandas as pd

from RideSimulator import RideSimulator

class Cooperative:
    amounts = None
    distribution_info = None

    def __init__(self, cluster_amounts: list[int] = [3, 3, 12]):
        self.amounts = cluster_amounts
        with open(Path("pythonapi") / "cluster_distributions.json") as f:
            self.distribution_info = json.loads(f.read())

    def simulate(self, num_months: int = 1) -> pd.DataFrame:
        rides = pd.DataFrame(columns = ["Month", "Cooperative", "ID_hh", "start_hour", "hours", "km", "is_weekend_ride", "is_offpeak_ride"])
        generators: list[RideSimulator] = []
        for dists in self.distribution_info:
            generators.append(RideSimulator(
                start_time_params = dists["start_time_params"],
                duration_mu = dists["duration_mu"],
                duration_sigma = dists["duration_sigma"],
                distance_mu = dists["distance_mu"],
                distance_sigma = dists["distance_sigma"],
                r_duration_distance = dists["r_duration_distance"],
                rides_wd_beta = dists["rides_wd_beta"],
                rides_we_beta = dists["rides_we_beta"],
            ))
        for i in range(num_months):
            month_rides = pd.DataFrame(columns = ["start_hour", "hours", "km", "is_weekend_ride", "ID_hh"])
            k = 0
            for j, gen in enumerate(generators):
                for _ in range(self.amounts[j]):
                    generated = gen.simulate_month(22, 8)
                    generated["ID_hh"] = k
                    month_rides = pd.concat([month_rides, generated])
                    k += 1
            month_rides["Month"] = i
            month_rides["Cooperative"] = "Simulated"
            month_rides["is_offpeak_ride"] = np.logical_or(np.logical_and(month_rides["start_hour"] >= 9, month_rides["start_hour"] <= 16), month_rides["start_hour"] >= 18.5)
            rides = pd.concat([rides, month_rides])
        rides.set_index(np.arange(rides.shape[0]))
        return rides

if __name__ == "__main__":
    small = Cooperative().simulate(6)
    big = Cooperative([10, 10, 10]).simulate(10)
    print(small["ID_hh"].unique())
    print(big["ID_hh"].unique())
    