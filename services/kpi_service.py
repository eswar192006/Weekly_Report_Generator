import numpy as np
from services.csv_service import load_sales_csv


def calculate_kpis(csv_text: str, period: str = "weekly") -> dict:
    df = load_sales_csv(csv_text)
    if df.empty:
        return {"error": "CSV contains no data."}
    if "revenue" not in df.columns:
        available = ", ".join(df.columns)
        raise ValueError(
            "CSV must contain a numeric sales/value column such as revenue, sales, "
            f"weekly sales, amount, total, price, value, net sales, or gross sales. Available columns: {available}"
        )

    total_revenue = float(df["revenue"].sum())
    avg_order_value = float(df["revenue"].mean()) if not df["revenue"].empty else 0.0
    if "category" in df.columns:
        category_summary = df.groupby("category")["revenue"].sum().sort_values(ascending=False)
        top_category = category_summary.index[0] if not category_summary.empty else "N/A"
    else:
        top_category = "N/A"
    if "region" in df.columns:
        region_summary = df.groupby("region")["revenue"].sum().sort_values(ascending=False)
        top_region = region_summary.index[0] if not region_summary.empty else "N/A"
    else:
        top_region = "N/A"

    if "date" in df.columns and not df["date"].isna().all():
        df = df.dropna(subset=["date"])
        df = df.sort_values(by="date")
        df["period"] = df["date"].dt.to_period("W").dt.start_time
        grouped = df.groupby("period")["revenue"].sum().reset_index()
        grouped["period_index"] = np.arange(len(grouped))

        growth_rate = 0.0
        if len(grouped) >= 2:
            prev = grouped["revenue"].iloc[-2]
            last = grouped["revenue"].iloc[-1]
            growth_rate = float((last - prev) / prev * 100) if prev != 0 else 0.0

        forecast_next_period = None
        if len(grouped) >= 2:
            coeffs = np.polyfit(grouped["period_index"], grouped["revenue"], 1)
            forecast_next_period = float(np.polyval(coeffs, len(grouped)))

        anomaly_threshold = grouped["revenue"].mean() + 2 * grouped["revenue"].std()
        anomalies = grouped[grouped["revenue"] > anomaly_threshold]
        anomaly_count = int(len(anomalies))
        anomaly_periods = anomalies["period"].dt.strftime("%Y-%m-%d").tolist()
    else:
        growth_rate = 0.0
        forecast_next_period = None
        anomaly_count = 0
        anomaly_periods = []

    return {
        "total_revenue": round(total_revenue, 2),
        "growth_rate": round(growth_rate, 2),
        "average_order_value": round(avg_order_value, 2),
        "top_category": str(top_category),
        "top_region": str(top_region),
        "forecast_next_period_revenue": round(forecast_next_period, 2) if forecast_next_period is not None else None,
        "anomaly_count": anomaly_count,
        "anomaly_periods": anomaly_periods,
    }
