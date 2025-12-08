from novaedit.languages.python.patch_apply import apply_patch_dsl


def test_apply_patch_dsl():
    code = "a = 1\nb = 2\nprint(a + b)\n"
    patch = "@@ 2-2\n- b = 2\n+ b = 3\n"
    updated = apply_patch_dsl(code, patch)
    assert "b = 3" in updated


def test_parse_rejects_invalid_header():
    code = "a = 1\n"
    bad_patch = "@@ 2-one\n- a = 1\n+ a = 2\n"
    try:
        apply_patch_dsl(code, bad_patch)
    except ValueError:
        return
    assert False, "Expected ValueError for invalid header"


def test_validate_overlapping_edits():
    code = "x = 1\ny = 2\n"
    patch = "@@ 1-2\n- x = 1\n+ x = 3\n@@ 2-2\n- y = 2\n+ y = 4\n"
    # Overlap because first edit already covers line 2
    try:
        apply_patch_dsl(code, patch)
    except ValueError:
        return
    assert False, "Expected ValueError for overlapping edits"
