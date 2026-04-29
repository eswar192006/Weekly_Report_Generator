# Weekly Report Generator / InsightForge AI / ReportGenie AI

## 1. Project Overview

This project is a full-stack CSV analytics application that accepts business data, infers schema, computes KPIs, generates charts, creates an AI-style executive report, and exposes a shareable saved report plus a follow-up chat workflow.

The repository currently uses multiple product names:

- `Weekly_Report_Generator-main` as the folder/repo name
- `InsightForge AI` in `README.md` and frontend branding
- `ReportGenie AI` in the FastAPI metadata and backend report payloads

That naming inconsistency is one of the maintainability issues in the codebase.

## 2. Main Problem This Project Solves

Business CSV files are usually raw, inconsistent, and hard for non-technical users to interpret quickly. This project solves that by:

- Uploading a CSV file through a web UI
- Detecting semantic roles such as `date`, `revenue`, `category`, and `region`
- Normalizing data types and labels
- Running KPI and anomaly analysis
- Producing charts and narrative text
- Saving the report for later reopening
- Supporting question-answer chat over the saved analysis

In short, the product turns spreadsheet-like data into an analytics story.

## 3. High-Level Architecture

### Backend

- Framework: `FastAPI`
- Runtime server: `uvicorn`
- Core data engine: `pandas`, `numpy`
- Visualization payload generation: `plotly`, `kaleido`
- Upload/form handling: `python-multipart`
- Optional environment config: `python-dotenv`
- Optional LLM provider: local `Ollama`-compatible API

### Frontend

- Framework: `React 19`
- Build tool: `Vite`
- Styling: `Tailwind CSS v4`
- Motion/animation: `framer-motion`
- Icons: `lucide-react`
- Charts: `react-plotly.js` + `plotly.js-dist-min`

### AI / Agent Pattern

The backend does not let the LLM directly invent analytics. Instead, it uses a controlled tool-calling loop:

1. Build a system prompt describing available tools.
2. Ask the LLM what to do next.
3. If the LLM asks for a tool, execute a real Python function.
4. Feed the tool result back to the LLM.
5. Repeat until final structured JSON is returned.
6. If the LLM fails or Ollama is unavailable, fall back to deterministic report generation.

This is the most important design decision in the repository.

## 4. Request/Response Flow

### Report generation flow

1. User uploads CSV in the React UI.
2. Frontend sends `POST /api/analyze`.
3. Backend validates file type, size, encoding, and prompt.
4. `prepare_dataset()` reads and normalizes the CSV.
5. Schema and metric roles are inferred heuristically, with optional local LLM assist.
6. Data quality report is built.
7. `AgentController.run_report()` invokes tools like KPI and chart generation.
8. Report payload is normalized and saved to `outputs/reports/*.json`.
9. Dataset records are saved to `outputs/datasets/*.json`.
10. Frontend renders summary, metrics, story, charts, and chat suggestions.

### Chat flow

1. Frontend sends `POST /api/chat` with `report_id` and message.
2. Backend reloads saved report and dataset.
3. `AgentController.run_chat()` may call tools for fresh KPI-backed reasoning.
4. If LLM orchestration fails, fallback chat text is returned.

## 5. Repository Structure

### Core source directories

- `app/`: FastAPI application and routes
- `services/`: business logic, schema inference, KPI engine, charts, LLM orchestration, persistence
- `frontend/`: React client
- `sample_data/`: bundled CSVs for testing/demo

### Other important directories

- `outputs/reports/`: saved report JSON payloads
- `outputs/datasets/`: saved normalized dataset JSON payloads
- `outputs/charts/`: generated chart assets from earlier runs
- `frontend/dist/`: built frontend bundle
- `frontend/node_modules/`: installed frontend dependencies

### Low-value or generated content

- `__pycache__/`: Python bytecode caches
- `outputs/*.html` and old artifacts: generated outputs, not source

## 6. File-by-File Report

### Root files

#### `README.md`
- Purpose: human-readable product overview, setup, run instructions, and endpoint list.
- Notes: brands the app as `InsightForge AI`, which conflicts with backend naming.

