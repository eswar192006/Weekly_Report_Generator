import os
import uuid
import pandas as pd
import plotly.express as px

from services.csv_service import load_sales_csv


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs", "charts")


def _ensure_chart_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _save_chart(fig, filename: str) -> str:
    _ensure_chart_dir()
    path = os.path.join(OUTPUT_DIR, filename)
    fig.write_image(path, format="png", scale=2)
    return path


def generate_charts(csv_text: str) -> list:
    df = load_sales_csv(csv_text)
    charts = []
    if df.empty:
        return charts
    if "revenue" not in df.columns:
        return charts

    if "date" in df.columns and not df["date"].isna().all():
        timeline = (
            df.groupby(pd.Grouper(key="date", freq="W"))["revenue"]
            .sum()
            .reset_index()
        )
        fig = px.line(
            timeline,
            x="date",
            y="revenue",
            markers=True,
            title="Revenue Trend by Week",
            labels={"date": "Week", "revenue": "Revenue"},
        )
        fig.update_layout(template="plotly_dark", plot_bgcolor="#0f172a", paper_bgcolor="#0f172a")
        filename = f"revenue-trend-{uuid.uuid4().hex[:8]}.png"
        charts.append({"title": "Revenue Trend", "file": _save_chart(fig, filename)})

    if "category" in df.columns:
        category_summary = df.groupby("category")["revenue"].sum().sort_values(ascending=False).reset_index()
        fig = px.bar(
            category_summary,
            x="category",
            y="revenue",
            color="category",
            title="Sales by Category",
            labels={"revenue": "Revenue", "category": "Category"},
            color_discrete_sequence=px.colors.qualitative.Vivid,
        )
        fig.update_layout(template="plotly_dark", showlegend=False, plot_bgcolor="#0f172a", paper_bgcolor="#0f172a")
        filename = f"category-sales-{uuid.uuid4().hex[:8]}.png"
        charts.append({"title": "Category Sales", "file": _save_chart(fig, filename)})

    if "region" in df.columns:
        region_summary = df.groupby("region")["revenue"].sum().sort_values(ascending=False).reset_index()
        fig = px.bar(
            region_summary,
            x="region",
            y="revenue",
            color="region",
            title="Revenue by Region",
            labels={"revenue": "Revenue", "region": "Region"},
            color_discrete_sequence=px.colors.qualitative.Dark24,
        )
        fig.update_layout(template="plotly_dark", showlegend=False, plot_bgcolor="#0f172a", paper_bgcolor="#0f172a")
        filename = f"region-sales-{uuid.uuid4().hex[:8]}.png"
        charts.append({"title": "Region Sales", "file": _save_chart(fig, filename)})

    for chart in charts:
        chart["url"] = chart["file"].replace(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "").replace("\\", "/")
    return charts
