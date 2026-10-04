#!/usr/bin/env python3
"""Split NIST OSCAL content (usnistgov/oscal-content) into per-control text files.

One file per control (direct child of a catalog group), carrying the control
id, title, family, statement text, parameters, and all enhancement/child
controls. Baselines (OSCAL profiles) become one file per baseline listing the
selected control ids. Stdlib only. Regeneration:

    git clone --depth 1 https://github.com/usnistgov/oscal-content
    python3 split_oscal.py --oscal-content ./oscal-content --out .

Shape rule enforced: no emitted file may exceed 150 KB.
"""
import argparse
import json
import re
import sys
from pathlib import Path

MAX_BYTES = 150 * 1024

# (output dir, path under oscal-content, id rule)
CATALOGS = [
    ("sp800-53r5", "nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json", "upper"),
    ("sp800-171r3", "nist.gov/SP800-171/rev3/json/NIST_SP800-171_rev3_catalog.json", "sp171"),
    ("sp800-172r3", "nist.gov/SP800-172/rev3/json/NIST_SP800-172_rev3_catalog.json", "sp172"),
    ("sp800-218", "nist.gov/SP800-218/ver1/json/NIST_SP800-218_ver1_catalog.json", "raw"),
    ("csf-2-0", "nist.gov/CSF/v2.0/json/NIST_CSF_v2.0_catalog.json", "raw"),
]

# (output dir, path under oscal-content, baseline name)
BASELINES = [
    ("sp800-53r5", "nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_%s-baseline_profile.json" % n, n)
    for n in ("LOW", "MODERATE", "HIGH", "PRIVACY")
]

RENDER_PART_NAMES = {"statement", "item", "guidance", "example", "overview"}
INSERT_RE = re.compile(r"\{\{\s*insert:\s*param\s*,\s*([^}]+?)\s*\}\}")


def control_filename(ctl_id, rule):
    """Map an OSCAL control id to a human-readable file stem."""
    if rule == "upper":  # ac-2 -> AC-2
        return ctl_id.upper()
    if rule == "sp171":  # SP_800_171_03.01.01 -> 3.1.1
        body = ctl_id[len("SP_800_171_"):]
    elif rule == "sp172":  # SP_800_172_3_0_0_03.01.01E -> 3.1.1E
        body = ctl_id[len("SP_800_172_3_0_0_"):]
    else:
        return ctl_id
    return ".".join(s.lstrip("0") or "0" for s in body.split("."))


def pretty_enhancement_id(ctl_id):
    """ac-2.1 -> AC-2(1); ids without the dotted-enhancement shape pass through."""
    m = re.match(r"^([a-z]+-\d+)\.(\d+)$", ctl_id)
    return "%s(%s)" % (m.group(1).upper(), m.group(2)) if m else ctl_id.upper()


def param_inline(pid, params):
    """Render {{ insert: param, id }} as a bracketed selection/assignment."""
    p = params.get(pid)
    if p is None:
        return "[param: %s]" % pid
    if "select" in p:
        how = p["select"].get("how-many", "")
        choices = "; ".join(str(c) for c in p["select"].get("choice", []))
        return "[Selection (%s): %s]" % (how, choices)
    if p.get("label"):
        return "[%s]" % p["label"]
    return "[param: %s]" % pid


def substitute(prose, params):
    return INSERT_RE.sub(lambda m: param_inline(m.group(1), params), prose)


def param_map(ctl):
    return {p["id"]: p for p in ctl.get("params", [])}


def render_parts(parts, params, depth, out):
    for part in parts or []:
        name = part.get("name", "")
        if name not in RENDER_PART_NAMES:
            continue  # assessment-objective/-method/-objects content is dropped
        label = ""
        for pr in part.get("props", []):
            if pr.get("name") == "label":
                label = pr.get("value", "")
                break
        indent = "  " * depth
        if name in ("guidance", "example") and depth == 0 and part.get("prose"):
            if out and out[-1] != "":
                out.append("")
            out.append("%s:" % name.capitalize())
        if part.get("prose"):
            prefix = label + " " if label else ("- " if name == "item" else "")
            for line in substitute(part["prose"], params).splitlines() or [""]:
                out.append(indent + prefix + line if line else indent)
                prefix = ""  # label applies to first line only
        elif label:
            out.append(indent + label)
        render_parts(part.get("parts"), params, depth + 1, out)


def render_params_section(ctl, out):
    params = ctl.get("params", [])
    if not params:
        return
    out.append("")
    out.append("Parameters:")
    for p in params:
        bits = [p["id"]]
        if p.get("label"):
            bits.append('label: "%s"' % p["label"])
        if "select" in p:
            how = p["select"].get("how-many", "")
            choices = "; ".join(str(c) for c in p["select"].get("choice", []))
            bits.append("selection (%s): %s" % (how, choices))
        out.append("- " + " | ".join(bits))
        for g in p.get("guidelines", []):
            if g.get("prose"):
                out.append("  guideline: " + substitute(g["prose"], param_map(ctl)))


