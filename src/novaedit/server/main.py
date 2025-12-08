from __future__ import annotations

from fastapi import FastAPI, HTTPException

from novaedit import __version__
from novaedit.model import NovaEditModel
from novaedit.server.api_schemas import EditRequest, EditResponse, StructuredEdit

app = FastAPI(title="NovaEdit", version=__version__)
model = NovaEditModel()
SUPPORTED_LANGUAGES = {"python"}
MAX_CODE_LINES = 2000


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


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

    edits, patch_dsl = model.generate_patch(
        code=request.code,
        start_line=request.start_line,
        end_line=request.end_line,
        diagnostics=request.diagnostics,
        instruction=request.instruction,
    )

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
