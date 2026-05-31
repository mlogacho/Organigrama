from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .orgchart import infer_org_chart_from_text, to_drawio_xml
from .schemas import OrgChart, TranscriptionResponse
from .transcription import transcribe_audio

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "tmp_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_SUFFIXES = {".mp3", ".mp4", ".wav"}

app = FastAPI(title="Organigrama System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/transcribe", response_model=TranscriptionResponse)
async def transcribe_endpoint(file: UploadFile = File(...), model_size: str = Form("base")) -> TranscriptionResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo sin nombre")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Formato no soportado. Usa mp3, mp4 o wav")

    if model_size not in {"tiny", "base", "small", "medium"}:
        raise HTTPException(status_code=400, detail="model_size inválido")

    temp_name = f"{uuid.uuid4().hex}{suffix}"
    temp_path = UPLOAD_DIR / temp_name

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        transcript = transcribe_audio(temp_path, model_size=model_size)
        org_chart = infer_org_chart_from_text(transcript)
        return TranscriptionResponse(transcript=transcript, org_chart=org_chart)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {exc}") from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass


@app.post("/api/export/drawio")
def export_drawio(org_chart: OrgChart, name: str = "organigrama") -> Response:
    xml = to_drawio_xml(org_chart, diagram_name=name)
    filename = f"{name.strip() or 'organigrama'}.drawio"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=xml, media_type="application/xml", headers=headers)
