import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
from scipy.special import erfinv

MultinomialGaussianParams = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
BetaParams = tuple[float, float, float, float]

class RideSimulator:
    start_time_params: MultinomialGaussianParams
    start_time_cdf: list[float]
    duration_mu: float
    duration_sigma: float
    distance_mu: float    # <--- NEW
    distance_sigma: float # <--- NEW
    r_duration_distance: float
    rides_wd_beta: BetaParams
    rides_we_beta: BetaParams
    generator: np.random.Generator

    def __init__(self, 
                 start_time_params: MultinomialGaussianParams, 
                 duration_mu: float, 
                 duration_sigma: float, 
                 distance_mu: float,    # <--- NEW
                 distance_sigma: float, # <--- NEW
                 r_duration_distance: float, 
                 rides_wd_beta: BetaParams, 
                 rides_we_beta: BetaParams):
        
        self.start_time_cdf = self.__build_trinomial_gaussian_cdf(start_time_params)
        self.duration_mu = duration_mu
        self.duration_sigma = duration_sigma
        self.distance_mu = distance_mu       # <--- NEW
        self.distance_sigma = distance_sigma # <--- NEW
        self.r_duration_distance = r_duration_distance
        self.rides_wd_beta = rides_wd_beta
        self.rides_we_beta = rides_we_beta
        self.generator = np.random.Generator(np.random.PCG64(42))

    def set_seed(self, random_state: int):
        self.generator = np.random.Generator(np.random.PCG64(random_state))

    def __build_trinomial_gaussian_cdf(self, params: MultinomialGaussianParams) -> list[float]:
        gaussian_pdf = lambda x: np.sum([params[i][0] / (np.sqrt(2 * np.pi) * params[i][2]) * np.exp(-((x - params[i][1]) ** 2)/(2 * params[i][2] ** 2)) for i in range(3)])
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
            cx = x
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

    def __reverse_lognormal_cdf(self, mu: float, sigma: float, u: float) -> float:
        u = np.clip(u, 1e-9, 1 - 1e-9)
        return np.exp(mu + sigma * np.sqrt(2) * erfinv(2 * u - 1))

    def simulate_month(self, weekdays: int, weekend_days: int) -> pd.DataFrame:
        wd_alpha, wd_beta, wd_min, wd_max = self.rides_wd_beta
        we_alpha, we_beta, we_min, we_max = self.rides_we_beta

        rate_wd = self.generator.beta(wd_alpha, wd_beta) * (wd_max - wd_min) + wd_min
        rate_we = self.generator.beta(we_alpha, we_beta) * (we_max - we_min) + we_min

        weekrides = int(np.round(weekdays * rate_wd))
        weekendrides = int(np.round(weekend_days * rate_we))
        
        ridelist = pd.DataFrame(index=np.arange(weekrides + weekendrides), columns=["start_hour", "hours", "km", "is_weekend_ride"])
        
        for i in range(weekrides):
            sh = self.__reverse_trinomial_cdf(self.generator.uniform())
            u_duration = self.generator.uniform()
            u_distance = u_duration * self.r_duration_distance + self.generator.uniform() * (1 - self.r_duration_distance)
            
            dur = self.__reverse_lognormal_cdf(self.duration_mu, self.duration_sigma, u_duration)
            dis = self.__reverse_lognormal_cdf(self.distance_mu, self.distance_sigma, u_distance) # <--- CHANGED
            
            ridelist.loc[i] = [sh, dur, dis, 0]
            
        for i in range(weekendrides):
            sh = self.__reverse_trinomial_cdf(self.generator.uniform())
            u_duration = self.generator.uniform()
            u_distance = u_duration * self.r_duration_distance + self.generator.uniform() * (1 - self.r_duration_distance)
            
            dur = self.__reverse_lognormal_cdf(self.duration_mu, self.duration_sigma, u_duration)
            dis = self.__reverse_lognormal_cdf(self.distance_mu, self.distance_sigma, u_distance) # <--- CHANGED
            
            ridelist.loc[weekrides + i] = [sh, dur, dis, 1]
            
        return ridelist