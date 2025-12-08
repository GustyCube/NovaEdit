from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.syntax import Syntax

from novaedit.model import NovaEditModel
from novaedit.server.api_schemas import EditRequest

console = Console()
app = typer.Typer(help="NovaEdit CLI")


@app.command()
def edit(
    code_file: Path = typer.Argument(..., help="Path to code snippet file."),
    language: str = typer.Option("python", "--language", "-l"),
    start_line: int = typer.Option(1, "--start-line"),
    end_line: Optional[int] = typer.Option(None, "--end-line"),
    instruction: str = typer.Option("", "--instruction", "-i"),
    diagnostic: List[str] = typer.Option(
        None,
        "--diag",
        "-d",
        help="Diagnostics to provide; repeat the flag for multiple entries.",
    ),
    apply: bool = typer.Option(False, "--apply", help="Write changes back to file."),
    use_server: bool = typer.Option(
        False, "--use-server", help="Send to running novaedit server instead of local model."
    ),
    server_url: str = typer.Option("http://localhost:8000/v1/edit", "--server-url"),
) -> None:
    """Generate a patch for a code region and optionally apply it."""
    code = code_file.read_text()
    lines = code.splitlines()
    end_line = end_line or len(lines)
    diagnostics = diagnostic or []

    if use_server:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover
            raise typer.BadParameter("Install httpx or drop --use-server.") from exc
        payload = EditRequest(
            language=language,
            code=code,
            file_path=str(code_file),
            start_line=start_line,
            end_line=end_line,
            diagnostics=diagnostics,
            instruction=instruction,
        )
        with httpx.Client(timeout=30) as client:
            resp = client.post(server_url, json=json.loads(payload.model_dump_json()))
            resp.raise_for_status()
            data = resp.json()
            patch_dsl = data["raw_patch_dsl"]
            new_code = NovaEditModel().apply_patch(code, patch_dsl)
    else:
        model = NovaEditModel(language=language)
        _, patch_dsl = model.generate_patch(
            code=code,
            start_line=start_line,
            end_line=end_line,
            diagnostics=diagnostics,
            instruction=instruction,
        )
        new_code = model.apply_patch(code, patch_dsl)

    console.rule("[bold green]Proposed Patch")
    console.print(patch_dsl.strip() or "(empty)")
    console.rule("[bold blue]Updated Code Preview")
    console.print(Syntax(new_code, "python"))

    if apply:
        code_file.write_text(new_code)
        console.print(f"Applied patch to {code_file}")


@app.command()
def serve(port: int = typer.Option(8000, "--port"), reload: bool = typer.Option(True, "--reload")) -> None:
    """Start the FastAPI server (development convenience)."""
    import uvicorn

    uvicorn.run("novaedit.server.main:app", host="0.0.0.0", port=port, reload=reload)


@app.command()
def regression() -> None:
    """Run the built-in regression cases and print patches."""
    from eval.run_eval_regression import REGRESSION_CASES

    model = NovaEditModel()
    for case in REGRESSION_CASES:
        _, patch_dsl = model.generate_patch(
            code=case["code"],
            start_line=1,
            end_line=len(case["code"].splitlines()),
            diagnostics=case["diagnostics"],
            instruction="fix",
        )
        updated = model.apply_patch(case["code"], patch_dsl)
        console.rule(f"[bold green]{case['name']}")
        console.print(patch_dsl.strip() or "(no patch)")
        console.print(Syntax(updated, "python"))


if __name__ == "__main__":
    app()
