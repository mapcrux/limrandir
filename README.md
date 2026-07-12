# Limrandir

A personal fitness-driven fantasy campaign project.

This repository combines Garmin training data collection with AI-assisted narrative generation to power an ongoing roleplaying campaign centered on Limrandir, a Dúnedain ranger traveling south to aid Aragorn.

## What This Project Does

- Collects Garmin Connect metrics with a Python script.
- Stores a structured daily/weekly report in `garmin-stats.json`.
- Uses those metrics as story input for an AI game master prompt.
- Updates character progression, quest outcomes, campaign chronicle notes, and upcoming quests in markdown/json files.

## Repository Structure

- `get-garmin-stats/`
  - `garmin_report.py`: Fetches Garmin data and writes JSON output.
  - `requirements.txt`: Python dependencies.
  - `run_garmin_report.bat`: Windows helper for local scheduling.
  - `README.md`: Detailed usage for Garmin extraction.
- `garmin-stats.json`
  - Latest generated Garmin report used by downstream narrative updates.
- `mapex-task-prompt.txt`
  - Game master instructions describing how AI should translate training data into campaign progression.
- `quest-data/`
  - `Limrandir.md`: Character sheet and progression state.
  - `quest-log.md`: Active and resolved quests.
  - `campaign-chronicle.md`: Ongoing story continuity and campaign memory.
  - `leveling-guide.json`: Attribute thresholds and title progression.

## Garmin Data Pipeline

The data collection script in `get-garmin-stats/garmin_report.py` authenticates to Garmin Connect and gathers multiple fitness endpoints, including activities, workouts, endurance metrics, and progression summaries.

### Required Environment Variables

- `GARMIN_USERNAME`
- `GARMIN_PASSWORD`

### Optional Environment Variable

- `GARMIN_REPORT_OUTPUT_TEMPLATE`
  - Supports `{report-date}` token.
  - In GitHub Actions, this repo sets it to the root output file: `garmin-stats.json`.

## Local Run

From the repository root:

```powershell
python -m pip install -r .\get-garmin-stats\requirements.txt
python .\get-garmin-stats\garmin_report.py
```

## GitHub Automation

The workflow in `.github/workflows/garmin-daily-report.yml` is configured to:

- Run daily at 5:00 AM Eastern Time.
- Execute the Garmin report script on GitHub-hosted runners.
- Inject `GARMIN_USERNAME` and `GARMIN_PASSWORD` from repository secrets.
- Set `GARMIN_REPORT_OUTPUT_TEMPLATE` to write `garmin-stats.json` in the repo.
- Commit and push changes when `garmin-stats.json` is updated.

## AI-Driven Campaign Layer

The narrative system is guided by `mapex-task-prompt.txt`, which instructs an AI game master to:

- Convert Garmin metrics into RPG attribute updates for Limrandir.
- Resolve completed or missed quests based on activity evidence.
- Advance campaign story arcs and continuity.
- Generate upcoming quests from scheduled workouts.

This creates a loop where real training drives character growth and story progression.

## Notes

- Keep Garmin credentials in secrets or local environment variables only.
- Avoid committing personal credentials or raw private account exports.
- Review generated narrative updates for lore continuity before publishing or sharing.
