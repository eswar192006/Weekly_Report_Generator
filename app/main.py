import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routes.report import router as report_router

app = FastAPI(
    title="ReportGenie AI",
    description="Automated KPI report generator using tool-augmented LLM behavior.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_router)

static_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
outputs_path = os.path.join(os.path.dirname(__file__), "..", "outputs")
sample_data_path = os.path.join(os.path.dirname(__file__), "..", "sample_data")
os.makedirs(outputs_path, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=outputs_path), name="outputs")
app.mount("/sample_data", StaticFiles(directory=sample_data_path), name="sample_data")
app.mount("/", StaticFiles(directory=static_path, html=True), name="frontend")