#### `requirements.txt`
- Python dependencies:
  - `fastapi==0.111.1`
  - `uvicorn[standard]==0.23.2`
  - `pandas==2.2.3`
  - `numpy==2.2.5`
  - `plotly==6.1.1`
  - `kaleido==1.2.0`
  - `python-multipart>=0.0.7`
  - `python-dotenv==1.0.0`

#### `LICENSE`
- MIT license.

#### `FIXES_SUMMARY.md`
- Documents trust/data-integrity fixes already implemented.
- Not executable source, but useful design history.

#### `fixes_reference.py`
- Lightweight code-change reference describing the five trust fixes.
- Mostly documentation via Python structure and print output.

#### `test_fixes.py`
- Manual validation script for deduplication, schema mapping, growth warning, anomaly detection, and confidence scoring.
- Not a formal `pytest` test; behaves more like a scripted smoke test.

#### `test_anomaly.py`
- Prints grouped revenue by period to inspect anomaly-related behavior.
- Also a manual investigation script, not an automated unit test.

### `app/`

#### `app/__init__.py`
- Empty package marker.

#### `app/main.py`
- Purpose: bootstraps FastAPI application, CORS, router registration, static file mounting, frontend serving.
- Key functions:
  - `_cors_origins()`: reads `CORS_ALLOW_ORIGINS` from environment or falls back to localhost values.
  - `index()`: serves `frontend/dist/index.html`.
- Notes:
  - Mounts `/outputs`, `/sample_data`, and optionally `/assets`.
  - Assumes frontend has already been built.

#### `app/routes/report.py`
- Purpose: API layer for analysis, saved reports, chat, sample data, and tool inspection.
- Key functions:
  - `_validate_text_input(value, field_name, max_length)`: trims and validates prompt/chat length.
  - `_build_report_payload(dataset, prompt)`: runs the agent, assembles report JSON, saves it, and adds share URL.
  - `analyze_csv(...)`: upload endpoint for CSV analysis.
  - `get_report(report_id)`: reopens saved report JSON.
  - `chat_with_report(report_id, message)`: follow-up QA on a saved report.
  - `sample_csv()`: exposes bundled sample CSV path.
  - `list_tools()`: returns tool registry metadata.
- Important constraints:
  - Upload size limited to 2 MB.
  - Prompt max length: 1500.
  - Chat message max length: 1000.

### `services/`

#### `services/__init__.py`
- Empty package marker.

#### `services/tool_service.py`
- Purpose: defines the tool contract that the LLM/agent is allowed to use.
- Main data structure:
  - `TOOL_REGISTRY`: metadata for `calculate_kpis`, `generate_chart`, and `generate_chart_set`.
- Key functions:
  - `_get_dataframe(dataset)`: validates active dataset contains a DataFrame.
  - `_summarize_tool_output(name, output)`: creates compact transparency metadata.
  - `execute_tool(name, arguments, dataset)`: guarded dispatcher for approved tools.
- Importance:
  - This is the safety boundary between the LLM layer and actual analytics functions.

#### `services/agent_controller.py`
- Purpose: orchestrates multi-step agent reasoning for report generation and chat.
- Main class:
  - `AgentController`
- Methods:
  - `__init__(max_iterations=6)`: controls maximum tool-calling loop length.
  - `_dataset_context(dataset)`: returns schema and preview subset.
  - `_append_tool_result(messages, tool_name, arguments, result)`: injects tool output back into the agent conversation.
  - `_normalize_report_payload(final_payload, tool_results, tool_log, dataset)`: converts final LLM JSON into stable report schema.
  - `run_report(prompt, dataset)`: orchestrates tool use and final report creation.
  - `run_chat(message, dataset, report_context)`: orchestrates tool use and final chat response.
- Special logic:
  - Blocks KPI-heavy reporting when duplicate ratio appears above 20%.
  - Downgrades insight tone when duplication is moderate or confidence is low.
  - Falls back to deterministic reporting if LLM orchestration fails.
