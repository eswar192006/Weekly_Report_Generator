import os
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from services.llm_service import generate_report
from services.report_service import build_html_report

router = APIRouter(prefix="/api", tags=["report"])

@router.post("/upload")
async def upload_report(
    file: UploadFile = File(...),
    question: str = Form("Generate weekly KPI report"),
):
    if file.content_type not in ["text/csv", "application/vnd.ms-excel", "application/octet-stream"]:
        raise HTTPException(status_code=400, detail="Please upload a valid CSV file.")

    raw_bytes = await file.read()
    try:
        csv_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Unable to decode CSV file. Please use UTF-8 encoding.")

    try:
        report = generate_report(csv_text, question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    report_html_path = build_html_report(report)
    report_url = "/outputs/" + os.path.basename(report_html_path)

    return {
        "summary": report["summary"],
        "kpis": report["kpis"],
        "charts": report["charts"],
        "insights": report["insights"],
        "report_url": report_url,
    }

@router.get("/sample")
def sample_csv():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "sales_sample.csv")
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample data not found.")
    return {
        "sample_file": "/sample_data/sales_sample.csv"
    }
