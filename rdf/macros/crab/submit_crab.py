#!/usr/bin/env python3
"""
Submit RDataFrame analyses (default: wzAnalysis ntuple production) to CRAB.

One CRAB task per (sample ID, year, DAS dataset). DAS dataset names are derived
from the skim directory names in utilsAna.py (SwitchSample for MC, getDATAlist
for data: "A+B+C" -> "/A/B/C"), so the cfg file stays the single source of truth.
Samples that are not in DAS (private/scratch samples) are listed and skipped:
run those with direct/submit_condor.sh.

Usage (from rdf/macros/crab/, after cmsenv in a CMSSW area + crab client + proxy):

    # see what would be submitted (no DAS / CRAB calls)
    python3 submit_crab.py --tag=v1 --dry-run

    # 2026 data and 2024 MC only, real submission
    python3 submit_crab.py --tag=v1 --years=20260,20240 --site=T2_US_MIT

    # selected samples
    python3 submit_crab.py --tag=v1 --processes=503,510 --site=T2_US_MIT

Options:
    --tag=<str>            production tag, part of task names and output path (required)
    --site=<CMS site>      Site.storageSite (required unless --dry-run)
    --lfn-base=<path>      Data.outLFNDirBase (default /store/user/<CERN user>/<ana>_crab)
    --ana=<name>           analysis driver (default wzAnalysis)
    --cfg=<file>           sample list (default ../<ana>_input_condor_jobs.cfg)
    --years=a,b            only these year codes
    --processes=a,b        only these sample IDs
    --mc-files-per-job=N   (default 5)   --data-files-per-job=N (default 10)
    --no-ntuples           histograms only (keep doNtuples as in the code)
    --redirector=<url>     prefix for LFNs on the worker (default root://cms-xrd-global.cern.ch/)
    --work-area=<dir>      CRAB project dir (default crab_projects)
    --dry-run              resolve tasks and build the payload, do not query DAS or submit
"""

import os
import re
import sys
import getopt
import io
import shutil
import tarfile
import multiprocessing
from subprocess import check_output, CalledProcessError

CRAB_DIR = os.path.dirname(os.path.abspath(__file__))
MACROS_DIR = os.path.dirname(CRAB_DIR)
BUILD_DIR = os.path.join(CRAB_DIR, "build")

# Same mapping as subDirName in mysf.h: ship only the POG eras that are used
POG_SUBDIR = {
    20160: "Run2-2016preVFP-UL-NanoAODv15",
    20161: "Run2-2016postVFP-UL-NanoAODv15",
    20170: "Run2-2017-UL-NanoAODv15",
    20180: "Run2-2018-UL-NanoAODv15",
    20220: "Run3-22CDSep23-Summer22-NanoAODv12",
    20221: "Run3-22EFGSep23-Summer22EE-NanoAODv12",
    20230: "Run3-23CSep23-Summer23-NanoAODv12",
    20231: "Run3-23DSep23-Summer23BPix-NanoAODv12",
    20240: "Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15",
    20250: "Run3-25Prompt-Summer24-NanoAODv15",
    20260: "Run3-26Prompt-Summer24-NanoAODv15",
    20261: "Run3-26Prompt-Summer24-NanoAODv15",
}

SANDBOX_LIMIT_MB = 120
DAS_DIR = re.compile(r"^[^+/]+\+[^+/]+\+(NANOAOD|NANOAODSIM|USER)$")

SKIM_TYPE = {"wzAnalysis": "3l", "fakeAnalysis": "1l", "triggerAnalysis": "2l",
             "metAnalysis": "met", "puAnalysis": "2l"}

sys.path.insert(0, MACROS_DIR)
os.chdir(MACROS_DIR)


def read_cfg(path, years, processes):
    entries = []
    for line in open(path):
        tok = line.split()
        if not tok or tok[0].startswith("#"):
            continue
        if len(tok) >= 3 and tok[2] == "no":
            continue
        process, year = int(tok[0]), int(tok[1])
        if years and year not in years:
            continue
        if processes and process not in processes:
            continue
        entries.append((process, year))
    return entries


def skim_dirs(process, year, skim_type):
    """Directories utilsAna would read for this sample (findDIR is intercepted)."""
    import ROOT
    import utilsAna
    seen = []

    def record(directory):
        seen.append(directory)
        return ROOT.vector('string')()

    utilsAna.findDIR = record
    utilsAna.USE_DIRECT_NANOAOD = False
    if process < 1000:
        seen.append(utilsAna.SwitchSample(process, skim_type)[0])
    else:
        utilsAna.getDATAlist(process, year, skim_type)
    return seen