- Issues seen:
  - Contains mojibake/encoding artifacts like `âš ï¸`.
  - Duplicate-ratio extraction parses text from confidence limitations instead of using structured fields, which is brittle.

#### `services/llm_service.py`
- Purpose: handles Ollama API communication, system prompts, schema suggestion, and non-LLM fallback content generation.
- Module variables:
  - `OLLAMA_HOST`
  - `OLLAMA_MODEL`
  - `OLLAMA_TIMEOUT_SECONDS`
- Key functions:
  - `_extract_json(content)`: pulls JSON object from raw model output.
  - `_post_ollama_chat(messages, response_format="json")`: HTTP call to local Ollama server.
  - `ask_agent(messages)`: gets structured agent response.
  - `suggest_schema_mapping(column_summaries)`: optional LLM-based schema assist.
  - `build_report_system_prompt(tool_registry)`: prompt for report-generation agent.
  - `build_chat_system_prompt(tool_registry)`: prompt for chat agent.
  - `fallback_report(tool_results, dataset_context, prompt)`: deterministic report text.
  - `fallback_chat(message, report_context, tool_results)`: deterministic chat response.
- Strength:
  - Strong prompt emphasis on tool-grounded analytics and confidence-based language.
- Risk:
  - JSON extraction is permissive and may fail on malformed model output.

#### `services/csv_service.py`
- Purpose: CSV ingestion, schema inference, metric inference, normalization, preview generation, and dataset packaging.
- Constants:
  - role/metric keywords and aliases
  - `SCHEMA_LLM_ASSIST`
  - `LLM_CONFIDENCE_THRESHOLD`
  - `REVENUE_CONFIDENCE_WARNING_THRESHOLD`
  - `METRIC_DEFINITIONS`
- Key functions:
  - `_metric_text_score()`: score column name against metric aliases/keywords.
  - `_find_metric_candidates()`: finds candidate columns for revenue, price, volume, cost, profit, discounts.
  - `_select_best_candidate()`: picks best-scoring candidate.
  - `_choose_revenue_source()`: prioritizes revenue, then gross sales, then computed revenue.
  - `_infer_metrics()`: builds metric map and diagnostics.
  - `_clean_numeric_string()`: normalizes numeric-like text.
  - `_clean_column_name()`: standardizes column labels.
  - `_make_unique_columns()`: avoids duplicate normalized column names.
  - `_tokenize()`: tokenizes column labels.
  - `_normalize_value()`: standardizes text values.
  - `_stringify()`: string-casts series safely.
  - `_numeric_score()`: estimates numeric parseability ratio.
  - `_text_score()`: role/alias matching score.
  - `_date_parse_profile()`: tries both MDY and DMY parsing and scores confidence.
  - `_infer_value_column()`: heuristic revenue-like column detection.
  - `_infer_date_column()`: heuristic date column detection.
  - `_infer_dimension_column()`: finds category/region candidates.
  - `_infer_role_map_heuristic()`: infers date/revenue/category/region roles.
  - `_column_summary_for_llm()`: summarizes columns for optional LLM schema assist.
  - `_try_llm_role_map()`: invokes local LLM schema mapping when heuristics are weak.
  - `_coerce_dataframe()`: creates normalized columns such as `date`, `category`, `region`, `revenue`.
  - `_column_profile()`: creates schema metadata per column.
  - `dataset_preview()`: returns first rows for UI preview.
  - `serialize_dataframe_records()`: JSON-safe dataset records.
  - `dataframe_from_records()`: rebuilds DataFrame from saved records.
  - `prepare_dataset()`: main ingestion pipeline.
  - `load_sales_csv()`: convenience wrapper around `prepare_dataset()`.
- Importance:
  - This is the heaviest and most central data-preparation module in the project.

