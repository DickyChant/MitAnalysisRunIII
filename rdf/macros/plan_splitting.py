#!/usr/bin/env python3
"""Job splitting from measured test jobs: number of jobs per file list such that a job is planned at
--plan minutes (default 240; the jobs run with +MaxWallTimeMins = 480, i.e. 100% margin).
Runs in rdf/macros/ on CMS Connect (stdlib only).

    # copy mode (the default of submit_wzz.py): rates from the wrapper logs of benchmark jobs
    python3 plan_splitting.py --bench-logs <area>/logs [<area2>/logs ...] --summary direct/dataset_summary.json \\
        --out direct/splitting.json
    # streaming jobs: rates from condor_history
    condor_history <cluster> -af Args RemoteWallClockTime ExitCode > test_history.txt
    python3 plan_splitting.py --history test_history.txt --summary direct/dataset_summary.json --out ...

Copy mode (--bench-logs): a job copies its files in chunks of --chunk-gb, runs wzzAnalysis per
chunk and merges (submit_wzz.py WRAPPER). Its planned minutes are
    overhead + GB x (analysis rate + copy rate) + chunks x chunk overhead (JIT per chunk)
with the analysis rate (min/GB) the slowest measured of the list's kind and year (falling back to
the same run, Run 2 or Run 3, then to all), and the copy rate the slowest copy measured anywhere
but at least --copy-floor (the copy speed depends on the site pair, not on the sample). Streaming
(--history): rate = (wall - overhead) / bytes of the job's files, the job's bytes being its file
share of the list's DAS total (stride grouping: representative files).
The njobs per (list, year) are resolved at submission (njobs()); the JSON is the bookkeeping kept
next to the file lists (direct/splitting.json).
"""
import argparse
import glob
import json
import math
import os
import re


def list_info(path, summary):
    txt = open(path).read()
    dsets = re.findall(r"^# DAS: (\S+)", txt, re.M)
    nfiles = sum(1 for line in txt.splitlines() if line.strip() and not line.startswith("#"))
    nbytes = sum((summary.get(d) or {}).get("bytes") or 0 for d in dsets)
    return nfiles, nbytes


