#!/usr/bin/env python3
"""Per-era completeness of a production (stdlib; runs in rdf/macros/ on CMS Connect).

    python3 era_status.py <area> [direct/splitting_<tag>.tsv]

An era is complete when every (sample, year) row of the splitting table that belongs to it has
all its job outputs in <area>/output: the MC of the era and the data harvested with it (2025
MC with 2025 + 2026 data, as wzz/harvest.DATA_ERAS). Prints one "COMPLETE <era>" line per
complete era, then "era MC done/total data done/total" per era.
"""
import collections
import os
import re
import sys

DATA_ERAS = {20250: (20250, 20260)}


def main(area, table="direct/splitting_v2.tsv"):
    need = {}
    for line in open(table):
        if line.startswith("#"):
            continue
        p = line.split("\t")
        need[(int(p[1]), int(p[2]))] = int(p[5])
    have = collections.defaultdict(set)
    for name in os.listdir(os.path.join(area, "output")):
        m = re.search(r"sample(\d+)_year(\d+)_job(\d+)\.root$", name)
        if m:
            have[(int(m.group(1)), int(m.group(2)))].add(int(m.group(3)))
    data_to_era = {d: e for e, ds in DATA_ERAS.items() for d in ds}
    stat = collections.defaultdict(lambda: [0, 0, 0, 0])   # mc done, mc jobs, data done, data jobs
    for (s, y), n in need.items():
        era = y if s < 1000 else data_to_era.get(y, y)
        k = 0 if s < 1000 else 2
        stat[era][k] += len(have[(s, y)] & set(range(n)))
        stat[era][k + 1] += n
    for era in sorted(stat):
        a = stat[era]
        if a[1] and a[0] == a[1] and a[2] == a[3]:
            print("COMPLETE", era)
    for era in sorted(stat):
        a = stat[era]
        print("{0} MC {1}/{2} data {3}/{4}".format(era, *a))


if __name__ == "__main__":
    main(*sys.argv[1:3])