#### `services/data_quality.py`
- Purpose: blank detection, text normalization, numeric parsing, duplicate analysis, categorical consistency checks, and full data quality reporting.
- Key functions:
  - `blank_mask()`: detects empty/blank cells.
  - `normalize_text()`: trims and compresses whitespace.
  - `normalize_category_labels()`: title-cases normalized categorical values.
  - `_numeric_formatting_mask()`: detects formatted numeric text.
  - `parse_numeric_series()`: converts messy numeric text to numeric dtype.
  - `inconsistent_categorical_values()`: groups spelling/case variants.
  - `deduplicate_dataframe()`: removes duplicates using `date`, `category`, `region`, `revenue` when possible.
  - `duplicate_row_count()`: counts duplicates using the same key logic.
  - `build_data_quality_report(...)`: returns summary, per-column issues, warnings, preprocessing summary.
- Importance:
  - This module enforces trustworthiness and is directly referenced by KPI confidence scoring.

#### `services/kpi_service.py`
- Purpose: KPI calculation, trend analysis, anomaly detection, comparisons, confidence scoring, and insight flag generation.
- Key functions:
  - `_format_period()`: stringifies timestamp output.
  - `_series_slope()`: linear slope over a sequence.
  - `_series_direction()`: maps slope to `upward`, `downward`, or `stable`.
  - `_derive_confidence_score(schema_metadata)`: converts data quality/signal ambiguity into a 0-1 confidence score and limitations list.
  - `calculate_kpis(data, period="W", schema_metadata=None, metric_roles=None)`: main analytics engine.
- Major behaviors:
  - Deduplicates before KPI calculation.
  - Calculates revenue, profit, cost, units, discounts, margin, and averages.
  - Produces category/region breakdowns.
  - Builds time-series growth and naive forecast when dates exist.
  - Uses both std-dev and IQR approaches for anomaly detection.
  - Adds warning when growth is based on too few periods.
  - Returns `headline`, `trend`, `comparisons`, `breakdowns`, `anomalies`, `trust`, and `insight_flags`.

#### `services/chart_service.py`
- Purpose: chart recommendation and Plotly figure generation.
- Constants:
  - `CHART_THEME`
- Key functions:
  - `_figure_payload(fig)`: converts Plotly figure into JSON payload for frontend.
  - `_candidate_dimensions(df)`: finds chartable categorical columns.
  - `suggest_chart_specs(data, max_charts=3)`: suggests chart types and fields.
  - `generate_chart(data, chart_type, x_field=None, y_field="revenue", color_field=None)`: builds line/bar/pie chart payload.
  - `generate_charts(data, max_charts=3)`: bulk chart generation wrapper.
- Notes:
  - Weekly grouping is hard-coded for line charts.
  - Uses themed Plotly JSON rather than static images.

#### `services/report_service.py`
- Purpose: saved report and dataset persistence.
- Constants:
  - `BASE_OUTPUT_DIR`
  - `REPORTS_DIR`
  - `DATASETS_DIR`
  - `REPORT_ID_PATTERN`
- Key functions:
  - `_ensure_storage_dirs()`: creates output directories.
  - `_sanitize_report_id(report_id)`: restricts report ID format.
  - `_report_path(report_id)`: computes report JSON path.
  - `_dataset_path(report_id)`: computes dataset JSON path.
  - `save_report(report, dataset_records)`: writes report and normalized dataset JSON.
  - `load_report(report_id)`: reads saved report.
  - `load_report_dataset(report_id)`: reads saved dataset and rebuilds DataFrame.
- Strength:
  - Uses strict report ID validation to reduce path abuse risk.

### `frontend/`

#### `frontend/package.json`
- Defines frontend package metadata and JavaScript dependencies.

#### `frontend/vite.config.js`
- Configures Vite with React and Tailwind plugins.

#### `frontend/index.html`
- Standard Vite HTML entry document.

#### `frontend/src/main.jsx`
- React bootstrap entry point.

#### `frontend/src/index.css`
- Global CSS, theme variables, background gradients, font setup, scrollbar styling.
- Uses Tailwind v4 `@import "tailwindcss";` and `@theme`.

#### `frontend/src/App.jsx`
- Main application component and frontend state coordinator.
- Helper functions:
  - `mapMetrics(report)`: maps backend KPI payload into UI cards.
  - `downloadInsights(report)`: exports summary/insight/story JSON.
- Main component:
  - `App()`
