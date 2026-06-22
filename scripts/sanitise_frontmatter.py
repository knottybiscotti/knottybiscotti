#!/usr/bin/env python3
"""
Strip Obsidian wiki-link syntax from specified YAML frontmatter fields,
and derive aggregating "umbrella" tags, before Hugo processes the content.

Wiki-link handling:
  [[path/to/File|Display Name]]  ->  Display Name
  [[Display Name]]               ->  Display Name

Umbrella derivation:
  After the `tags` list has been cleaned to bare slugs, any tag implying a
  broader umbrella (e.g. an orientation/identity tag implying `queer`) is
  added to the build's tag list. The rule lives in umbrella_tags.py so it is
  shared with the AO3 CSV generator rather than encoded twice.

This runs on the ephemeral CI content, so derived tags become first-class
taxonomy terms in the build while the authored .md files stay untouched.
"""

import re
import sys
from pathlib import Path

from umbrella_tags import derive_umbrella_tags

# Only clean these frontmatter keys (lowercase for comparison)
TARGET_FIELDS = {"tags", "characters", "series"}

WIKILINK_ALIASED = re.compile(r'\[\[[^\]]*?\|([^\]]+?)\]\]')
WIKILINK_PLAIN   = re.compile(r'\[\[([^\]]+?)\]\]')

# A block-sequence item line, e.g. "  - sapphic"
ITEM_RE = re.compile(r'^(\s*)-\s+(.*\S)\s*$')


def clean_wikilinks(value: str) -> str:
    value = WIKILINK_ALIASED.sub(r'\1', value)
    value = WIKILINK_PLAIN.sub(r'\1', value)
    return value


def _strip_quotes(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


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

    in_target_field = False   # any wiki-link-cleaned field (tags/characters/series)
    in_tags_field = False     # specifically the tags: block
    tag_values = []           # cleaned slugs collected from the current tags block
    tags_indent = "  "        # item indentation, detected from the block
    last_item_idx = None      # index in new_lines of the most recent tags item

    def flush_tags():
        """Insert any derived umbrella tags right after the last tags item."""
        nonlocal last_item_idx
        if last_item_idx is not None:
            derived = derive_umbrella_tags(tag_values)
            extra = sorted(derived - set(tag_values), key=str.lower)
            for offset, tag in enumerate(extra, start=1):
                new_lines.insert(last_item_idx + offset, f"{tags_indent}- {tag}")
        last_item_idx = None

    for line in lines:
        field_match = re.match(r'^(\w+)\s*:', line)
        if field_match:
            # Leaving the previous field; finalize the tags block if that's
            # what we were in (must happen before this new key is appended).
            if in_tags_field:
                flush_tags()
            key = field_match.group(1).lower()
            in_target_field = key in TARGET_FIELDS
            in_tags_field = key == "tags"
            if in_tags_field:
                tag_values = []
                tags_indent = "  "

        if in_target_field and "[[" in line:
            line = clean_wikilinks(line)

        new_lines.append(line)

        # Collect tag slugs from the (already wiki-link-cleaned) item line.
        if in_tags_field:
            m = ITEM_RE.match(line)
            if m:
                tags_indent = m.group(1)
                tag_values.append(_strip_quotes(m.group(2).strip()))
                last_item_idx = len(new_lines) - 1

    # tags: may be the final frontmatter field — flush at end of block too.
    if in_tags_field:
        flush_tags()

    new_frontmatter = "\n".join(new_lines)
    path.write_text(f"---{new_frontmatter}---{body}", encoding="utf-8")
    return True


if __name__ == "__main__":
    content_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("content")
    count = sum(process_file(p) for p in content_dir.rglob("*.md"))
    print(f"Sanitised {count} files in {content_dir}")
