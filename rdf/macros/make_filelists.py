#!/usr/bin/env python3
"""Raw-NanoAOD file lists for the fused (direct) wzzAnalysis production. Runs in rdf/macros/
on CMS Connect (dasgoclient + VOMS proxy). No skims: every dataset is the raw DAS NANOAOD(SIM).

    python3 make_filelists.py --config wzzAnalysis_input_condor_jobs.cfg \\
        --redirector root://cmsxrootd.fnal.gov/ [--out direct/filelists] [--dry-run]

MC:   <out>/<id>.txt     from SwitchSample(id)[0]: "<primary>+<processed>+NANOAODSIM"
Data: <out>/data_<type>_<YYYY>.txt from getDATAlist's directory names
      "<PD>+<era>-<processing>+NANOAOD" -> /<PD>/<era>-<processing>/NANOAOD
(the directory naming of the skims is reused only as a dataset registry).
"""
import argparse
import os
import re
import subprocess
import sys

# "<sample> <year> [+<second year>] [no]" (submit_wzz.ROW; the second year reads the same files)
ROW = re.compile(r"^\s*(\d+)\s+(\d+)(?:\s+\+\d+)?\s*(no)?\s*$")


def das_name(dirname, tier):
    base = os.path.basename(dirname.rstrip("/"))
    parts = base.split("+")
    if len(parts) != 3:
        raise ValueError("unexpected dataset directory: " + base)
    return "/{0}/{1}/{2}".format(parts[0], parts[1], parts[2] if parts[2] else tier)


def data_datasets(utils_path):
    """{(year, type): [DAS names]} from getDATAlist."""
    src = open(utils_path).read()
    body = src.split("def getDATAlist", 1)[1].split("\ndef ", 1)[0]
    out, key = {}, None
    for line in body.splitlines():
        m = re.search(r"year == (\d{4}) and type == (\d+)", line)
        if m:
            key = (int(m.group(1)), int(m.group(2)))
            continue
        for d in re.findall(r'findDIR\("\{0\}/([^"]+)"', line):
            if key is not None:
                out.setdefault(key, []).append(das_name(d, "NANOAOD"))
    return out


def files_of(das):
    r = subprocess.run(["dasgoclient", "-query", "file dataset={0}".format(das)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("dasgoclient failed for {0}: {1}".format(das, r.stderr.strip()[:300]))
    return [x.strip() for x in r.stdout.splitlines() if x.strip().startswith("/store")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="wzzAnalysis_input_condor_jobs.cfg")
    ap.add_argument("--redirector", default="root://cmsxrootd.fnal.gov/")
    ap.add_argument("--out", default="direct/filelists")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sys.path.insert(0, os.getcwd())
    from utilsAna import SwitchSample
    rows = []
    for line in open(args.config):
        m = ROW.match(line)
        if m and not m.group(3):
            rows.append((int(m.group(1)), int(m.group(2))))
    data = data_datasets("utilsAna.py")
    os.makedirs(args.out, exist_ok=True)
    jobs = {}
    for sid, year in rows:
        if sid < 1000:
            jobs.setdefault(os.path.join(args.out, "{0}.txt".format(sid)), [das_name(SwitchSample(sid, "3l")[0], "NANOAODSIM")])
        else:
            key = (year // 10 if year > 10000 else year, sid)
            if key not in data:
                print("WARNING: no getDATAlist entry for {0}".format(key))
                continue
            jobs.setdefault(os.path.join(args.out, "data_{0}_{1}.txt".format(sid, key[0])), data[key])
    nfiles = 0
    for path, datasets in sorted(jobs.items()):
        lines = []
        for das in datasets:
            if args.dry_run:
                print("{0}: {1}".format(path, das))
                continue
            fl = files_of(das)
            if not fl:
                print("WARNING: no files for {0}".format(das))
            lines += ["# DAS: {0} ({1} files)".format(das, len(fl))] + [args.redirector + f for f in fl]
            nfiles += len(fl)
        if not args.dry_run:
            open(path, "w").write("\n".join(lines) + "\n")
            print("{0}: {1} datasets".format(path, len(datasets)), flush=True)
    print("lists: {0}, files: {1}".format(len(jobs), nfiles))


if __name__ == "__main__":
    main()
