from novaedit.languages.python.patch_apply import apply_patch_dsl


def test_apply_patch_dsl():
    code = "a = 1\nb = 2\nprint(a + b)\n"
    patch = "@@ 2-2\n- b = 2\n+ b = 3\n"
    updated = apply_patch_dsl(code, patch)
    assert "b = 3" in updated
