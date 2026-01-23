import pandas as pd
import numpy as np
import warnings

MultinomialGaussianParams = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]

class RideSimulator:
    start_time_params: MultinomialGaussianParams
    start_time_cdf: list[float]
    duration_lambda: float
    distance_lambda: float
    r_duration_distance: float
    rides_per_weekday: float
    rides_per_weekend_day: float
    generator: np.random.Generator

    def __init__(self, start_time_params: MultinomialGaussianParams, duration_lambda: float, distance_lambda: float, r_duration_distance: float, rides_per_weekday: float, rides_per_weekend_day: float):
        self.start_time_params = start_time_params
        self.start_time_cdf = self.__build_trinomial_gaussian_cdf(start_time_params)
        self.duration_lambda = duration_lambda
        self.distance_lambda = distance_lambda
        self.r_duration_distance = r_duration_distance
        self.rides_per_weekday = rides_per_weekday
        self.rides_per_weekend_day = rides_per_weekend_day
        self.generator = np.random.Generator(np.random.PCG64(42))

    def to_json(self) -> dict:
        return {
            "start_time": self.start_time_params,
            "duration_lambda": self.duration_lambda,
            "distance_lambda": self.distance_lambda,
            "r_duration_distance": self.r_duration_distance,
            "rides_per_weekday": self.rides_per_weekday,
            "rides_per_weekend_day": self.rides_per_weekend_day
        }
    
    @classmethod
    def from_json(cls, json_obj: dict):
        return cls(json_obj["start_time"], json_obj["duration_lambda"], json_obj["distance_lambda"], json_obj["r_duration_distance"], json_obj["rides_per_weekday"], json_obj["rides_per_weekend_day"])

    def set_seed(self, random_state: int):
        self.generator = np.random.Generator(np.random.PCG64(random_state))

    def __build_trinomial_gaussian_cdf(self, params: MultinomialGaussianParams) -> list[float]:
        gaussian_pdf = lambda x: np.sum([params[i][0] / (np.sqrt(2 * np.pi * params[i][2] ** 2)) * np.exp(-((x - params[i][1]) ** 2)/(2 * params[i][2] ** 2)) for i in range(3)])
        xs = np.linspace(3, 27, 1000)
        numeric_cdf: list[float] = []
        current = 0
        cx = 0
        for x in xs:
            dx = x - cx
            if dx == 0:
                numeric_cdf.append(current)
                continue
            density = gaussian_pdf(x)
            current += dx * density
            if(current > 1):
                warnings.warn("Numeric sampling of multinomial gaussian exceeded probability of 1")
                current = 1
            numeric_cdf.append(current)
        return numeric_cdf
    
    def __reverse_trinomial_cdf(self, u: float) -> float:
        cidx = 500
        cstep = 250
        cdir = None
        while cstep > 0:
            pivot = self.start_time_cdf[cidx]
            if pivot > u:
                nextdir = -1
            else:
                nextdir = 1
            dirchange = cdir == None or cdir != nextdir
            cidx += nextdir * cstep
            if cidx < 0:
                cidx = 0
                break
            if cidx > 999:
                cidx = 999
                break
            if dirchange: cstep //= 2
            cdir = nextdir
        frac = cidx / 1000 * 24 + 3
        return frac % 24

    def __reverse_exponential_cdf(self, lambd: float, u: float) -> float:
        return -np.log(1 - u) / lambd

    def simulate_month(self, weekdays: int, weekend_days: int) -> pd.DataFrame:
        weekrides = int(np.round(weekdays * self.rides_per_weekday))
        weekendrides = int(np.round(weekend_days * self.rides_per_weekend_day))
        ridelist = pd.DataFrame(index=np.arange(weekrides + weekendrides), columns=["StartHour", "hours", "km", "weekday_flag", "weekend_flag"])
        for i in range(weekrides):
            sh = self.__reverse_trinomial_cdf(self.generator.uniform())
            u_duration = self.generator.uniform()
            u_distance = u_duration * self.r_duration_distance + self.generator.uniform() * (1 - self.r_duration_distance)
            dur = self.__reverse_exponential_cdf(self.duration_lambda, u_duration)
            dis = self.__reverse_exponential_cdf(self.distance_lambda, u_distance)
            ridelist.loc[i] = [sh, dur, dis, 1, 0]
        for i in range(weekendrides):
            sh = self.__reverse_trinomial_cdf(self.generator.uniform())
            u_duration = self.generator.uniform()
            u_distance = u_duration * self.r_duration_distance + self.generator.uniform() * (1 - self.r_duration_distance)
            dur = self.__reverse_exponential_cdf(self.duration_lambda, u_duration)
            dis = self.__reverse_exponential_cdf(self.distance_lambda, u_distance)
            ridelist.loc[weekrides + i] = [sh, dur, dis, 0, 1]
        return ridelist