"""Reject static cross-domain imports that bypass public interfaces."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "backend" / "modules"


def violations(source: str, module_path: str) -> list[str]:
    """module_path is a dotted module name, e.g. modules.billing.services."""
    owner = module_path.split(".")[1]
    failures = []
    for node in ast.walk(ast.parse(source)):
        targets = []
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parent = module_path.split(".")[: -node.level]
                base = ".".join(parent + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            targets = [base] if base else []
            # Handles `from modules import billing` and `from modules.billing import models`.
            if base == "modules" or (
                base.startswith("modules.") and len(base.split(".")) == 2
            ):
                targets = [f"{base}.{alias.name}" for alias in node.names]
        for target in targets:
            parts = target.split(".")
            if parts[0] != "modules" or len(parts) < 2 or parts[1] == owner:
                continue
            if len(parts) == 3 and parts[2] == "interfaces":
                continue
            failures.append(
                f"line {node.lineno}: {owner} imports private boundary {target}"
            )
    return failures


def main() -> int:
    errors = []
    for path in MODULES.rglob("*.py"):
        relative = path.relative_to(MODULES)
        if len(relative.parts) < 2 or "migrations" in relative.parts:
            continue
        dotted = ".".join(path.relative_to(ROOT / "backend").with_suffix("").parts)
        for error in violations(path.read_text(), dotted):
            errors.append(f"{path.relative_to(ROOT)}:{error}")
    if errors:
        print("\n".join(errors))
        return 1
    print("Module boundaries passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