- Responsibilities:
  - Theme state
  - File selection state
  - Prompt state
  - Report loading state
  - Shared-report loading from query string
  - Calling `/api/analyze`, `/api/sample`, and `/api/chat`
  - Rendering summary, schema, preview, insights, story, charts, and chat
- Issues seen:
  - Contains encoding artifacts like `Iâ€™ll`, `Weâ€™ll`, `Â·`.
  - Uses `useMemo` reasonably for metrics, but overall state is concentrated in one large component.

#### `frontend/src/components/DataDropzone.jsx`
- Component: `DataDropzone(...)`
- Purpose: upload/dropzone UI, prompt editor, analyze button, sample loader.

#### `frontend/src/components/MetricCard.jsx`
- Helper:
  - `formatValue(value, kind="number")`
- Component:
  - `MetricCard({ metric, index })`
- Purpose: styled KPI card renderer.

#### `frontend/src/components/ChartPanel.jsx`
- Component:
  - `ChartPanel({ chart, active })`
- Purpose: lazy-loaded Plotly chart renderer with active/inactive styling.

#### `frontend/src/components/StoryMode.jsx`
- Component:
  - `StoryMode({ story, activeStoryId, onActivate })`
- Purpose: narrative chapter scroller that syncs highlighted story section with charts.

#### `frontend/src/components/ChatPanel.jsx`
- Helper:
  - `toolLabel(tool)`
  - `submitMessage(nextMessage)`
- Component:
  - `ChatPanel({ reportId, suggestions, onSend, messages, loading })`
- Purpose: renders assistant/user messages, suggested questions, and input box.

### `sample_data/`

#### `sample_data/sales_sample.csv`
- Demo dataset used by sample loading endpoint.

#### `sample_data/Financial Sample.csv`
- Larger real-world-like dataset used by manual fix-validation scripts.

#### `sample_data/x.csv`
- Additional sample file; likely for quick testing.

## 7. Libraries and Frameworks Used

### Backend libraries

- `FastAPI`: API framework
- `uvicorn`: ASGI server
- `pandas`: data ingestion, cleaning, grouping, coercion
- `numpy`: trend slope, forecast, numeric operations
- `plotly`: chart figure generation
- `kaleido`: Plotly export support
- `python-multipart`: file upload and form parsing
- `python-dotenv`: environment support
- Python stdlib:
  - `os`
  - `re`
  - `json`
  - `uuid`
  - `datetime`
  - `typing`
  - `io.StringIO`
  - `urllib.request`
  - `urllib.error`

### Frontend libraries

- `react`
- `react-dom`
- `vite`
- `@vitejs/plugin-react`
- `tailwindcss`
- `@tailwindcss/vite`
- `framer-motion`
- `lucide-react`
- `react-plotly.js`
- `plotly.js-dist-min`

### External platform dependency

- `Ollama` local chat API, expected by `services/llm_service.py`

## 8. Tool and LLM Design

### Tools exposed to the agent

#### `calculate_kpis`
- Real function source: `services.kpi_service.calculate_kpis`
- Purpose: compute metrics, trend signals, breakdowns, anomalies, and trust score.

#### `generate_chart`
- Real function source: `services.chart_service.generate_chart`
- Purpose: produce a single chart from the active dataset.

#### `generate_chart_set`
- Real function source:
  - `services.chart_service.generate_charts`
  - `services.chart_service.suggest_chart_specs`
- Purpose: create a recommended multi-chart package.

### LLM orchestration behavior

- The agent is asked to return either:
  - a tool call JSON object
  - a final JSON object
- The backend never directly executes arbitrary code from the model.
- Tool outputs are re-injected into the message history as `TOOL_RESULT`.
- This is effectively a lightweight custom agent loop rather than a full external agent framework.

### Strength of this design

- Analytics claims can be grounded in real computation.
- The system can degrade gracefully when the LLM is unavailable.
- The tool registry is explicit and inspectable through `/api/tools`.

### Weakness of this design

