#!/usr/bin/env python3
"""Generate API reference docs from FastAPI OpenAPI schema."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> None:
    from backend.main import app

    schema = app.openapi()
    out_path = Path("docs/api_reference.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(schema, indent=2))
    print(f"✅ OpenAPI schema written to {out_path}")

    # Generate markdown reference
    md_lines = ["# API Reference\n", f"**Version:** {schema.get('info', {}).get('version', '1.0')}\n\n"]
    for path, methods in schema.get("paths", {}).items():
        for method, spec in methods.items():
            summary = spec.get("summary", "")
            description = spec.get("description", "")
            md_lines.append(f"## `{method.upper()} {path}`\n")
            if summary:
                md_lines.append(f"**{summary}**\n\n")
            if description:
                md_lines.append(f"{description}\n\n")
            tags = spec.get("tags", [])
            if tags:
                md_lines.append(f"*Tags: {', '.join(tags)}*\n\n")
            md_lines.append("---\n\n")

    md_path = Path("docs/api_reference.md")
    md_path.write_text("".join(md_lines))
    print(f"✅ Markdown API reference written to {md_path}")


if __name__ == "__main__":
    main()
