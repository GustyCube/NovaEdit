from novaedit.model.modeling_novaedit import NovaEditModel, build_patch_dsl


def test_generate_patch_fixes_name_error():
    code = "def foo(items):\n    for itm in items:\n        print(item)\n"
    diags = ["NameError: name 'item' is not defined"]
    model = NovaEditModel()
    edits, patch_dsl = model.generate_patch(
        code=code, start_line=1, end_line=3, diagnostics=diags, instruction="fix"
    )
    assert edits, "expected at least one edit"
    assert "item" in patch_dsl


def test_build_patch_dsl_roundtrip():
    original_lines = ["a = 1", "b = 2", "print(a + b)"]
    edits = [
        model_patch(2, 2, "b = 3\n"),
        model_patch(3, 3, "print(a + b + 1)\n"),
    ]
    patch = build_patch_dsl(original_lines, edits)
    assert "@@ 2-2" in patch
    assert "@@ 3-3" in patch


def model_patch(start_line: int, end_line: int, replacement: str):
    # helper to create PatchEdit without importing dataclass directly
    return type("Patch", (), {"start_line": start_line, "end_line": end_line, "replacement": replacement})