- The prompts are large and string-based rather than strongly typed end to end.
- Duplicate-blocking logic partially relies on parsing warning text.
- There is no formal schema validator for final LLM output beyond best-effort normalization.

## 9. Problems Found in the Current Project

### Product and naming inconsistency

- Repo name, README, frontend, and backend use different product names.
- This creates confusion in documentation, screenshots, reports, and handoff.

### Encoding/mojibake issues

- Several files contain corrupted characters like:
  - `Iâ€™ll`
  - `Weâ€™ll`
  - `Â·`
  - `âš ï¸`
- This affects professional polish and report readability.

### Manual tests instead of formal automated tests

- `test_fixes.py` and `test_anomaly.py` are scripts, not `pytest` test suites.
- There are no assertions across the main API routes or frontend behavior.

### Large `App.jsx`

- The main React component handles many concerns:
  - data loading
  - chat
  - share-link state
  - status messaging
  - report rendering
- This makes the frontend harder to extend and test.

### B brittle duplication block

- The agent controller derives duplication ratio by parsing natural-language limitation strings.
- A structured numeric field would be safer and easier to maintain.

### Unused or unclear directories

- `app/templates/` exists but was not part of the active source flow inspected here.
- This suggests leftover structure from an earlier architecture.

### Build/runtime coupling

- Backend serves `frontend/dist/index.html`, so the frontend must be built before the root route works properly.

## 10. Solutions Already Implemented in This Codebase

The repository already contains a meaningful trust-improvement pass. The key fixes are:

### Duplicate handling

- Duplicate-like rows are removed before KPI calculation.
- High duplication reduces confidence heavily.
- Very high duplication can block report-style insight generation.

### Better revenue detection

- Revenue selection prioritizes actual revenue/gross sales semantics over price fallback.
- This reduces false KPI inflation from confusing unit price with total sales.

### Growth reliability warnings

- If too few time periods exist, growth metrics receive explicit warnings.

### Stronger anomaly detection

- KPI engine combines standard deviation and IQR logic for anomaly detection.

### Confidence-aware reporting

- Prompts and controller logic downgrade or block strong claims when data quality is weak.

## 11. Strengths of the Project

- Clear separation between API, services, and frontend.
- Strong practical use of `pandas` for business-data normalization.
- Good fallback strategy when Ollama is unavailable.
- Explicit tool registry improves transparency and safety.
- Shareable saved reports are a strong product feature.
- Story mode adds a differentiated UI layer beyond standard dashboards.

## 12. Weaknesses and Improvement Opportunities

### Short-term improvements

- Standardize the product name across repo, UI, API metadata, and saved report payloads.
- Fix all encoding issues to clean UTF-8 text.
- Replace manual scripts with `pytest` tests.
- Add structured duplicate ratio to KPI/data-quality payloads.
- Add API tests for `/api/analyze`, `/api/chat`, and `/api/reports/{id}`.

### Medium-term improvements

- Split `App.jsx` into hooks and smaller feature containers.
- Add stronger typed response schemas on the backend with Pydantic models.
- Version the saved report schema explicitly.
- Add better frontend error states for blocked/low-confidence reports.

### Long-term improvements

- Add authentication and multi-user report storage if this becomes a real product.
- Add database persistence instead of filesystem JSON only.
- Add richer chart types and user-configurable grouping periods.
- Support Excel files and multi-sheet ingestion.

## 13. Summary

This is a solid prototype-to-product-style analytics storytelling application built with FastAPI, React, Pandas, Plotly, and an Ollama-compatible local LLM flow. The technical center of gravity is in `csv_service.py`, `kpi_service.py`, `agent_controller.py`, and `llm_service.py`.

The biggest engineering idea in the project is not the UI. It is the controlled tool-based AI architecture: the model is instructed to ask for real KPI and chart tools instead of inventing results. That gives the project a stronger trust model than a plain text-generation analytics app.

The biggest current risks are naming inconsistency, encoding issues, reliance on manual tests, and a few brittle pieces of logic around data quality enforcement. Even with those issues, the repository has a good foundation and already includes thoughtful safety fixes around duplicate data, confidence scoring, and schema ambiguity.
