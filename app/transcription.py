from __future__ import annotations

from pathlib import Path

import whisper


_model_cache: dict[str, whisper.Whisper] = {}


def transcribe_audio(file_path: Path, model_size: str = "base") -> str:
    model = _model_cache.get(model_size)
    if model is None:
        model = whisper.load_model(model_size)
        _model_cache[model_size] = model

    result = model.transcribe(str(file_path), language="es")
    return (result.get("text") or "").strip()
