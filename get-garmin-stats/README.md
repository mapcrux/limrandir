# get-garmin-stats

Python script for scheduled extraction of Garmin Connect metrics into JSON.

## What It Collects

- `get_fitnessage_data` (falls back to `get_fitness_age_data` if needed)
- `get_scheduled_workouts` for the current year/month
- `get_activities_by_date` for the last 7 days
- `get_running_tolerance`
- `get_endurance_score`
- `get_hill_score`
- `get_max_metrics`
- `get_lactate_threshold`
- `get_progress_summary_between_dates` for the last 7 days

## Requirements

- Python 3.10+
- Garmin Connect account credentials

## Setup

1. Install dependencies:

```powershell
pip install -r requirements.txt
```

1. Set environment variables (PowerShell examples):

```powershell
setx GARMIN_USERNAME "your-garmin-email"
setx GARMIN_PASSWORD "your-garmin-password"
setx GARMIN_REPORT_OUTPUT_TEMPLATE "C:\Users\codet\OneDrive\Documents\Garmin Reports\{report-date}.json"
```

Open a new terminal after `setx` so the variables are available.

## Run Manually

```powershell
python .\garmin_report.py
```

Optional custom output template:

```powershell
python .\garmin_report.py --output-template "C:\temp\garmin-{report-date}.json"
```

## Output

The script writes one JSON file per run and includes:

- `generated_at`
- `status` (`success`, `partial_success`, `failed`)
- `date_window` (rolling last 7 days)
- `data` (endpoint responses)
- `errors` (endpoint/config/auth failures)

## Exit Codes

- `0`: all endpoints succeeded
- `2`: missing required environment variables
- `3`: authentication failed
- `4`: partial success (some endpoints failed)
- `5`: all data endpoints failed

## Windows Task Scheduler

Recommended action:

- Program/script: `cmd.exe`
- Add arguments: `/c "C:\Users\codet\source\repos\get-garmin-stats\run_garmin_report.bat"`
- Start in: `C:\Users\codet\source\repos\get-garmin-stats`

Use a task account that has access to the configured environment variables.
