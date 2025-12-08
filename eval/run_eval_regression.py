from __future__ import annotations

from novaedit.model import NovaEditModel


REGRESSION_CASES = [
    {
        "name": "missing_import",
        "code": "def area(r):\n    return pi * r * r\n",
        "diagnostics": ["NameError: name 'pi' is not defined"],
    },
    {
        "name": "typo_variable",
        "code": "total = 0\nfor i in range(3):\n    total += i\nprint(totl)\n",
        "diagnostics": ["NameError: name 'totl' is not defined"],
    },
]


def main() -> None:
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
        print(f"[{case['name']}]")
        print(patch_dsl.strip())
        print(updated)
        print("-" * 20)


if __name__ == "__main__":
    main()
