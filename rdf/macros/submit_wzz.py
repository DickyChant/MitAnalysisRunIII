#!/usr/bin/env python3
"""Condor submission of the fused (raw NanoAOD -> histograms) wzzAnalysis production on CMS Connect.
Run in rdf/macros/ after make_filelists.py.

    python3 submit_wzz.py --tag <tag> --kind mc|data --splitting direct/splitting.json [--max-wall 480] \\
        [--chunk-mb 5000] [--disk 12] [--no-tarball] [--only-years 20240 ...] [--only-samples 516 ...] [--submit]

Without --submit only the work area is prepared (tarball, wrapper, jobs.txt, submit file) and
the job count is printed. Work area: <base>/<tag>/ with output/ (fillhisto files, per-job
normalised: harvest with wvz wzz/harvest.py), logs/. +REQUIRED_OS = "rhel9": the CMS Connect
schedd otherwise defaults to rhel7, for which (2026) no glideins match, and CMSSW_14_1_4 is el9. Re-running with --missing-only writes a
jobs.txt with only the jobs whose output is absent (top-up; the harvest's per-job
normalisation makes partial and late jobs safe).
"""
import argparse
import math
import os
import re
import subprocess
import sys

ROW = re.compile(r"^\s*(\d+)\s+(\d+)\s*(no)?\s*$")
WRAPPER = r"""#!/bin/bash
# wzzAnalysis condor payload: $1 sample, $2 year, $3 job, $4 group (number of jobs of the sample)
# WZZ_COPY_INPUT=1 (default): the job's files are xrdcp'd to the worker in chunks of >= WZZ_CHUNK_MB,
# one wzzAnalysis run per chunk on the local copies (normalised to the chunk's files), the chunks
# merged with the harvest's weights (wzz_merge_chunks.py). Streamed jobs were read-bound (test3:
# ~3% CPU efficiency; the same jobs copied first ran 25-40x faster with identical histograms).
# WZZ_COPY_INPUT=0: stream with xrootd.
S=$1; Y=$2; J=$3; G=$4
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=el9_amd64_gcc12
scramv1 project CMSSW CMSSW_14_1_4 > /dev/null 2>&1
cd CMSSW_14_1_4/src && eval $(scramv1 runtime -sh) && cd ../..
tar xzf wzzAnalysis.tgz || { echo "FAILED untar"; exit 1; }
export USE_DIRECT_NANOAOD=1 FILELIST_DIR=direct/filelists
export XRD_NETWORKSTACK=IPv4 XRD_REQUESTTIMEOUT=600 XRD_REDIRECTLIMIT=255 XRD_CONNECTIONRETRY=4 XRD_STREAMTIMEOUT=120
echo "host $(hostname) site ${GLIDEIN_CMSSite:-unknown} cpu $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2) args $@"
out=fillhisto_wzzAnalysis_sample${S}_year${Y}_job${J}.root
one=fillhisto_wzzAnalysis_sample${S}_year${Y}_job0.root
status=0
if [ "${WZZ_COPY_INPUT:-1}" = 1 ]; then
  if [ $S -lt 1000 ]; then list=direct/filelists/$S.txt; kind=mc; else list=direct/filelists/data_${S}_$(( Y / 10 )).txt; kind=data; fi
  cp $list list.orig
  # the job's files: groupFiles stride (files[job::group])
  grep -v '^#' list.orig | awk -v j=$J -v g=$G 'NF { if (n % g == j) print; n++ }' > job_files.txt
  nc=0; nfiles=0; mbtot=0; tcopy=0; tana=0
  run_chunk() {
    (grep '^#' list.orig; cat local.txt) > $list
    local mb=$(du -sm input | cut -f1) t1=$(date +%s)
    python3 wzzAnalysis.py --process=$S --year=$Y --whichJob=0 --group=1 < /dev/null
    [ -f $one ] || { echo "FAILED chunk $nc: no output"; exit 1; }
    mv $one chunk_$nc.root
    local ta=$(( $(date +%s) - t1 ))
    echo "chunk $nc: $(wc -l < local.txt) files, $mb MB, analysis $ta s"
    tana=$((tana + ta)); mbtot=$((mbtot + mb)); nc=$((nc + 1))
    rm -rf input; mkdir -p input; : > local.txt
  }
  mkdir -p input; : > local.txt
  for f in $(cat job_files.txt); do
    lf=$PWD/input/$(basename $f); ok=0; t1=$(date +%s)
    # deadline per copy from the file size: slower than 2 MB/s is abandoned and retried through the
    # other redirector (another source), so one slow site pair cannot eat the job's wall time
    lfn="/store/${f#*/store/}"
    sz=$(timeout 120 xrdfs cmsxrootd.fnal.gov stat "$lfn" < /dev/null 2>/dev/null | awk '/Size:/ {print $2}')
    tmo=$(( 300 + ${sz:-4000000000} / 2000000 ))
    for src in "$f" "${f/cmsxrootd.fnal.gov/cms-xrd-global.cern.ch}" "$f" "${f/cmsxrootd.fnal.gov/cms-xrd-global.cern.ch}"; do
      timeout $tmo xrdcp -s -f "$src" "$lf" < /dev/null && { ok=1; break; }
      echo "copy attempt failed or slower than 2 MB/s (deadline $tmo s): $src"
      rm -f "$lf"; sleep 20
    done
    [ $ok = 1 ] || { echo "FAILED copy $f"; exit 1; }
    tcopy=$((tcopy + $(date +%s) - t1)); nfiles=$((nfiles + 1))
    echo "$lf" >> local.txt
    if [ $(du -sm input | cut -f1) -ge ${WZZ_CHUNK_MB:-6000} ]; then run_chunk; fi
  done
  if [ -s local.txt ]; then run_chunk; fi
  echo "copied $nfiles files, $mbtot MB in $tcopy s"
  echo "analysis $tana s in $nc chunks"
  if [ $nc = 0 ]; then echo "FAILED no files for job $J of $G"; exit 1; fi
  if [ $nc = 1 ]; then mv chunk_0.root $out
  else python3 wzz_merge_chunks.py $out $kind chunk_*.root < /dev/null || { echo "FAILED merge"; exit 1; }
  fi
  rm -rf input chunk_*.root
else
  t1=$(date +%s)
  python3 wzzAnalysis.py --process=$S --year=$Y --whichJob=$J --group=$G
  status=$?
  echo "analysis $(( $(date +%s) - t1 )) s"
fi
times > times.txt   # (not in a pipe: a subshell would report its own, empty, child times)
echo "cpu (user sys) of the payload: $(tail -n 1 times.txt)"
if [ $status -ne 0 ] || [ ! -f $out ]; then echo "FAILED status=$status"; exit 1; fi
echo DONE
"""
SUBMIT = """universe = vanilla
executable = {area}/wzz_condor.sh
arguments = $(sample) $(year) $(job) $(group)
request_memory = 4000
+MaxWallTimeMins = {maxwall}
request_cpus = 1
request_disk = {disk}GB
environment = "WZZ_COPY_INPUT={copy} WZZ_CHUNK_MB={chunk_mb}"
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_input_files = {area}/wzzAnalysis.tgz
transfer_output_files = fillhisto_wzzAnalysis_sample$(sample)_year$(year)_job$(job).root
transfer_output_remaps = "fillhisto_wzzAnalysis_sample$(sample)_year$(year)_job$(job).root = {area}/output/fillhisto_wzzAnalysis_sample$(sample)_year$(year)_job$(job).root"
log = {area}/logs/$(sample)_$(year)_$(job).log
output = {area}/logs/$(sample)_$(year)_$(job).out
error = {area}/logs/$(sample)_$(year)_$(job).err
+REQUIRED_OS = "rhel9"
use_x509userproxy = True
x509userproxy = {proxy}
max_retries = 2
# a failed payload leaves no output: condor then holds the job (output transfer, code 12) before
# max_retries applies; release such holds up to 3 starts, later ones stay held for inspection
periodic_release = (HoldReasonCode == 12 || HoldReasonCode == 13) && (NumJobStarts < 3)
queue sample, year, job, group from {jobs}
"""
# every local header (functions.h -> mysf.h -> muonCrystalBall.h, ...): a missing one only shows up on
# the worker nodes (the pilot failed on muonCrystalBall.h); utils*.py are the only local Python modules
TAR_ITEMS = ["wzzAnalysis.py", "wzz_merge_chunks.py", "*.h", "utils*.py", "tmva_helper_xml.*", "data", "jsns", "config",
             "jsonpog-integration", "direct/filelists"]


