from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class EditRequest(BaseModel):
    language: str = Field(default="python", description="Source language, e.g. python")
    code: str = Field(..., max_length=20000, description="Code snippet to edit.")
    file_path: Optional[str] = None
    start_line: int = Field(default=1, ge=1)
    end_line: int = Field(default=1, ge=1)
    diagnostics: List[str] = Field(default_factory=list)
    instruction: Optional[str] = ""
    max_edits: int = Field(default=5, ge=1, le=50)
    temperature: float = 0.2


class StructuredEdit(BaseModel):
    start_line: int
    end_line: int
    replacement: str


class EditResponse(BaseModel):
    edits: List[StructuredEdit]
    raw_patch_dsl: str
    model_version: str = "novaedit-baseline-0.1.0"
