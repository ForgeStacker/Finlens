#!/usr/bin/env python3
"""Create distributable offline zip from frontend/dist."""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = ROOT / "frontend" / "dist-offline"
OUT_DIR = ROOT / "release"
ZIP_BASENAME = OUT_DIR / "autovyn-static"


def inline_assets_for_file_mode(index_path: Path) -> None:
    html = index_path.read_text(encoding="utf-8")

    css_match = re.search(r'<link[^>]*href="([^"]+\.css)"[^>]*>', html)
    if css_match:
        css_href = css_match.group(1)
        css_path = (index_path.parent / css_href).resolve()
        css_content = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
        html = html.replace(css_match.group(0), f"<style>\n{css_content}\n</style>")

    js_match = re.search(r'<script[^>]*src="([^"]+\.js)"[^>]*></script>', html)
    if js_match:
        js_src = js_match.group(1)
        js_path = (index_path.parent / js_src).resolve()
        js_content = js_path.read_text(encoding="utf-8") if js_path.exists() else ""
        # Remove original script from <head> and inject before </body> so #root always exists.
        html = html.replace(js_match.group(0), "")
        inline_module = f"<script type=\"module\">\n{js_content}\n</script>"
        if "</body>" in html:
            html = html.replace("</body>", f"{inline_module}\n  </body>")
        else:
            html = f"{html}\n{inline_module}\n"

    index_path.write_text(html, encoding="utf-8")


def main() -> int:
    if not DIST_DIR.exists() or not (DIST_DIR / "index.html").exists():
        print(f"Build output not found at {DIST_DIR}. Run offline build first.")
        return 1

    inline_assets_for_file_mode(DIST_DIR / "index.html")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    target_zip = shutil.make_archive(str(ZIP_BASENAME), "zip", root_dir=str(DIST_DIR))

    print(f"Offline package created: {target_zip}")
    print(f"Created at: {datetime.now().isoformat(timespec='seconds')}")
    print("Share the zip, unzip it, then open index.html locally.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
