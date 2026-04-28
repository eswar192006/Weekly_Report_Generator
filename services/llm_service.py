import json
import os
from urllib import error, request

from services.chart_service import generate_charts
from services.kpi_service import calculate_kpis


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")


def _extract_json(content: str):
    try:
        trimmed = content.strip()
        start = trimmed.index("{")
        end = trimmed.rfind("}")
        candidate = trimmed[start:end + 1]
        return json.loads(candidate)
    except Exception:
        return None


def _fallback_report(kpis: dict, charts: list, message: str = "") -> dict:
    top_category = kpis.get("top_category", "N/A")
    top_region = kpis.get("top_region", "N/A")
    total_revenue = kpis.get("total_revenue", 0)
    growth_rate = kpis.get("growth_rate", 0)

    summary = (
        f"Total revenue is {total_revenue}, with {growth_rate}% growth in the latest period. "
        f"The leading category is {top_category}, and the strongest region is {top_region}."
    )
    if message:
        summary = f"{summary} Ollama note: {message}"

    return {
        "summary": summary,
        "kpis": kpis,
        "charts": charts,
        "insights": [
            f"{top_category} is the top-performing category.",
            f"{top_region} is the top-performing region.",
            "Review anomaly periods and recent growth before making business decisions.",
        ],
    }


def _ask_ollama(prompt: str) -> str:
    payload = json.dumps(
        {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
    ).encode("utf-8")

    req = request.Request(
        f"{OLLAMA_HOST}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("response", "")
    except error.URLError as exc:
        raise RuntimeError(
            "Unable to reach Ollama. Start Ollama and run "
            f"`ollama pull {OLLAMA_MODEL}` first."
        ) from exc


def generate_report(csv_text: str, user_question: str = "Generate weekly report") -> dict:
    kpis = calculate_kpis(csv_text)
    chart_error = ""
    try:
        charts = generate_charts(csv_text)
    except Exception as exc:
        charts = []
        chart_error = f"Chart generation failed: {exc}"

    prompt = f"""
You are ReportGenie AI, a business reporting assistant.
Create a concise executive KPI report from the provided metrics.

User request:
{user_question}

KPIs:
{json.dumps(kpis, indent=2)}

Charts:
{json.dumps([{"title": chart.get("title"), "url": chart.get("url")} for chart in charts], indent=2)}

Chart status:
{chart_error or "Charts generated successfully."}

Return only valid JSON in this exact shape:
{{
  "summary": "2-4 sentence business summary",
  "insights": [
    "short actionable insight",
    "short actionable insight",
    "short actionable insight"
  ]
}}

Do not invent numeric values. Use only the KPI values above.
"""

    try:
        model_output = _ask_ollama(prompt)
    except RuntimeError as exc:
        messages = [str(exc)]
        if chart_error:
            messages.append(chart_error)
        return _fallback_report(kpis, charts, " ".join(messages))

    parsed = _extract_json(model_output) or {}
    summary = parsed.get("summary") or _fallback_report(kpis, charts)["summary"]
    insights = parsed.get("insights") or _fallback_report(kpis, charts)["insights"]

    return {
        "summary": summary,
        "kpis": kpis,
        "charts": charts,
        "insights": insights,
    }
