#!/usr/bin/env python3
"""Self-contained validation for the edit-hwpx-docs skill."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


MAX_SKILL_NAME_LENGTH = 64
EXPECTED_FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/hwpx-format.md",
    "scripts/hwpx_tool.py",
    "scripts/validate_skill.py",
)
ALLOWED_FRONTMATTER_KEYS = {"name", "description"}
NAME_RE = re.compile(r"^[a-z0-9-]+$")


class ValidationError(RuntimeError):
    pass


def as_posix(path: Path) -> str:
    return path.as_posix()


def strip_inline_comment(value: str) -> str:
    if "#" not in value:
        return value
    quote: Optional[str] = None
    escaped = False
    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in ("'", '"'):
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        elif char == "#" and quote is None:
            return value[:index].rstrip()
    return value


def parse_scalar(value: str) -> str:
    value = strip_inline_comment(value.strip())
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def parse_simple_yaml_mapping(text: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            raise ValidationError(f"unsupported nested YAML at line {lineno}: {line}")
        if ":" not in line:
            raise ValidationError(f"expected 'key: value' at line {lineno}: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            raise ValidationError(f"empty YAML key at line {lineno}")
        result[key] = parse_scalar(value)
    return result


def extract_frontmatter(content: str) -> Tuple[Dict[str, str], str]:
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines or lines[0] != "---":
        raise ValidationError("SKILL.md must start with YAML frontmatter")
    try:
        closing_index = lines[1:].index("---") + 1
    except ValueError as exc:
        raise ValidationError("SKILL.md frontmatter is not closed with ---") from exc
    frontmatter = "\n".join(lines[1:closing_index])
    body = "\n".join(lines[closing_index + 1 :])
    return parse_simple_yaml_mapping(frontmatter), body


def validate_frontmatter(skill_path: Path, errors: List[str]) -> Optional[str]:
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        errors.append("SKILL.md is missing")
        return None
    try:
        frontmatter, body = extract_frontmatter(skill_md.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, ValidationError) as exc:
        errors.append(f"SKILL.md frontmatter error: {exc}")
        return None

    unexpected = sorted(set(frontmatter) - ALLOWED_FRONTMATTER_KEYS)
    if unexpected:
        errors.append(f"SKILL.md has unexpected frontmatter keys: {', '.join(unexpected)}")

    name = frontmatter.get("name", "").strip()
    description = frontmatter.get("description", "").strip()
    if not name:
        errors.append("SKILL.md frontmatter is missing name")
    elif not NAME_RE.fullmatch(name):
        errors.append("SKILL.md name must use lowercase letters, digits, and hyphens only")
    elif name.startswith("-") or name.endswith("-") or "--" in name:
        errors.append("SKILL.md name cannot start/end with hyphen or contain consecutive hyphens")
    elif len(name) > MAX_SKILL_NAME_LENGTH:
        errors.append(f"SKILL.md name is longer than {MAX_SKILL_NAME_LENGTH} characters")

    if not description:
        errors.append("SKILL.md frontmatter is missing description")
    elif len(description) > 1024:
        errors.append("SKILL.md description is longer than 1024 characters")
    elif "<" in description or ">" in description:
        errors.append("SKILL.md description must not contain angle brackets")

    if not body.strip():
        errors.append("SKILL.md body is empty")
    return name or None


def parse_openai_interface(text: str) -> Dict[str, str]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    values: Dict[str, str] = {}
    in_interface = False
    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line == "interface:":
            in_interface = True
            continue
        if not line.startswith(" "):
            in_interface = False
        if not in_interface:
            continue
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        values[key.strip()] = parse_scalar(value)
    return values


def validate_openai_yaml(skill_path: Path, skill_name: Optional[str], errors: List[str]) -> None:
    path = skill_path / "agents" / "openai.yaml"
    if not path.exists():
        errors.append("agents/openai.yaml is missing")
        return
    try:
        values = parse_openai_interface(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        errors.append(f"agents/openai.yaml is not valid UTF-8: {exc}")
        return

    for key in ("display_name", "short_description", "default_prompt"):
        if not values.get(key):
            errors.append(f"agents/openai.yaml is missing interface.{key}")
    if skill_name and values.get("default_prompt") and f"${skill_name}" not in values["default_prompt"]:
        errors.append("agents/openai.yaml default_prompt must mention the skill as $skill-name")


def imported_top_level_modules(path: Path) -> Iterable[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".", 1)[0]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".", 1)[0]


def validate_python_imports(skill_path: Path, errors: List[str]) -> None:
    stdlib = getattr(sys, "stdlib_module_names", set())
    local_modules = {path.stem for path in (skill_path / "scripts").glob("*.py")}
    allowed_external = set()

    for path in (skill_path / "scripts").glob("*.py"):
        try:
            imports = sorted(set(imported_top_level_modules(path)))
        except SyntaxError as exc:
            errors.append(f"{as_posix(path.relative_to(skill_path))} has syntax error: {exc}")
            continue
        for module in imports:
            if module in local_modules or module in stdlib or module in allowed_external:
                continue
            errors.append(
                f"{as_posix(path.relative_to(skill_path))} imports non-stdlib module '{module}'"
            )


def validate_expected_files(skill_path: Path, errors: List[str]) -> None:
    for relative in EXPECTED_FILES:
        if not (skill_path / relative).exists():
            errors.append(f"expected file is missing: {relative}")
    if (skill_path / "scripts" / "ensure_pyyaml.py").exists():
        errors.append("scripts/ensure_pyyaml.py should not exist in the self-contained skill")


def validate_skill(skill_path: Path) -> Dict[str, object]:
    errors: List[str] = []
    if not skill_path.exists():
        errors.append(f"skill path does not exist: {skill_path}")
    elif not skill_path.is_dir():
        errors.append(f"skill path is not a directory: {skill_path}")
    if errors:
        return {"ok": False, "path": str(skill_path), "errors": errors}

    validate_expected_files(skill_path, errors)
    skill_name = validate_frontmatter(skill_path, errors)
    validate_openai_yaml(skill_path, skill_name, errors)
    validate_python_imports(skill_path, errors)
    return {
        "ok": not errors,
        "path": str(skill_path),
        "skill_name": skill_name,
        "self_contained": not errors,
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate this skill without external packages.")
    parser.add_argument(
        "skill_path",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1]),
        help="Skill directory. Defaults to the parent skill folder.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_skill(Path(args.skill_path).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
