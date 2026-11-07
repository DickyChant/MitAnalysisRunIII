#!/usr/bin/env python3
"""Build the MC normalization cache of a dataset: its Runs trees only, merged into one small file.

CRAB MC jobs normalize to the full dataset (genEventSumw etc. of every Runs tree). Without a cache each
job opens the whole dataset over xrootd (~3000 files for the 2025 W/DY samples), and one bad or slow
replica kills every job of the task. With the cache, submit_crab.py --runs-cache=<dir> points the job's
normalization list at this one file instead. The analyses read it unchanged (RDataFrame("Runs", ...)).

  python3 make_runs_cache.py --dataset=/WtoTauNu-2Jets_.../RunIII2024Summer24NanoAODv15-.../NANOAODSIM \\
      --out-dir=/eos/cms/store/user/<you>/norm_runs [--exclude-lfns=bad.lst] [--workers=48]

Writes <out-dir>/<name>.root and <name>.json (dataset, DAS file list hash, files used, files that failed).
Files that cannot be read after the retries are listed under "failed": submit_crab.py adds them to the
excluded inputs, so normalization and processed events stay consistent.
"""
import getopt
import hashlib
import json
import os
import subprocess
import sys
import time
from multiprocessing import Pool

REDIRECTOR = "root://cms-xrd-global.cern.ch/"
# fail fast on dead replicas (the retries below go back through the redirector)
os.environ.setdefault("XRD_CONNECTIONRETRY", "2")
os.environ.setdefault("XRD_REQUESTTIMEOUT", "120")


def cache_name(dataset):
    primary, processed, tier = dataset.strip("/").split("/")
    return "{0}__{1}__{2}".format(primary, processed, tier)


def files_hash(lfns):
    return hashlib.sha1("".join(l + "\n" for l in sorted(lfns)).encode()).hexdigest()


def das_files(dataset):
    instance = " instance=prod/phys03" if dataset.endswith("/USER") else ""
    out = subprocess.check_output(["dasgoclient", "-query", "file dataset={0}{1}".format(dataset, instance)]).decode()
    return sorted(l.strip() for l in out.splitlines() if l.strip().startswith("/store/"))


def copy_chunk(args):
    """Copy the Runs trees of a chunk of LFNs into one file; return (path, used, failed)."""
    idx, lfns, tmpdir, retries = args
    import ROOT
    ROOT.gErrorIgnoreLevel = ROOT.kError
    path = os.path.join(tmpdir, "chunk_{0:04d}.root".format(idx))
    done = path[:-5] + ".json"
    if os.path.exists(done) and os.path.exists(path):   # resume: chunk finished in an earlier run
        with open(done) as f:
            d = json.load(f)
        return path, d["used"], d["failed"]
    fout = ROOT.TFile(path, "RECREATE")
    out = None
    used, failed = [], []
    for lfn in lfns:
        ok = False
        for attempt in range(retries):
            try:   # PyROOT raises OSError when the open fails
                f = ROOT.TFile.Open(REDIRECTOR + lfn)
            except OSError:
                f = None
            t = f.Get("Runs") if f and not f.IsZombie() else None
            if t:
                fout.cd()
                # CopyEntries returns bytes, not entries: check the entry count instead
                n0 = out.GetEntries() if out is not None else 0
                if out is None:
                    out = t.CloneTree(-1, "fast")
                else:
                    out.CopyEntries(t, -1, "fast")
                ok = out.GetEntries() - n0 == t.GetEntries()
                if not ok:   # never keep a partial copy: a retry would double-count
                    raise RuntimeError("partial Runs copy from {0}; rerun (finished chunks are kept)".format(lfn))
            if f:
                f.Close()
            if ok:
                break
            time.sleep(5 * (attempt + 1))
        (used if ok else failed).append(lfn)
    fout.cd()
    if out is not None:
        out.Write()
    fout.Close()
    with open(done, "w") as f:
        json.dump({"used": used, "failed": failed}, f)
    return path, used, failed


def main():
    opts = {"dataset": None, "out_dir": None, "exclude_lfns": None, "workers": 48, "chunk": 25, "retries": 3}
    longopts = ["dataset=", "out-dir=", "exclude-lfns=", "workers=", "chunk=", "retries=", "help"]
    for k, v in getopt.getopt(sys.argv[1:], "", longopts)[0]:
        if k == "--help":
            print(__doc__)
            return
        key = k[2:].replace("-", "_")
        opts[key] = int(v) if key in ("workers", "chunk", "retries") else v
    if not opts["dataset"] or not opts["out_dir"]:
        sys.exit("ERROR: --dataset and --out-dir are required (see --help)")

    allfiles = das_files(opts["dataset"])
    if not allfiles:
        sys.exit("ERROR: DAS returned no files for {0}".format(opts["dataset"]))
    exclude = set()
    if opts["exclude_lfns"]:
        with open(opts["exclude_lfns"]) as f:
            exclude = {l.strip() for l in f if l.strip().startswith("/store/")}
    todo = [l for l in allfiles if l not in exclude]
    print("{0}: {1} files in DAS, {2} excluded up front".format(opts["dataset"], len(allfiles), len(allfiles) - len(todo)))

    name = cache_name(opts["dataset"])
    tmpdir = os.path.join(opts["out_dir"], "tmp_" + name)
    os.makedirs(tmpdir, exist_ok=True)
    chunks = [(i, todo[s:s + opts["chunk"]], tmpdir, opts["retries"]) for i, s in enumerate(range(0, len(todo), opts["chunk"]))]
    used, failed, parts = [], [], []
    t0 = time.time()
    with Pool(opts["workers"]) as pool:
        for n, (path, u, fl) in enumerate(pool.imap_unordered(copy_chunk, chunks), 1):
            parts.append(path)
            used += u
            failed += fl
            if n % 10 == 0 or n == len(chunks):
                print("  {0}/{1} chunks, {2} files read, {3} failed, {4:.0f} s".format(n, len(chunks), len(used), len(failed), time.time() - t0))
            sys.stdout.flush()

    out = os.path.join(opts["out_dir"], name + ".root")
    subprocess.check_call(["hadd", "-f", "-k", out] + sorted(parts), stdout=subprocess.DEVNULL)
    import ROOT
    df = ROOT.RDataFrame("Runs", out)
    nruns, sumw = df.Count().GetValue(), df.Sum("genEventSumw").GetValue()
    if nruns < len(used):
        sys.exit("ERROR: merged cache has {0} Runs entries for {1} files read".format(nruns, len(used)))
    for p in parts:
        os.remove(p)
        os.remove(p[:-5] + ".json")
    os.rmdir(tmpdir)
    meta = {"dataset": opts["dataset"], "das_files": len(allfiles), "das_hash": files_hash(allfiles),
            "excluded_up_front": sorted(exclude & set(allfiles)), "used": len(used), "failed": sorted(failed),
            "runs_entries": nruns, "genEventSumw": sumw, "created": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(os.path.join(opts["out_dir"], name + ".json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("Wrote {0}: {1} Runs entries from {2} files, genEventSumw={3:.6g}, {4} failed".format(out, nruns, len(used), sumw, len(failed)))
    for l in failed:
        print("  FAILED " + l)


if __name__ == "__main__":
    main()
