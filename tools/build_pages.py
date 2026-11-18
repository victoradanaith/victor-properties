"""Build the GitHub Pages copy of the app.

Usage: python3 tools/build_pages.py <export_dir>

<export_dir> holds an ArtifactData export of the app database:
  <export_dir>/listings/*.json and <export_dir>/settings/main.json

Writes:
  index.html          the app page wrapped as a full HTML document
  data/snapshot.json  a read-only public copy of the listings

Listings imported from the private Google Sheet (ids starting "sheet-"),
contact details (names, phone numbers) and the main property (its pin and
details) are left out of the public copy.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHONE = re.compile(r"\b0\d{1,2}[- ]?\d{3}[- ]?\d{3,4}\b")
SKIP_FIELDS = {"contact"}
PUBLIC_SUBJECT = {"name": "BTS ราชเทวี", "address": "", "lat": 13.7521, "lng": 100.5316,
                  "landSqw": None, "usableSqm": None, "floors": None, "units": None, "notes": ""}


def load(path):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return doc.get("data", doc), doc.get("id", Path(path).stem)


def clean(listing):
    out = {k: v for k, v in listing.items() if k not in SKIP_FIELDS}
    for key in ("notes", "location", "title"):
        if isinstance(out.get(key), str):
            text = PHONE.sub("[ตัดเบอร์โทร]", out[key])
            # Drop phrases that hint where the main property is (e.g. "same soi as the main property").
            out[key] = " ".join(w for w in text.split() if "ทรัพย์หลัก" not in w)
    return out


def main(export_dir):
    export = Path(export_dir)
    listings = []
    for f in sorted((export / "listings").glob("*.json")):
        data, doc_id = load(f)
        if doc_id.startswith("sheet-"):
            continue
        listings.append({"id": doc_id, **clean(data)})

    settings = {}
    settings_file = export / "settings" / "main.json"
    if settings_file.exists():
        settings, _ = load(settings_file)
    # The public copy never carries the main property: distances use BTS Ratchathewi instead.
    settings["subject"] = PUBLIC_SUBJECT

    (ROOT / "data").mkdir(exist_ok=True)
    snapshot = {"exportedAt": date.today().isoformat(), "public": True, "settings": settings, "listings": listings}
    (ROOT / "data" / "snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    body = (ROOT / "ratchathewi-shophouse.html").read_text(encoding="utf-8")
    page = (
        "<!doctype html><html lang=\"th\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">"
        "<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);"
        "padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font:14px system-ui,sans-serif}"
        "img{max-width:100%}[hidden]{display:none!important}</style></head><body>\n"
        + body
        + "\n</body></html>\n"
    )
    (ROOT / "index.html").write_text(page, encoding="utf-8")
    print(f"index.html + data/snapshot.json written: {len(listings)} listings")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