def list_name(s, y):
    return "{0}.txt".format(s) if s < 1000 else "data_{0}_{1}.txt".format(s, y // 10)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", help="condor_history -af Args RemoteWallClockTime ExitCode (streaming jobs)")
    ap.add_argument("--bench-logs", nargs="+", help="dirs of wrapper .out logs of copy-mode jobs (copied / analysis lines)")
    ap.add_argument("--summary", default="direct/dataset_summary.json")
    ap.add_argument("--filelists", default="direct/filelists")
    ap.add_argument("--plan", type=float, default=240.0)
    ap.add_argument("--overhead", type=float, default=4.0, help="setup minutes per job (CMSSW area, untar)")
    ap.add_argument("--chunk-gb", type=float, default=6.0, help="copy mode: inputs per chunk (submit_wzz --chunk-mb)")
    ap.add_argument("--chunk-overhead", type=float, default=1.0, help="copy mode: minutes per chunk (JIT, merge)")
    ap.add_argument("--copy-floor", type=float, default=1.5, help="copy mode: min/GB at least (1.5 = 11 MB/s)")
    ap.add_argument("--max-files-per-job", type=int, default=150, help="limits what one bad file can take down")
    ap.add_argument("--out", default="direct/splitting.json")
    args = ap.parse_args()
    if not (args.history or args.bench_logs):
        ap.error("--history or --bench-logs")
    summary = json.load(open(args.summary))
    rates, meas, copy_rates = {}, {}, []

    def add(s, y, rate, **extra):
        kind = "mc" if s < 1000 else "data"
        meas["{0}:{1}".format(list_name(s, y), y)] = dict(sample=s, year=y, list=list_name(s, y),
                                                         min_per_gb=round(rate, 3), **extra)
        rates[(kind, y)] = max(rates.get((kind, y), 0), rate)

    for line in (open(args.history) if args.history else []):
        p = line.split()
        if len(p) < 6 or p[5] != "0":
            continue
        s, y, j, g, wall = int(p[0]), int(p[1]), int(p[2]), int(p[3]), float(p[4]) / 60.0
        nf, nb = list_info(os.path.join(args.filelists, list_name(s, y)), summary)
        if nb <= 0 or nf <= 0:
            continue
        job_gb = nb / 1e9 * len(range(j, nf, g)) / nf
        # a job of a few minutes is mostly overhead: at least 2 min of processing (rate floor)
        add(s, y, max(wall - args.overhead, 2.0) / job_gb, wall_min=round(wall, 1), job_gb=round(job_gb, 2))
    for path in sorted(p for d in (args.bench_logs or []) for p in glob.glob(os.path.join(d, "*.out"))):
        txt = open(path).read()
        a = re.search(r"args (\d+) (\d+) (-?\d+) (\d+)", txt)
        c = re.search(r"^copied (\d+) files, (\d+) MB in (\d+) s", txt, re.M)
        t = re.search(r"^analysis (\d+) s", txt, re.M)
        if not (a and c and t and re.search(r"^DONE", txt, re.M)):
            print("skip (incomplete):", path)
            continue
        s, y = int(a.group(1)), int(a.group(2))
        gb = max(int(c.group(2)) * 1.048576e-3, 0.05)   # du -sm: MiB
        copy_s, ana_s = int(c.group(3)), int(t.group(1))
        copy_rates.append(copy_s / 60.0 / gb)
        site = re.search(r"site (\S+)", txt)
        # analysis rate floor: 1 min per job (a tiny job is all JIT)
        add(s, y, max(ana_s / 60.0, 1.0) / gb, copy_min_per_gb=round(copy_s / 60.0 / gb, 3),
            analysis_min=round(ana_s / 60, 1), copy_min=round(copy_s / 60, 1), job_gb=round(gb, 2),
            site=site.group(1) if site else None)
    split = {}
    for name in sorted(os.listdir(args.filelists)):
        m = re.match(r"(data_(\d+)_(\d{4})|(\d+))\.txt$", name)
        if not m:
            continue
        nf, nb = list_info(os.path.join(args.filelists, name), summary)
        if nf == 0:
            continue
        e = {"files": nf, "gb": round(nb / 1e9, 2)}
        if m.group(2):
            own = [v["min_per_gb"] for v in meas.values() if v["list"] == name]
            if own:
                e["min_per_gb"], e["rate_source"] = max(own), "own"
        split[name] = e
    out = {"plan_min": args.plan, "overhead_min": args.overhead, "max_files_per_job": args.max_files_per_job,
           "mode": "copy" if args.bench_logs else "stream",
           "chunk_gb": args.chunk_gb if args.bench_logs else 0,
           "chunk_overhead_min": args.chunk_overhead if args.bench_logs else 0,
           "copy_min_per_gb": round(max(copy_rates + [args.copy_floor]), 3) if args.bench_logs else 0,
           "rates": {"{0}:{1}".format(k, y): round(r, 3) for (k, y), r in sorted(rates.items())},
           "measured": meas, "lists": split}
    json.dump(out, open(args.out, "w"), indent=1)
    print("measured jobs: {0}; analysis rates (min/GB) {1}; copy {2} min/GB".format(
        len(meas), out["rates"], out["copy_min_per_gb"]))
    print("written", args.out)


def rate_for(splitting, name, sample, year):
    """Analysis (or streaming) min/GB of one (list, year): own, else slowest of the kind and year,
    of the same run (Run 2: year < 20210), of the kind."""
    e = splitting["lists"][name]
    if e.get("min_per_gb"):
        return e["min_per_gb"]
    kind = "mc" if sample < 1000 else "data"
    rs = {tuple(k.split(":")): r for k, r in splitting["rates"].items()}
    for sel in (lambda y: y == year, lambda y: (y < 20210) == (year < 20210), lambda y: True):
        c = [r for (k, y), r in rs.items() if k == kind and sel(int(y))]
        if c:
            return max(c)
    raise KeyError("no rate for {0} {1}".format(kind, year))


def job_minutes(splitting, gb, rate):
    m = splitting["overhead_min"] + gb * (rate + splitting.get("copy_min_per_gb", 0))
    if splitting.get("chunk_gb"):
        m += math.ceil(gb / splitting["chunk_gb"]) * splitting["chunk_overhead_min"]
    return m


def njobs(splitting, name, sample, year):
    """Jobs for one (list, year) from a splitting.json: the fewest with every job <= plan minutes."""
    e = splitting["lists"].get(name)
    if not e:
        return None
    rate = rate_for(splitting, name, sample, year)
    n = max(1, math.ceil(e["files"] / splitting.get("max_files_per_job", 150)))
    while n < e["files"] and job_minutes(splitting, e["gb"] / n, rate) > splitting["plan_min"]:
        n += 1
    return min(e["files"], n)


if __name__ == "__main__":
    main()
