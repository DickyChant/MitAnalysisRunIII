#!/usr/bin/env python3
"""MC file lists like make_filelists.py, but from given DAS names (no ROOT / utilsAna import), plus the
DAS size summary plan_splitting.py needs. Runs in rdf/macros/ on CMS Connect (dasgoclient + proxy):

    X509_USER_PROXY=~/.wzz/x509_proxy python3 -u filelists_from_das.py <das.json> > log
    # das.json: {"<sample id>": "/<primary>/<processed>/NANOAODSIM"} from wzz/config/sample_table_fork.json

Writes direct/filelists/<id>.txt (same format: "# DAS: <name> (<n> files)" + redirector URLs) and
direct/dataset_summary_conv.json. Why: importing ROOT (LCG view) on the CMS Connect login node sat
for > 15 min on a cold CVMFS cache (v2c, 2026-11-17); the lists only need the DAS names.
"""
import json, subprocess, sys
das_of = json.load(open(sys.argv[1]))
red = "root://cmsxrootd.fnal.gov/"
summ = {}
for s, das in sorted(das_of.items(), key=lambda x: int(x[0])):
    r = subprocess.run(["dasgoclient", "-query", "file dataset=" + das], capture_output=True, text=True, timeout=300)
    fl = [x.strip() for x in r.stdout.splitlines() if x.strip().startswith("/store")]
    if r.returncode != 0 or not fl:
        print("WARNING", s, das, "rc", r.returncode, r.stderr.strip()[:200], flush=True)
    open("direct/filelists/%s.txt" % s, "w").write("\n".join(["# DAS: {0} ({1} files)".format(das, len(fl))] + [red + f for f in fl]) + "\n")
    q = subprocess.run(["dasgoclient", "-query", "summary dataset=" + das, "-json"], capture_output=True, text=True, timeout=300)
    try:
        j = json.loads(q.stdout)[0]["summary"][0]
        summ[das] = {"bytes": j["file_size"], "files": j["nfiles"], "events": j["nevents"]}
    except Exception:
        summ[das] = {"bytes": None, "files": len(fl), "events": None}
    print(s, len(fl), "files", round((summ[das]["bytes"] or 0) / 1e9, 1), "GB", summ[das]["events"], das, flush=True)
json.dump(summ, open("direct/dataset_summary_conv.json", "w"), indent=1)
print("DONE", len(summ))
