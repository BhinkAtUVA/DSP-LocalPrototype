from flask import Flask, Response, request, jsonify
from optimizer_rovshan import optimize_pricing
from RideSimulator import RideSimulator
import pandas as pd
import numpy as np
import json
from Cooperative import Cooperative

app = Flask(__name__)

coop_json = ""
with open("pythonapi/proto_coop.json") as f:
    coop_json = f.read()

rides = Cooperative().simulate(10)

weights = {"heavy": 1.0, "proportionality": 1.0, "overall": 0.2}

bounds = {
    "hour_rate": (1.5, 10.0),
    "km_rate": (0.10, 1.00),
    "heavy_threshold_hours": (0.0, 40.0),
    "heavy_discount_pct": (0.0, 0.40),
    "offpeak_discount_pct": (0.0, 0.40),
    "weekend_discount_pct": (0.0, 0.40),
}

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("X-Content-Type-Options", "*")
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

@app.get("/methods/all")
def optimize_all():
    weights["heavy"] = 0 if "heavy" not in request.args else float(request.args["heavy"])
    weights["proportionality"] = 0 if "proportionality" not in request.args else float(request.args["proportionality"])
    weights["overall"] = 0.2 if "overall" not in request.args else float(request.args["overall"])
    result = []
    for variant in ["BASE", "BASE", "HEAVY", "WEEKEND", "OFFPEAK", "HEAVY_WEEKEND", "HEAVY_OFFPEAK", "WEEKEND_OFFPEAK"]:
        summary, costs, gaps = optimize_pricing(rides, weights, bounds, variant)
        summary["success"] = bool(summary["success"])
        gap_list = []
        for key in gaps:
            gap_list.append({ "Cooperative": key[0], "Month": key[1], "Profit": gaps[key] })
        costs_mean = costs[["ID_hh", "hours", "km", "cost"]].groupby("ID_hh").mean()
        costs_cihalf = costs[["ID_hh", "hours", "km", "cost"]].groupby("ID_hh").std() / np.sqrt(10) * 1.96
        result.append({ "summary": summary, "costsMean": costs_mean.to_dict(), "costsCIHalf": costs_cihalf.to_dict(), "gaps": gap_list })
    response = jsonify(result)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, 200

@app.get("/methods/single")
def optimize_single():
    weights["heavy"] = 0 if "heavy" not in request.args else float(request.args["heavy"])
    weights["proportionality"] = 0 if "proportionality" not in request.args else float(request.args["proportionality"])
    weights["overall"] = 0.2 if "overall" not in request.args else float(request.args["overall"])
    variant = "BASE" if "variant" not in request.args else request.args["variant"]
    summary, costs, gaps = optimize_pricing(rides, weights, bounds, variant)
    summary["success"] = bool(summary["success"])
    gap_list = []
    for key in gaps:
        gap_list.append({ "Cooperative": key[0], "Month": key[1], "Profit": gaps[key] })
    costs_mean = costs[["Month", "hours", "km", "cost"]].groupby("Month").mean()
    costs_cihalf = costs[["Month", "hours", "km", "cost"]].groupby("Month").std() / np.sqrt(10) * 1.96
    response = jsonify({ "summary": summary, "costsMean": costs_mean.to_dict(), "costsCIHalf": costs_cihalf.to_dict(), "gaps": gap_list })
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, 200