def golden_json(year):
    """Golden JSON getDATAlist loads for a data year, or None if it is missing."""
    src = open(os.path.join(MACROS_DIR, "utilsAna.py")).read()
    m = re.search(r"year == {0}\):\s*\n\s*jsnName = \"([^\"]+)\"".format(year // 10), src)
    if not m:
        return None
    return m.group(1) if os.path.exists(os.path.join(MACROS_DIR, "jsns", m.group(1))) else None


def resolve_tasks(entries, skim_type):
    tasks, private = [], []
    for process, year in entries:
        for d in skim_dirs(process, year, skim_type):
            base = os.path.basename(d.rstrip("/"))
            if not DAS_DIR.match(base):
                private.append((process, year, d))
                continue
            das = "/" + base.replace("+", "/")
            tasks.append({"process": process, "year": year, "dataset": das})
    return tasks, private


def das_files(dataset):
    out = check_output(["dasgoclient", "-query", "file dataset={0}".format(dataset)]).decode()
    return sorted(l.strip() for l in out.splitlines() if l.strip().startswith("/store/"))


def build_payload(ana, years, mc_norm):
    """Trimmed sandbox: code, config, corrections for the requested years only."""
    if os.path.isdir(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)
    payload = os.path.join(BUILD_DIR, "payload.tgz")
    code = [ana + ".py", "functions.h", "mysf.h", "tmva_helper_xml.h", "tmva_helper_xml.py"]
    code += sorted(f for f in os.listdir(".") if f.startswith("utils") and f.endswith(".py"))

    def keep_jsns(info):
        return None if os.path.basename(info.name).startswith("lumi_") else info

    with tarfile.open(payload, "w:gz") as tar:
        for f in code:
            tar.add(f)
        for d in ("config", "data"):
            tar.add(d)
        tar.add("jsns", filter=keep_jsns)
        if ana == "wzAnalysis":
            tar.add("weights_mva/bdt_BDTG_vbfinc_nsel0_v0.weights.xml")
        for pog in sorted(os.listdir("jsonpog-integration/POG")):
            for sub in sorted({POG_SUBDIR[y] for y in years if y in POG_SUBDIR}):
                path = os.path.join("jsonpog-integration/POG", pog, sub)
                if os.path.isdir(path):
                    tar.add(path)
        for name, files in mc_norm.items():
            info = tarfile.TarInfo("crab_norm/" + name)
            data = "".join(f + "\n" for f in files).encode()
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    size_mb = os.path.getsize(payload) / 1024.0 / 1024.0
    print("Payload {0}: {1:.1f} MB".format(payload, size_mb))
    if size_mb > SANDBOX_LIMIT_MB - 5:
        sys.exit("ERROR: payload too large for the CRAB sandbox ({0} MB limit); submit fewer years at once".format(SANDBOX_LIMIT_MB))
    return payload


def task_name(ana, tag, task):
    primary, processed = task["dataset"].split("/")[1:3]
    name = "{0}_{1}_s{2}_y{3}_{4}_{5}".format(ana, tag, task["process"], task["year"], primary, processed)
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)[:100]


def make_config(opts, task, payload):
    from CRABClient.UserUtilities import config
    cfg = config()
    cfg.General.requestName = task_name(opts["ana"], opts["tag"], task)
    cfg.General.workArea = opts["work_area"]
    cfg.General.transferOutputs = True
    cfg.General.transferLogs = True

    is_mc = task["process"] < 1000
    args = ["process={0}".format(task["process"]), "year={0}".format(task["year"]),
            "ana={0}".format(opts["ana"]), "ntuples={0}".format(1 if opts["ntuples"] else 0),
            "redirector={0}".format(opts["redirector"])]
    if is_mc:
        args.append("normlist=crab_norm/{0}.txt".format(task["process"]))

    cfg.JobType.pluginName = "Analysis"
    cfg.JobType.psetName = os.path.join(CRAB_DIR, "PSet.py")
    cfg.JobType.scriptExe = os.path.join(CRAB_DIR, "crab_script.sh")
    cfg.JobType.scriptArgs = args
    cfg.JobType.inputFiles = [payload]
    cfg.JobType.outputFiles = ["fillhisto.root"] + (["ntuple.root"] if opts["ntuples"] else [])
    cfg.JobType.maxMemoryMB = 2500
    cfg.JobType.allowUndistributedCMSSW = True

    cfg.Data.inputDataset = task["dataset"]
    cfg.Data.inputDBS = "phys03" if task["dataset"].endswith("/USER") else "global"
    cfg.Data.splitting = "FileBased"
    cfg.Data.unitsPerJob = opts["mc_fpj"] if is_mc else opts["data_fpj"]
    cfg.Data.publication = False
    cfg.Data.outLFNDirBase = "{0}/{1}".format(opts["lfn_base"], opts["tag"])
    cfg.Data.outputDatasetTag = cfg.General.requestName

    cfg.Site.storageSite = opts["site"]
    return cfg


def submit_one(opts, task, payload):
    from CRABAPI.RawCommand import crabCommand
    from CRABClient.ClientExceptions import ClientException
    cfg = make_config(opts, task, payload)
    try:
        crabCommand("submit", config=cfg)
    except (ClientException, Exception) as e:
        print("SUBMIT FAILED {0}: {1}".format(cfg.General.requestName, e))


def main():
    opts = {"tag": None, "site": None, "lfn_base": None, "ana": "wzAnalysis", "cfg": None,
            "years": set(), "processes": set(), "mc_fpj": 5, "data_fpj": 10, "ntuples": True,
            "redirector": "root://cms-xrd-global.cern.ch/", "work_area": "crab_projects",
            "dry_run": False}
    valid = ["tag=", "site=", "lfn-base=", "ana=", "cfg=", "years=", "processes=",
             "mc-files-per-job=", "data-files-per-job=", "no-ntuples", "redirector=",
             "work-area=", "dry-run", "help"]
    try:
        parsed, _ = getopt.getopt(sys.argv[1:], "", valid)
    except getopt.GetoptError as ex:
        sys.exit(str(ex) + "\n" + __doc__)
    for opt, arg in parsed:
        if opt == "--help":
            print(__doc__)
            return
        key = opt[2:].replace("-", "_")
        if key in ("years", "processes"):
            opts[key] = {int(x) for x in arg.split(",") if x}
        elif key == "mc_files_per_job":
            opts["mc_fpj"] = int(arg)
        elif key == "data_files_per_job":
            opts["data_fpj"] = int(arg)
        elif key == "no_ntuples":
            opts["ntuples"] = False
        elif key == "dry_run":
            opts["dry_run"] = True
        else:
            opts[key] = arg

    if not opts["tag"]:
        sys.exit("ERROR: --tag is required\n" + __doc__)
    if not opts["dry_run"] and not opts["site"]:
        sys.exit("ERROR: --site is required for submission")
    if opts["ana"] not in SKIM_TYPE:
        sys.exit("ERROR: unknown analysis {0}".format(opts["ana"]))
    if not opts["cfg"]:
        opts["cfg"] = "{0}_input_condor_jobs.cfg".format(opts["ana"])
    opts["work_area"] = os.path.join(CRAB_DIR, opts["work_area"])

    entries = read_cfg(opts["cfg"], opts["years"], opts["processes"])
    tasks, private = resolve_tasks(entries, SKIM_TYPE[opts["ana"]])

    data_years = sorted({t["year"] for t in tasks if t["process"] >= 1000})
    missing = [y for y in data_years if not golden_json(y)]
    if missing:
        sys.exit("ERROR: golden JSON missing in jsns/ for data years {0}: every data event "
                 "would be rejected by the lumi filter. Add the JSON or drop these years.".format(missing))

    print("{0} CRAB tasks:".format(len(tasks)))
    for t in tasks:
        print("  s{process:<5} y{year}  {dataset}".format(**t))
    if private:
        print("\n{0} samples are not in DAS; run them with direct/submit_condor.sh:".format(len(private)))
        for process, year, d in private:
            print("  s{0:<5} y{1}  {2}".format(process, year, d))
    if not tasks:
        return

    mc_norm = {}
    if not opts["dry_run"]:
        if not opts["lfn_base"]:
            from CRABClient.UserUtilities import getUsername
            opts["lfn_base"] = "/store/user/{0}/{1}_crab".format(getUsername(), opts["ana"])
        for t in tasks:
            if t["process"] < 1000 and str(t["process"]) + ".txt" not in mc_norm:
                try:
                    files = das_files(t["dataset"])
                except CalledProcessError as e:
                    sys.exit("ERROR: DAS query failed for {0}: {1}".format(t["dataset"], e))
                if not files:
                    sys.exit("ERROR: DAS returned no files for {0}".format(t["dataset"]))
                mc_norm[str(t["process"]) + ".txt"] = [opts["redirector"] + f for f in files]

    payload = build_payload(opts["ana"], {t["year"] for t in tasks}, mc_norm)
    if opts["dry_run"]:
        print("\nDry run: nothing submitted. Output would go to <lfn-base>/{0}".format(opts["tag"]))
        return

    for t in tasks:
        # CRAB client keeps global state; one process per submission
        p = multiprocessing.Process(target=submit_one, args=(opts, t, payload))
        p.start()
        p.join()


if __name__ == "__main__":
    main()