def render_references(ctl, backmatter, out):
    refs = []
    for link in ctl.get("links", []):
        href = link.get("href", "")
        if href.startswith("#"):
            res = backmatter.get(href[1:])
            if res:
                cite = res.get("citation", {}).get("text") or res.get("title") or ""
                cite = " ".join(cite.split())
                if cite:
                    refs.append(cite)
    if refs:
        out.append("")
        out.append("References:")
        for r in refs:
            out.append("- " + r)


def render_control(ctl, family, backmatter, out, child=False):
    params = param_map(ctl)
    cid = ctl["id"]
    if child:
        pretty = pretty_enhancement_id(cid)
        out.append("")
        out.append("=" * 72)
        if pretty != cid.upper():
            out.append("Enhancement %s (%s) - %s" % (pretty, cid, ctl.get("title", "")))
        else:
            out.append("Child control %s - %s" % (cid, ctl.get("title", "")))
    has_statement = any(p.get("name") == "statement" for p in ctl.get("parts", []))
    body = []
    render_parts(ctl.get("parts"), params, 0, body)
    if has_statement:
        out.append("")
        out.append("Statement:")
    out.extend(body)
    render_params_section(ctl, out)
    render_references(ctl, backmatter, out)
    for ch in ctl.get("controls", []):
        render_control(ch, family, backmatter, out, child=True)


def split_catalog(src, out_dir, rule):
    doc = json.loads(Path(src).read_text(encoding="utf-8"))
    cat = doc["catalog"]
    backmatter = {r["uuid"]: r for r in cat.get("back-matter", {}).get("resources", [])}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = []
    for grp in cat.get("groups", []):
        family = "%s (%s)" % (grp.get("title", ""), grp.get("id", ""))
        overview = ""
        for part in grp.get("parts", []):
            if part.get("prose"):
                overview = " ".join(part["prose"].split())
                break
        for ctl in grp.get("controls", []):
            out = []
            out.append("id: %s" % ctl["id"])
            out.append("title: %s" % ctl.get("title", ""))
            out.append("family: %s" % family)
            if ctl.get("class"):
                out.append("class: %s" % ctl["class"])
            if overview:
                out.append("family-overview: %s" % overview)
            render_control(ctl, family, backmatter, out)
            stem = control_filename(ctl["id"], rule)
            path = out_dir / ("%s.txt" % stem)
            path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
            counts.append(path)
    return counts


def write_baseline(src, out_dir, name):
    doc = json.loads(Path(src).read_text(encoding="utf-8"))
    ids = []
    for imp in doc["profile"].get("imports", []):
        for inc in imp.get("include-controls", []):
            ids.extend(inc.get("with-ids", []))
    ids = sorted(set(ids))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "SP 800-53 Rev. 5 %s baseline - selected control ids" % name,
        "source: %s" % Path(src).name,
        "count: %d" % len(ids),
        "",
    ]
    lines += [i.upper() for i in ids]
    path = out_dir / ("baseline-%s.txt" % name)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--oscal-content", required=True, help="path to a clone of usnistgov/oscal-content")
    ap.add_argument("--out", required=True, help="mirror root to write control files into")
    args = ap.parse_args()
    root = Path(args.oscal_content)
    out = Path(args.out)
    total, biggest, big_file = 0, 0, ""
    for out_dir, rel, rule in CATALOGS:
        files = split_catalog(root / rel, out / out_dir, rule)
        mx = max((f.stat().st_size for f in files), default=0)
        print("%-12s %4d control files, largest %8d B (%s)"
              % (out_dir, len(files), mx, max(files, key=lambda f: f.stat().st_size).name if files else "-"))
        total += len(files)
        if mx > biggest:
            biggest, big_file = mx, (out_dir + "/" + max(files, key=lambda f: f.stat().st_size).name if files else "")
    for out_dir, rel, name in BASELINES:
        p = write_baseline(root / rel, out / out_dir, name)
        print("%-12s baseline-%s.txt %d B, %d ids" % (out_dir, name, p.stat().st_size, sum(1 for l in p.read_text().splitlines() if l and not l.startswith(("SP 8", "source", "count")))))
        total += 1
    print("TOTAL files written: %d" % total)
    # shape rule
    offenders = [p for p in out.rglob("*.txt") if p.stat().st_size > MAX_BYTES]
    if offenders:
        for p in offenders:
            print("OVER 150KB: %s (%d B)" % (p, p.stat().st_size), file=sys.stderr)
        sys.exit(1)
    print("largest file overall: %s at %d B" % (big_file, biggest))
    print("shape rule OK: no file over %d B" % MAX_BYTES)


if __name__ == "__main__":
    main()
