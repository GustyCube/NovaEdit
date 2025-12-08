from __future__ import annotations

import asyncio
import logging
import os
from functools import partial
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from novaedit import __version__
from novaedit.model import NovaEditModel
from novaedit.server.api_schemas import EditRequest, EditResponse, StructuredEdit

app = FastAPI(title="NovaEdit", version=__version__)

MODEL_LANGUAGE = os.getenv("NOVAEDIT_LANGUAGE", "python")
MODEL_ID = os.getenv("NOVAEDIT_MODEL_ID")
MODEL_DEVICE = os.getenv("NOVAEDIT_DEVICE")
SUPPORTED_LANGUAGES = {"python", "javascript"}
MAX_CODE_LINES = int(os.getenv("NOVAEDIT_MAX_CODE_LINES", "2000"))
MAX_CONCURRENT = int(os.getenv("NOVAEDIT_MAX_CONCURRENT", "8"))
REQUEST_TIMEOUT = float(os.getenv("NOVAEDIT_REQUEST_TIMEOUT", "15"))
LOG_REQUESTS = os.getenv("NOVAEDIT_LOG_REQUESTS", "false").lower() in {"1", "true", "yes"}
CORS_ORIGINS = os.getenv("NOVAEDIT_CORS_ORIGINS", "")
ORIGINS: List[str] = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

if ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

model = NovaEditModel(language=MODEL_LANGUAGE, hf_model_id=MODEL_ID, device=MODEL_DEVICE)
semaphore = asyncio.Semaphore(MAX_CONCURRENT)
logger = logging.getLogger("novaedit.server")
logging.basicConfig(level=logging.INFO if LOG_REQUESTS else logging.WARNING)


@app.get("/health")
async def health() -> dict[str, str]:
    backend = "hf" if MODEL_ID else "heuristic"
    return {
        "status": "ok",
        "version": __version__,
        "backend": backend,
        "language": MODEL_LANGUAGE,
        "cors": ORIGINS,
    }


@app.post("/v1/edit", response_model=EditResponse)
async def edit(request: EditRequest) -> EditResponse:
    if request.start_line > request.end_line:
        raise HTTPException(status_code=400, detail="start_line must be <= end_line")
    if request.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {request.language}")
    if request.code.count("\n") > MAX_CODE_LINES:
        raise HTTPException(
            status_code=400,
            detail=f"Code snippet too large; limit {MAX_CODE_LINES} lines.",
        )

    try:
        semaphore.acquire_nowait()
    except Exception:
        raise HTTPException(status_code=429, detail="Too many concurrent requests")
    try:
        if LOG_REQUESTS:
            logger.info("edit request language=%s start=%s end=%s", request.language, request.start_line, request.end_line)
        loop = asyncio.get_event_loop()
        generate = partial(
            model.generate_patch,
            code=request.code,
            start_line=request.start_line,
            end_line=request.end_line,
            diagnostics=request.diagnostics,
            instruction=request.instruction,
        )
        edits, patch_dsl = await asyncio.wait_for(loop.run_in_executor(None, generate), timeout=REQUEST_TIMEOUT)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out")
    finally:
        semaphore.release()

    structured = [
        StructuredEdit(
            start_line=e.start_line,
            end_line=e.end_line,
            replacement=e.replacement,
        )
        for e in edits[: request.max_edits]
    ]
    return EditResponse(edits=structured, raw_patch_dsl=patch_dsl)


def get_app() -> FastAPI:
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("novaedit.server.main:app", host="0.0.0.0", port=8000, reload=True)
