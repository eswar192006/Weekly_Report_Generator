# ReportGenie AI: Automated KPI Reporter using Tool-Augmented LLM

A demo-ready FastAPI application that accepts CSV sales data, performs KPI calculations and chart generation locally, and uses a local Ollama LLM to produce a polished business report.

## Features

- Upload CSV sales/business dataset
- Backend built with FastAPI and Pandas
- Tool functions for KPI calculation and chart generation
- Local Ollama LLM integration for summary and insight generation
- Structured JSON report output plus HTML report export
- Responsive frontend for upload, report preview, and charts

## Folder Structure

- `app/main.py` - FastAPI application entrypoint
- `app/routes/report.py` - upload and report API route
- `services/kpi_service.py` - KPI and forecasting logic
- `services/chart_service.py` - chart creation and saving
- `services/llm_service.py` - Ollama report summary orchestration
- `services/report_service.py` - HTML report export
- `frontend/` - static single-page UI
- `outputs/charts/` - generated chart images
- `sample_data/sales_sample.csv` - sample dataset

## Setup

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install and start Ollama, then pull a local model:

```bash
ollama pull llama3.1
ollama serve
```

The app uses `llama3.1` by default. To use another local model:

```bash
export OLLAMA_MODEL="mistral"
```

If Ollama runs on another host or port:

```bash
export OLLAMA_HOST="http://localhost:11434"
```

4. Run the app in a separate terminal:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Open the UI:

```text
http://localhost:8000
```

## Demo

- Upload `sample_data/sales_sample.csv`
- Click `Generate Report`
- Review live KPIs, charts, and AI-generated insights
- Download the generated HTML report from the backend output path
