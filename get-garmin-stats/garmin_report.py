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

from garminconnect import Garmin

DEFAULT_OUTPUT_TEMPLATE = (
    r"C:\Users\codet\OneDrive\Documents\Garmin Reports\{report-date}.json"
)


@dataclass
class EndpointSpec:
    output_key: str
    method_names: tuple[str, ...]
    args: tuple[Any, ...] = ()


def build_output_path(template: str, report_date: date) -> str:
    return template.replace("{report-date}", report_date.isoformat())


def get_required_env(var_name: str) -> str:
    value = os.getenv(var_name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")
    return value


def invoke_endpoint(client: Garmin, spec: EndpointSpec) -> Any:
    last_error: Exception | None = None
    for method_name in spec.method_names:
        method: Callable[..., Any] | None = getattr(client, method_name, None)
        if callable(method):
            return method(*spec.args)
        last_error = AttributeError(f"Method not found: {method_name}")

    if last_error is None:
        raise AttributeError("No candidate methods were provided.")
    raise last_error


def build_report(
    output_path: str,
    start_date: date,
    end_date: date,
    data: dict[str, Any],
    errors: dict[str, str],
) -> dict[str, Any]:
    if not data:
        status = "failed"
    elif errors:
        status = "partial_success"
    else:
        status = "success"

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "report_path": output_path,
        "status": status,
        "auth_mode": "username_password_env",
        "date_window": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": 7,
        },
        "data": data,
        "errors": errors,
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

    output_path = build_output_path(args.output_template, report_date)

    report_data: dict[str, Any] = {}
    report_errors: dict[str, str] = {}

    try:
        username = get_required_env("GARMIN_USERNAME")
        password = get_required_env("GARMIN_PASSWORD")
    except ValueError as exc:
        report_errors["configuration"] = str(exc)
        report = build_report(output_path, start_date, end_date, report_data, report_errors)
        write_json(output_path, report)
        print(str(exc), file=sys.stderr)
        return 2

    try:
        client = Garmin(username, password)
        client.login()
    except Exception as exc:  # pragma: no cover - depends on remote API and credentials
        report_errors["authentication"] = f"{type(exc).__name__}: {exc}"
        report = build_report(output_path, start_date, end_date, report_data, report_errors)
        write_json(output_path, report)
        print("Authentication failed. Check GARMIN_USERNAME and GARMIN_PASSWORD.", file=sys.stderr)
        return 3

    endpoint_specs = [
        EndpointSpec(
            "fitnessage_data",
            ("get_fitnessage_data", "get_fitness_age_data"),
            (end_date_str,),
        ),
        EndpointSpec("scheduled_workouts", ("get_scheduled_workouts",), (report_date.year, report_date.month)),
        EndpointSpec("activities_by_date", ("get_activities_by_date",), (start_date_str, end_date_str)),
        EndpointSpec("running_tolerance", ("get_running_tolerance",), (start_date_str, end_date_str)),
        EndpointSpec("endurance_score", ("get_endurance_score",), (start_date_str,)),
        EndpointSpec("hill_score", ("get_hill_score",), (start_date_str,)),
        EndpointSpec("max_metrics", ("get_max_metrics",), (end_date_str,)),
        EndpointSpec("lactate_threshold", ("get_lactate_threshold",)),
        EndpointSpec(
            "progress_summary_between_dates",
            ("get_progress_summary_between_dates",),
            (start_date_str, end_date_str),
        ),
    ]

    for spec in endpoint_specs:
        try:
            report_data[spec.output_key] = invoke_endpoint(client, spec)
        except Exception as exc:  # pragma: no cover - depends on remote API responses
            report_errors[spec.output_key] = f"{type(exc).__name__}: {exc}"

    report = build_report(output_path, start_date, end_date, report_data, report_errors)
    write_json(output_path, report)

    print(f"Report written to: {output_path}")

    if report["status"] == "success":
        return 0
    if report["status"] == "partial_success":
        return 4
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
