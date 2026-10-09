"""Seed and reconcile task references with the user-provided refs catalog.

This tool checks file identity and bibliographic matches. It does not verify claims.
"""
import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from orchestration.protocol import safe_path

FIELDS = ("source_id", "title", "authors", "year", "venue", "doi", "url",
          "accessed_at", "access_level", "verification_status", "notes")
CATALOG = ROOT / "refs/catalog.csv"
HASHES = ROOT / "refs/file_hashes.json"


def read_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError(f"missing reference fields in {path}")
        rows = list(reader)
    if any(not row["title"].strip() for row in rows):
        raise ValueError("reference title is required")
    return rows


def load_catalog(topic):
    rows = [row for row in read_csv(CATALOG) if row["topic"] == topic]
    if not rows or len({row["source_id"] for row in rows}) != len(rows):
        raise ValueError("missing or duplicated local source IDs")
    return rows


def verify_archive():
    expected = json.loads(HASHES.read_text(encoding="utf-8"))
    for relative, digest in expected.items():
        path = safe_path(ROOT, relative)
        if not path.is_file():
            raise ValueError("missing archived source: " + relative)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError("archived source hash changed: " + relative)
    return expected


def verify_local_files(rows):
    expected = verify_archive()
    for row in rows:
        for field in ("local_file", "local_text"):
            relative = row.get(field, "")
            if not relative:
                continue
            path = safe_path(ROOT, relative)
            if relative not in expected or not path.is_file():
                raise ValueError("untracked or missing local source: " + relative)


def normalize_doi(value):
    value = value.strip().lower()
    value = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", value)
    return value.rstrip(" .,/;")


def normalize_title(value):
    value = unicodedata.normalize("NFKC", value).casefold()
    return "".join(char for char in value if char.isalnum())


def normalize_url(value):
    if not value.strip():
        return ""
    parts = urlsplit(value.strip())
    if parts.netloc.lower() in ("doi.org", "dx.doi.org"):
        return "doi:" + normalize_doi(parts.path.lstrip("/"))
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(),
                       parts.path.rstrip("/"), "", ""))


def same_source(incoming, existing):
    a, b = normalize_doi(incoming.get("doi", "")), normalize_doi(existing.get("doi", ""))
    if a and b:
        return a == b
    ua, ub = normalize_url(incoming.get("url", "")), normalize_url(existing.get("url", ""))
    if ua and ub and ua == ub:
        return True
    ta, tb = normalize_title(incoming["title"]), normalize_title(existing["title"])
    ya, yb = incoming.get("year", "").strip(), existing.get("year", "").strip()
    return bool(ta and ta == tb and ya and yb and ya == yb)


def metadata_differences(incoming, existing):
    different = []
    for field in ("title", "authors", "year", "doi"):
        a, b = incoming.get(field, "").strip(), existing.get(field, "").strip()
        if not a or not b:
            continue
        if field == "doi":
            unequal = normalize_doi(a) != normalize_doi(b)
        elif field == "title":
            unequal = normalize_title(a) != normalize_title(b)
        else:
            unequal = a.casefold() != b.casefold()
        if unequal:
            different.append(field)
    return different


def public_row(row):
    clean = {field: row.get(field, "").strip() for field in FIELDS}
    if row.get("local_file"):
        detail = "local_file=" + row["local_file"]
        clean["notes"] = (clean["notes"] + "; " + detail).strip("; ")
    return clean


def external_id(topic, row):
    key = normalize_doi(row.get("doi", "")) or normalize_url(row.get("url", ""))
    key = key or normalize_title(row["title"]) + row.get("year", "")
    return f"{topic}X" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:10].upper()


def reconcile(topic, incoming_rows, catalog_rows=None):
    merged = [public_row(row) for row in (catalog_rows if catalog_rows is not None else load_catalog(topic))]
    events = []
    for incoming in incoming_rows:
        candidates = [row for row in merged if same_source(incoming, row)]
        incoming_id = incoming.get("source_id", "").strip()
        if len(candidates) > 1:
            raise ValueError("ambiguous match for " + incoming["title"])
        if candidates:
            kept = candidates[0]
            differing = metadata_differences(incoming, kept)
            events.append(("metadata_conflict" if differing else "matched", incoming_id,
                           kept["source_id"], ",".join(differing)))
            continue
        new = public_row(incoming)
        new["source_id"] = external_id(topic, new)
        if any(row["source_id"] == new["source_id"] for row in merged):
            raise ValueError("generated source ID collision")
        if new["verification_status"] == "verified":
            new["verification_status"] = "partially_verified"
            new["notes"] = (new["notes"] + "; incoming verification needs independent review").strip("; ")
        merged.append(new)
        title_collisions = [row["source_id"] for row in merged[:-1]
                            if normalize_title(row["title"]) == normalize_title(new["title"])]
        status = "possible_title_conflict" if title_collisions else "new_unreviewed"
        events.append((status, incoming_id, new["source_id"], ",".join(title_collisions)))
    return merged, events


def task_output(relative):
    path = safe_path(ROOT, relative)
    parts = path.relative_to(ROOT).parts
    if len(parts) < 4 or parts[:2] not in (("competition", "runs"), ("knowledge", "runs")):
        raise ValueError("output must be inside a task run directory")
    if not path.parent.is_dir() or path.exists():
        raise ValueError("output parent must exist and output must be new")
    return path


def write_csv(path, rows):
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    seed = sub.add_parser("seed", help="copy local source metadata into a new task references.csv")
    seed.add_argument("--topic", choices=("C", "D"), required=True)
    seed.add_argument("--out", required=True)
    merge = sub.add_parser("merge", help="reconcile later Codex references without changing local refs")
    merge.add_argument("--topic", choices=("C", "D"), required=True)
    merge.add_argument("--incoming", required=True)
    merge.add_argument("--out", required=True)
    merge.add_argument("--report", required=True)
    args = parser.parse_args()
    try:
        catalog = load_catalog(args.topic)
        verify_local_files(catalog)
        output = task_output(args.out)
        if args.command == "seed":
            rows = [public_row(row) for row in catalog]
            write_csv(output, rows)
            summary = {"topic":args.topic,"seeded":len(rows),"output":args.out,
                       "scope":"local file and bibliographic inventory; claims not verified"}
        else:
            incoming = safe_path(ROOT, args.incoming)
            if not incoming.is_file() or incoming == output:
                raise ValueError("incoming references.csv is missing or equals output")
            report = task_output(args.report)
            if report == output:
                raise ValueError("report and output must differ")
            rows, events = reconcile(args.topic, read_csv(incoming), catalog)
            write_csv(output, rows)
            lines = ["# Reference reconciliation", "", "This is a metadata match, not claim verification.", "",
                     "| status | incoming ID | canonical ID | differing metadata |",
                     "|---|---|---|---|"]
            lines.extend("| " + " | ".join(event) + " |" for event in events)
            report.write_text("\n".join(lines) + "\n", encoding="utf-8")
            summary = {"topic":args.topic,"local":len(catalog),"incoming":len(events),
                       "merged":len(rows),"output":args.out,"report":args.report}
        print(json.dumps(summary, ensure_ascii=True, indent=2))
        return 0
    except (ValueError, OSError, KeyError, UnicodeError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
