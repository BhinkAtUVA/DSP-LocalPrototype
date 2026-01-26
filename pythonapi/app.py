from flask import Flask, Response, request, jsonify
from optimizer_rovshan import optimize_pricing
from RideSimulator import RideSimulator
import pandas as pd
import numpy as np
import json

app = Flask(__name__)

coop_json = ""
with open("pythonapi/proto_coop.json") as f:
    coop_json = f.read()
generators = [RideSimulator.from_json(obj) for obj in json.loads(coop_json)]

def sim_month() -> pd.DataFrame:
    rides_month = pd.DataFrame(columns=["StartHour", "hours", "km", "weekday_flag", "weekend_flag", "ID_hh"])
    for i, gen in enumerate(generators):
        rides_hh = gen.simulate_month(22, 8)
        rides_hh["ID_hh"] = i
        rides_month = pd.concat((rides_month, rides_hh))
    rides_month["Cooperative"] = "Proto"
    rides_month["Month"] = "2026-01"
    rides_month = rides_month.set_index(np.arange(rides_month.shape[0]))
    return rides_month

rides = sim_month()

weights = {"heavy": 1.0, "proportionality": 1.0, "overall": 0.2}

bounds = {
    "hour_rate": (1.5, 6.0),
    "km_rate": (0.10, 0.60),
    "heavy_threshold_hours": (0.0, 40.0),
    "heavy_discount_pct": (0.0, 0.40),
}

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("X-Content-Type-Options", "*")
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

@app.get("/month")
def optimize_month():
    weights["heavy"] = 0 if "heavy" not in request.args else float(request.args["heavy"])
    weights["proportionality"] = 0 if "proportionality" not in request.args else float(request.args["proportionality"])
    weights["overall"] = 0.2 if "overall" not in request.args else float(request.args["overall"])
    summary, costs, gaps = optimize_pricing(rides, weights, bounds)
    summary["success"] = bool(summary["success"])
    gap_list = []
    for key in gaps:
        gap_list.append({ "Cooperative": key[0], "Month": key[1], "Profit": gaps[key] })
    print(gap_list)
    response = jsonify({ "summary": summary, "costs": costs.to_dict(), "gaps": gap_list })
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, 200