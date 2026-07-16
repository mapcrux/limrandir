#!/usr/bin/env python3
"""Generate a Garmin Connect JSON report for scheduled task runs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Callable
from xmlrpc import client

from garminconnect import Garmin

DEFAULT_OUTPUT_TEMPLATE = (
    r"C:\Users\codet\OneDrive\Documents\Garmin Reports\{report-date}.json"
)

def build_output_path(template: str, report_date: date) -> str:
    return template.replace("{report-date}", report_date.isoformat())


def get_required_env(var_name: str) -> str:
    value = os.getenv(var_name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")
    return value


def build_report(
    start_date: date,
    end_date: date,
    activities: list[dict[str, Any]],
    workouts: list[dict[str, Any]],
    endurance_score: int,
    fitnessage_data: dict[str, Any],
    hill_score: dict[str, Any],
    lactate_threshold: dict[str, Any],
    running_tolerance: dict[str, Any],
    errors: dict[str, str],
) -> dict[str, Any]:
    if not hill_score or not endurance_score or not fitnessage_data or not lactate_threshold or not running_tolerance:
        status = "failed"
    elif errors:
        status = "partial_success"
    else:
        status = "success"

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "report_date": end_date.isoformat(),
        "endurance_score": endurance_score,
        "fitnessage_data": fitnessage_data,
        "hill_score": hill_score,
        "lactate_threshold": lactate_threshold,
        "running_tolerance": running_tolerance,
        "activities": activities,
        "workouts": workouts,
        "errors": errors
    }


def write_json(path: str, payload: dict[str, Any]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(path, "w", encoding="utf-8") as report_file:
        json.dump(payload, report_file, indent=2, sort_keys=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Garmin Connect metrics and write a JSON report."
    )
    parser.add_argument(
        "--output-template",
        default=os.getenv("GARMIN_REPORT_OUTPUT_TEMPLATE", DEFAULT_OUTPUT_TEMPLATE),
        help=(
            "Output file template. Supports {report-date} token. "
            "Can also be set with GARMIN_REPORT_OUTPUT_TEMPLATE."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    report_date = date.today()
    end_date = report_date
    start_date = end_date - timedelta(days=6)
    start_date_str = start_date.isoformat()
    end_date_str = end_date.isoformat()
    yesterday_str = (report_date - timedelta(days=1)).isoformat()
    report_date_str = report_date.strftime('%Y-%m-%d')

    output_path = build_output_path(args.output_template, report_date)

    activities: list[dict[str, Any]] = []
    workouts: list[dict[str, Any]] = []
    endurance_score: int = 0
    fitnessage_data: dict[str, Any] = {}
    hill_score: dict[str, Any] = {}
    lactate_threshold: dict[str, Any] = {}
    running_tolerance: dict[str, Any] = {}
    report_errors: dict[str, str] = {}

    try:
        username = get_required_env("GARMIN_USERNAME")
        password = get_required_env("GARMIN_PASSWORD")
    except ValueError as exc:
        report_errors["configuration"] = str(exc)
        report = build_report(start_date, end_date, activities, workouts, endurance_score, fitnessage_data, hill_score, lactate_threshold, running_tolerance, report_errors)
        write_json(output_path, report)
        print(str(exc), file=sys.stderr)
        return 2

    try:
        client = Garmin(username, password)
        client.login()
    except Exception as exc:  # pragma: no cover - depends on remote API and credentials
        report_errors["authentication"] = f"{type(exc).__name__}: {exc}"
        report = build_report(start_date, end_date, activities, workouts, endurance_score, fitnessage_data, hill_score, lactate_threshold, running_tolerance, report_errors)
        write_json(output_path, report)
        print("Authentication failed. Check GARMIN_USERNAME and GARMIN_PASSWORD.", file=sys.stderr)
        return 3
    
    try:
        activities_raw =  client.get_activities_by_date(yesterday_str,report_date_str)
        activities = [{key: activities[key] for key in {
            "activityName", 
            "activityTrainingLoad", 
            "activityType",
            "aerobicTrainingEffect",
            "aerobicTrainingEffectMessage",
            "anaerobicTrainingEffect",
            "anaerobicTrainingEffectMessage",
            "averageHR",
            "averageRunningCadenceInStepsPerMinute",
            "averageSpeed",
            "avgPower",
            "beginTimestamp",
            "calories",
            "distance",
            "duration",
            "elapsedDuration",
            "elevationGain",
            "elevationLoss",
            "hrTimeInZone_1",
            "hrTimeInZone_2",
            "hrTimeInZone_3",
            "hrTimeInZone_4",
            "hrTimeInZone_5",
            "locationName",
            "maxHR",
            "maxPower",
            "maxSpeed",
            "moderateIntensityMinutes",
            "movingDuration",
            "powerTimeInZone_1",
            "powerTimeInZone_2",
            "powerTimeInZone_3",
            "powerTimeInZone_4",
            "powerTimeInZone_5",
            "pr",
            "startTimeLocal",
            "steps",
            "trainingEffectLabel",
            "vO2MaxValue",
            "vigorousIntensityMinutes",
            "waterEstimated"
            } if key in activities} for activities in activities_raw]
        for activity in activities:
            activity["activityType"] = activity.get("activityType",{}).get("typeKey", "")
    except Exception as exc:  
        report_errors["activities"] = f"{type(exc).__name__}: {exc}"
    
    try:
        endurance_score_raw =  client.get_endurance_score(start_date_str,)
        endurance_score = int(endurance_score_raw.get("overallScore") or 0)
    except Exception as exc:
        report_errors["endurance_score"] = f"{type(exc).__name__}: {exc}"
        
    try:
        fitnessage_raw =  client.get_fitnessage_data(end_date_str)
        fitnessage_data = {key: fitnessage_raw[key] for key in {"achievableFitnessAge", "chronologicalAge", "fitnessAge"} if key in fitnessage_raw}
    except Exception as exc:  
        report_errors["fitnessage_data"] = f"{type(exc).__name__}: {exc}"
    
    try:
        hill_score_raw =  client.get_hill_score(end_date_str)
        hill_score = {key: hill_score_raw[key] for key in {"enduranceScore","overallScore","strengthScore","vo2Max","vo2MaxPreciseValue"} if key in hill_score_raw}
    except Exception as exc:  
        report_errors["hill_score"] = f"{type(exc).__name__}: {exc}"
        
    try:
        lactate_threshold_raw =  client.get_lactate_threshold()
        lactate_threshold["power"] = lactate_threshold_raw.get("power", {}).get("functionalThresholdPower", 0)
        lactate_threshold["weight"] = lactate_threshold_raw.get("power", {}).get("weight", 0)
        lactate_threshold["heart_rate"] = lactate_threshold_raw.get("speed_and_heart_rate", {}).get("heartRate", 0)
        lactate_threshold["speed"] = lactate_threshold_raw.get("speed_and_heart_rate", {}).get("speed", 0)
    except Exception as exc:  
        report_errors["lactate_threshold"] = f"{type(exc).__name__}: {exc}"
        
    try:
        workouts_raw =  client.get_scheduled_workouts(report_date.year, report_date.month)
        workouts = [{key: workout[key] for key in {"date", "sportTypeKey", "title"} if key in workout} for workout in workouts_raw.get("calendarItems",[]) if workout.get("date", "") == report_date_str]
    except Exception as exc:  
        report_errors["workouts"] = f"{type(exc).__name__}: {exc}"
    
    try:
        running_tolerance_raw =  client.get_running_tolerance(start_date_str, end_date_str)
        running_tolerance = {key: running_tolerance_raw[-1][key] for key in {"calendarDate", "endOfWeek", "startOfWeek","tolerance", "totalDistance", "totalImpactLoad"} if key in running_tolerance_raw[-1]} 
    except Exception as exc: 
        report_errors["running_tolerance"] = f"{type(exc).__name__}: {exc}"

    report = build_report(start_date, end_date, activities, workouts, endurance_score, fitnessage_data, hill_score, lactate_threshold, running_tolerance, report_errors)
    write_json(output_path, report)

    print(f"Report written to: {output_path}")

    if report["status"] != "success":
        for key, error in report_errors.items():
            print(f"Error fetching {key}: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
