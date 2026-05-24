# /// script
# dependencies = ["requests"]
# ///
"""
Derive correct visual/color/* tags for every emoji in seed.py by analysing
Twemoji SVG files. SVGs are cached locally so re-runs are fast.

Usage (from the backend/ directory):
    uv run scripts/update_colors.py
"""
import re
import sys
import time
import colorsys
import importlib.util
from pathlib import Path
from collections import Counter

import requests

SEED_PATH = Path(__file__).parent / "seed.py"
CACHE_DIR = Path(__file__).parent / ".svg_cache"
TWEMOJI_CDN = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/svg/{}.svg"

CACHE_DIR.mkdir(exist_ok=True)


# ── Color classification ─────────────────────────────────────────────────────

def hex_to_hls(hex_color: str):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    if len(h) != 6:
        return None
    r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, ll, ss


def classify_hex(hex_color: str) -> str | None:
    result = hex_to_hls(hex_color)
    if result is None:
        return None
    h, l, s = result

    # Near-white / near-black regardless of saturation
    if l > 0.90:
        return "white"
    if l < 0.08:
        return "black"

    # Low saturation → achromatic
    if s < 0.12:
        if l > 0.78:
            return "white"
        if l < 0.22:
            return "black"
        return "brown"  # mid-gray reads as neutral/earthy in practice

    # Chromatic — map by hue
    if h >= 345 or h < 12:
        return "red"
    if h < 22:
        return "orange" if (l > 0.42 or s > 0.70) else "brown"
    if h < 48:
        return "yellow" if l > 0.48 else "brown"
    if h < 72:
        return "yellow"
    if h < 165:
        return "green" if l > 0.22 else "brown"
    if h < 258:
        return "blue"
    if h < 292:
        return "purple"
    if h < 345:
        return "pink" if l > 0.58 else "purple"
    return None


def svg_colors(svg_text: str) -> list[str]:
    """Return all distinct explicit hex fill colors found in an SVG."""
    found: set[str] = set()
    for pat in (
        re.compile(r'fill="(#[0-9a-fA-F]{3,6})"', re.I),
        re.compile(r"fill:\s*(#[0-9a-fA-F]{3,6})", re.I),
    ):
        for m in pat.finditer(svg_text):
            found.add(m.group(1).lower())
    found.discard("#ffffff")
    found.discard("#fff")
    return list(found)


def colors_to_tags(hex_colors: list[str]) -> list[str]:
    """Map a list of hex colors to visual/color/* taxonomy tags."""
    if not hex_colors:
        return []
    names = [n for h in hex_colors if (n := classify_hex(h)) is not None]
    unique = list(dict.fromkeys(names))  # deduplicated, first-seen order
    if len(unique) >= 5:
        return ["visual/color/multicolor"]
    return [f"visual/color/{c}" for c in unique]


# ── Twemoji SVG fetching ─────────────────────────────────────────────────────

def _emoji_fname(emoji: str, skip_vs: bool = True) -> str:
    parts = []
    for c in emoji:
        cp = ord(c)
        if skip_vs and cp == 0xFE0F:
            continue
        parts.append(f"{cp:x}")
    return "-".join(parts)


def fetch_svg(emoji: str) -> str | None:
    """Return SVG text for the emoji (cached on disk)."""
    for skip in (True, False):
        fname = _emoji_fname(emoji, skip_vs=skip)
        cache = CACHE_DIR / f"{fname}.svg"
        if cache.exists():
            return cache.read_text(encoding="utf-8")
        url = TWEMOJI_CDN.format(fname)
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                cache.write_text(r.text, encoding="utf-8")
                time.sleep(0.04)  # be gentle with the CDN
                return r.text
        except requests.RequestException:
            pass
    return None


# ── Seed file patching ────────────────────────────────────────────────────────

def load_documents() -> list[dict]:
    # seed.py imports elasticsearch at the top; stub it so we can load the data
    from unittest.mock import MagicMock
    sys.modules.setdefault("elasticsearch", MagicMock())
    spec = importlib.util.spec_from_file_location("_seed", SEED_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.DOCUMENTS  # type: ignore[attr-defined]


def non_color_tags(tags: list[str]) -> list[str]:
    return [t for t in tags if not t.startswith("visual/color/")]


def main() -> None:
    documents = load_documents()
    total = len(documents)
    print(f"Processing {total} emoji …")

    updated: list[dict] = []
    missing: list[str] = []

    for i, doc in enumerate(documents, 1):
        icon = doc["icon"]
        svg = fetch_svg(icon)
        if svg is None:
            # Keep original color tags rather than discarding them
            color_tags = [t for t in doc["tags"] if t.startswith("visual/color/")]
            missing.append(f"{icon} {doc['name']}")
            status = "?"
        else:
            color_tags = colors_to_tags(svg_colors(svg))
            status = "✓"

        new_tags = non_color_tags(doc["tags"]) + color_tags
        updated.append({**doc, "tags": new_tags})
        print(f"  [{i}/{total}] {status} {icon}  {doc['name']}: {color_tags}")

    if missing:
        print(f"\n⚠ No SVG found for {len(missing)} emoji:")
        for m in missing:
            print(f"    {m}")

    # Build replacement DOCUMENTS block
    lines = ["DOCUMENTS = [\n"]
    for doc in updated:
        lines.append(
            f'    {{"name": {doc["name"]!r}, "icon": {doc["icon"]!r},'
            f' "tags": {doc["tags"]!r}}},\n'
        )
    lines.append("]\n")

    seed_text = SEED_PATH.read_text(encoding="utf-8")
    replacement = "".join(lines)
    new_text = re.sub(
        r"DOCUMENTS = \[.*?\n\]\n",
        lambda _: replacement,  # lambda avoids re interpreting \u in replacement
        seed_text,
        flags=re.DOTALL,
    )
    if new_text == seed_text:
        print("\n✗ Could not locate DOCUMENTS block in seed.py — no changes written.")
        sys.exit(1)

    SEED_PATH.write_text(new_text, encoding="utf-8")
    print(f"\n✓ Wrote corrected colors for {total} emoji to {SEED_PATH}")


if __name__ == "__main__":
    main()
