#!/usr/bin/env python3
"""Per-dataset splitting table of a submitted production: the bookkeeping kept next to the file lists.

    python3 splitting_table.py <area>/splitting.json <area> [<removed rows file>] > direct/splitting_<tag>.tsv

One row per (file list, year) of the work area's jobs_*.txt (every submission, e.g. jobs_data_fix1.txt;
a one-pass two-year job of jobs_*_dual.txt gives a row for each year, with the same njobs),
minus the (sample, year) rows of the optional removed-rows file (v2: wrong_rows.txt): files, DAS GB,
njobs, GB per job, analysis rate (min/GB) and its source, planned minutes (plan_splitting.job_minutes),
the DAS datasets.
"""
import glob
import json
import os
import re
import sys

from plan_splitting import job_minutes, rate_for


def main(splitting, area, removed=None):
    sp = json.load(open(splitting))
    drop = {tuple(int(x) for x in line.split()[:2]) for line in (open(removed) if removed else []) if line.strip()}
    rows = {}      # (sample, year) -> (njobs, the other year of a one-pass two-year job or None)
    for path in sorted(glob.glob(os.path.join(area, "jobs_*.txt"))):
        for line in open(path):
            p = [int(x) for x in line.split()]
            s, y, j, g = p[:4]
            also = p[4] if len(p) > 4 else None
            for yr, other in ((y, also), (also, y)):
                if yr is not None and (s, yr) not in drop:
                    rows[(s, yr)] = (g, other)
    print("# list\tsample\tyear\tfiles\tGB\tnjobs\tGB_per_job\tanalysis_min_per_GB\trate_source\tplanned_min\tDAS")
    for (s, y), (g, other) in sorted(rows.items()):
        name = "{0}.txt".format(s) if s < 1000 else "data_{0}_{1}.txt".format(s, y // 10)
        e = sp["lists"][name]
        r = rate_for(sp, name, s, y)
        src = e.get("rate_source") or ("own" if "{0}:{1}".format(name, y) in sp["measured"] else "kind/year/run max")
        if other is not None:
            # planned minutes of the shared job: both years' analysis on one copy
            src += "; one pass with {0}".format(other)
            r_job = r + rate_for(sp, name, s, other)
        else:
            r_job = r
        das = re.findall(r"^# DAS: (\S+)", open(os.path.join("direct/filelists", name)).read(), re.M)
        print("\t".join(str(x) for x in (name, s, y, e["files"], e["gb"], g, round(e["gb"] / g, 2), round(r, 3), src,
                                           round(job_minutes(sp, e["gb"] / g, r_job)), ",".join(das))))


if __name__ == "__main__":
    main(*sys.argv[1:4])
