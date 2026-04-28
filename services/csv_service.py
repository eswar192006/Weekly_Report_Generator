from io import StringIO
import re

import pandas as pd


VALUE_KEYWORDS = [
    "revenue",
    "sales",
    "sale",
    "amount",
    "total",
    "price",
    "value",
    "income",
    "earning",
    "turnover",
    "gmv",
    "net",
    "gross",
]
VALUE_EXCLUDE_KEYWORDS = [
    "id",
    "code",
    "postal",
    "zip",
    "phone",
    "qty",
    "quantity",
    "count",
    "number",
]
DATE_ALIASES = ["date", "order date", "purchase date", "sales date", "week", "month"]
CATEGORY_ALIASES = ["category", "product category", "item category", "department", "segment"]
REGION_ALIASES = [
    "region",
    "ship-state",
    "ship state",
    "state",
    "ship-city",
    "ship city",
    "city",
    "ship-country",
    "ship country",
    "country",
]


def _clean_column_name(column: str) -> str:
    return re.sub(r"\s+", " ", str(column).strip().lower())


def _tokenize(column: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", column))


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for column in candidates:
        if column in df.columns:
            return column
    return None


def _numeric_score(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    return float(numeric.notna().mean())


def _infer_value_column(df: pd.DataFrame) -> str | None:
    best_column = None
    best_score = 0.0

    for column in df.columns:
        tokens = _tokenize(column)
        if tokens.intersection(VALUE_EXCLUDE_KEYWORDS):
            continue
        keyword_hits = len(tokens.intersection(VALUE_KEYWORDS))
        phrase_hit = any(keyword in column for keyword in VALUE_KEYWORDS)
        if not keyword_hits and not phrase_hit:
            continue

        numeric_score = _numeric_score(df[column])
        if numeric_score < 0.5:
            continue

        score = numeric_score + keyword_hits + (0.5 if phrase_hit else 0)
        if score > best_score:
            best_column = column
            best_score = score

    return best_column


def load_sales_csv(csv_text: str) -> pd.DataFrame:
    df = pd.read_csv(StringIO(csv_text), low_memory=False)
    df.columns = [_clean_column_name(column) for column in df.columns]

    date_column = _first_existing_column(df, DATE_ALIASES)
    if date_column:
        df["date"] = pd.to_datetime(df[date_column], errors="coerce", format="mixed")

    value_column = _infer_value_column(df)
    if value_column:
        df["revenue"] = pd.to_numeric(df[value_column], errors="coerce").fillna(0)

    category_column = _first_existing_column(df, CATEGORY_ALIASES)
    if category_column:
        df["category"] = df[category_column].fillna("Unknown").astype(str)

    region_column = _first_existing_column(df, REGION_ALIASES)
    if region_column:
        df["region"] = df[region_column].fillna("Unknown").astype(str)

    return df
