#!/usr/bin/env python3
"""
Strip Obsidian wiki-link syntax from specified YAML frontmatter fields
before Hugo processes the content.

Handles:
  [[path/to/File|Display Name]]  ->  Display Name
  [[Display Name]]               ->  Display Name
"""

import re
import sys
from pathlib import Path

# Only clean these frontmatter keys (lowercase for comparison)
TARGET_FIELDS = {"tags", "characters", "series"}

WIKILINK_ALIASED = re.compile(r'\[\[[^\]]*?\|([^\]]+?)\]\]')
WIKILINK_PLAIN   = re.compile(r'\[\[([^\]]+?)\]\]')

def clean_wikilinks(value: str) -> str:
    value = WIKILINK_ALIASED.sub(r'\1', value)
    value = WIKILINK_PLAIN.sub(r'\1', value)
    return value

def process_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")

    if not text.startswith("---"):
        return False

    # Split into frontmatter and body
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False

    _, frontmatter, body = parts
    lines = frontmatter.split("\n")
    new_lines = []
    in_target_field = False

    for line in lines:
        # Detect field name (top-level YAML key)
        field_match = re.match(r'^(\w+)\s*:', line)
        if field_match:
            in_target_field = field_match.group(1).lower() in TARGET_FIELDS

        if in_target_field and "[[" in line:
            line = clean_wikilinks(line)

        new_lines.append(line)

    new_frontmatter = "\n".join(new_lines)
    path.write_text(f"---{new_frontmatter}---{body}", encoding="utf-8")
    return True

if __name__ == "__main__":
    content_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("content")
    count = sum(process_file(p) for p in content_dir.rglob("*.md"))
    print(f"Sanitised {count} files in {content_dir}")