def nfiles(path):
    return sum(1 for line in open(path) if line.strip() and not line.startswith("#"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--base", default="/scratch/stqian/wzz_prod")
    ap.add_argument("--config", default="wzzAnalysis_input_condor_jobs.cfg")
    ap.add_argument("--mc-files-per-job", type=int, default=4)
    ap.add_argument("--data-files-per-job", type=int, default=4)
    ap.add_argument("--only-years", nargs="*", type=int)
    ap.add_argument("--only-samples", nargs="*", type=int)
    ap.add_argument("--missing-only", action="store_true")
    ap.add_argument("--kind", choices=("all", "mc", "data"), default="all")
    ap.add_argument("--max-jobs-per-sample", type=int, help="test submissions: only the first N jobs of each sample")
    ap.add_argument("--splitting", help="plan_splitting.py output: jobs per list from measured rates")
    ap.add_argument("--max-wall", type=int, default=480, help="+MaxWallTimeMins (jobs planned at half of it)")
    ap.add_argument("--no-tarball", action="store_true", help="keep the work area's tarball as it is")
    ap.add_argument("--stream", action="store_true", help="stream the inputs with xrootd instead of copying them")
    ap.add_argument("--chunk-mb", type=int, default=6000, help="copy mode: inputs held on the worker per chunk (MiB)")
    ap.add_argument("--disk", type=int, default=12, help="request_disk in GB (copy mode: chunk + largest file + 3)")
    ap.add_argument("--jobs-list", help="explicit 'sample year job group' rows (benchmarks), instead of the config")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--proxy", default="~/.wzz/x509_proxy",
                    help="grid proxy shipped with the jobs (long-lived copy of the EOS proxy; mode 600)")
    args = ap.parse_args()
    area = os.path.join(args.base, args.tag)
    for d in ("output", "logs"):
        os.makedirs(os.path.join(area, d), exist_ok=True)
    splitting = None
    if args.splitting:
        import json
        from plan_splitting import njobs as plan_njobs
        splitting = json.load(open(args.splitting))
    jobs, per = [], {}
    if args.jobs_list:
        for line in open(args.jobs_list):
            if line.strip() and not line.startswith("#"):
                s, y, j, g = (int(x) for x in line.split()[:4])
                jobs.append((s, y, j, g))
                per[(s, y)] = (0, g)
    for line in (open(args.config) if not args.jobs_list else []):
        m = ROW.match(line)
        if not m or m.group(3):
            continue
        s, y = int(m.group(1)), int(m.group(2))
        if (args.only_years and y not in args.only_years) or (args.only_samples and s not in args.only_samples):
            continue
        if (args.kind == "mc" and s >= 1000) or (args.kind == "data" and s < 1000):
            continue
        fl = "direct/filelists/{0}.txt".format(s) if s < 1000 else "direct/filelists/data_{0}_{1}.txt".format(s, y // 10)
        if not os.path.exists(fl):
            sys.exit("missing file list {0}: run make_filelists.py".format(fl))
        n = nfiles(fl)
        if n == 0:
            print("WARNING: empty file list", fl)
            continue
        fpj = args.mc_files_per_job if s < 1000 else args.data_files_per_job
        g = max(1, math.ceil(n / fpj))
        if splitting is not None:
            gs = plan_njobs(splitting, os.path.basename(fl), s, y)
            if gs is None:
                print("WARNING: no splitting entry for", fl, "-> files per job", fpj)
            else:
                g = gs
        per[(s, y)] = (n, g)
        for j in range(min(g, args.max_jobs_per_sample) if args.max_jobs_per_sample else g):
            out = os.path.join(area, "output", "fillhisto_wzzAnalysis_sample{0}_year{1}_job{2}.root".format(s, y, j))
            if args.missing_only and os.path.exists(out):
                continue
            jobs.append((s, y, j, g))
    jobs_file = os.path.join(area, "jobs_{0}.txt".format(args.kind))
    with open(jobs_file, "w") as f:
        for r in jobs:
            f.write("{0} {1} {2} {3}\n".format(*r))
    open(os.path.join(area, "wzz_condor.sh"), "w").write(WRAPPER)
    os.chmod(os.path.join(area, "wzz_condor.sh"), 0o755)
    proxy = os.path.expanduser(args.proxy)
    if not os.path.exists(proxy):
        sys.exit("no grid proxy at {0}".format(proxy))
    jdl = os.path.join(area, "submit_{0}.jdl".format(args.kind))
    open(jdl, "w").write(SUBMIT.format(area=area, proxy=proxy, jobs=jobs_file, maxwall=args.max_wall,
                                         disk=args.disk, copy=0 if args.stream else 1, chunk_mb=args.chunk_mb))
    if not args.no_tarball and (not args.missing_only or not os.path.exists(os.path.join(area, "wzzAnalysis.tgz"))):
        items = " ".join(TAR_ITEMS)
        subprocess.run("tar czf {0}/wzzAnalysis.tgz {1}".format(area, items), shell=True, check=True)
    nmc = sum(1 for r in jobs if r[0] < 1000)
    print("samples {0}  jobs {1} (MC {2}, data {3})  files {4}".format(
        len(per), len(jobs), nmc, len(jobs) - nmc, sum(n for n, _ in per.values())))
    print("work area", area)
    if args.submit:
        # CMS Connect's condor_submit checks X509_USER_PROXY (default /tmp/x509up_u<uid>) and tries an
        # interactive voms-proxy-init when that one is short: point it at the proxy the jobs ship
        subprocess.run(["condor_submit", jdl], check=True, stdin=subprocess.DEVNULL,
                       env=dict(os.environ, X509_USER_PROXY=proxy))
    else:
        print("not submitted (add --submit)")


if __name__ == "__main__":
    main()
