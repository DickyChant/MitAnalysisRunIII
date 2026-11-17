#!/usr/bin/env python3
"""Condor submission of the fused (raw NanoAOD -> histograms) wzzAnalysis production on CMS Connect.
Run in rdf/macros/ after make_filelists.py.

    python3 submit_wzz.py --tag <tag> --kind mc|data --splitting direct/splitting.json [--max-wall 480] \\
        [--chunk-mb 5000] [--disk 12] [--no-tarball] [--only-years 20240 ...] [--only-samples 516 ...] [--submit]

Job config rows "<sample> <year>"; "<sample> 20240 +20250" (Summer24 MC) is one job per file group that
copies the files once and runs wzzAnalysis for 2024 and for 2025 (each with its own calibrations),
delivering both outputs (jobs_<name>_dual.txt, second queue block of the submit file). v2 and earlier
ran them as separate jobs: top-ups of those areas use their own config (direct/v2_jobs.cfg), since the
job split differs.

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

# job config row: "<sample> <year> [+<second year>] [no]"; "+20250" on a Summer24 MC row (year 20240) runs the
# 2025 normalisation and calibrations on the same copy of the files (one job, two outputs)
ROW = re.compile(r"^\s*(?P<sample>\d+)\s+(?P<year>\d+)(?:\s+\+(?P<also>\d+))?\s*(?P<no>no)?\s*$")
WRAPPER = r"""#!/bin/bash
# wzzAnalysis condor payload: $1 sample, $2 year, $3 job, $4 group (number of jobs of the sample)
# WZZ_COPY_INPUT=1 (default): the job's files are xrdcp'd to the worker in chunks of >= WZZ_CHUNK_MB,
# one wzzAnalysis run per chunk on the local copies (normalised to the chunk's files), the chunks
# merged with the harvest's weights (wzz_merge_chunks.py). Streamed jobs were read-bound (test3:
# ~3% CPU efficiency; the same jobs copied first ran 25-40x faster with identical histograms).
# WZZ_COPY_INPUT=0: stream with xrootd.
# $5 (optional) a second year code for the same MC files, e.g. 20250 for the Summer24 samples run as
# 20240: each chunk is analysed for both years on the local copy (the input is copied once) and the
# job delivers two outputs. The two years differ in calibrations (JEC/JER, veto maps, PU, SFs: one
# year's corrections per process in the framework), hence one wzzAnalysis run per year.
S=$1; Y=$2; J=$3; G=$4; ALSO=${5:-}
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=el9_amd64_gcc12
scramv1 project CMSSW CMSSW_14_1_4 > /dev/null 2>&1
cd CMSSW_14_1_4/src && eval $(scramv1 runtime -sh) && cd ../..
tar xzf wzzAnalysis.tgz || { echo "FAILED untar"; exit 1; }
export USE_DIRECT_NANOAOD=1 FILELIST_DIR=direct/filelists
export XRD_NETWORKSTACK=IPv4 XRD_REQUESTTIMEOUT=600 XRD_REDIRECTLIMIT=255 XRD_CONNECTIONRETRY=4 XRD_STREAMTIMEOUT=120
echo "host $(hostname) site ${GLIDEIN_CMSSite:-unknown} cpu $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2) args $@"
years="$Y $ALSO"
outof() { echo fillhisto_wzzAnalysis_sample${S}_year$1_job$2.root; }
out=$(outof $Y $J)
status=0
# every failure removes the outputs: condor then holds the job (no output to transfer, code 12) and
# periodic_release retries it; a partial file must never reach output/ (the harvest would take it)
fail() { echo "FAILED $*"; rm -f fillhisto_*.root chunk_*.root; exit 1; }
# input check per chunk: an empty NanoAOD file (0 events) keeps only ~16 branches and breaks the TChain
# switch in RDF (TChain::LoadTree -6, 2022 MuonEG); data lose nothing by dropping it, MC files only if
# their Runs genEventSumw is 0 too (the normalisation is unchanged). An unreadable file (not copied and
# not streamable, or a broken copy) is dropped for MC (the job normalises to the genEventSumw of the
# files it reads: only statistics are lost; v2c: a DYG file with no replica online) and fails a data job
# (its luminosity would be lost silently).
cat > wzz_check_inputs.py <<'PY'
import sys
import ROOT
ROOT.gErrorIgnoreLevel = ROOT.kError
kind, lst = sys.argv[1], sys.argv[2]
for p in [l.strip() for l in open(lst) if l.strip()]:
    try:
        f = ROOT.TFile.Open(p)
    except OSError:                   # recent PyROOT raises instead of returning a null file
        f = None
    ev = f.Get("Events") if f and not f.IsZombie() else None
    if not ev:
        if kind == "mc":
            sys.stderr.write("dropping unreadable MC input " + p + "\n")
            continue
        sys.exit("unreadable input " + p)
    drop = False
    if ev.GetEntries() == 0:
        sumw = 0.0
        runs = f.Get("Runs")
        if kind == "mc" and runs:
            for r in runs:
                sumw += getattr(r, "genEventSumw", 0.0)
        drop = sumw == 0.0
    if drop:
        sys.stderr.write("dropping empty input " + p + "\n")
    else:
        print(p)
    f.Close()
PY
if [ "${WZZ_COPY_INPUT:-1}" = 1 ]; then
  if [ $S -lt 1000 ]; then list=direct/filelists/$S.txt; kind=mc; else list=direct/filelists/data_${S}_$(( Y / 10 )).txt; kind=data; fi
  cp $list list.orig
  # the job's files: groupFiles stride (files[job::group])
  grep -v '^#' list.orig | awk -v j=$J -v g=$G 'NF { if (n % g == j) print; n++ }' > job_files.txt
  nc=0; nfiles=0; nstream=0; mbtot=0; tcopy=0; declare -A tana
  run_chunk() {
    python3 wzz_check_inputs.py $kind local.txt < /dev/null > keep.txt || fail "input check (chunk $nc)"
    local nd=$(( $(wc -l < local.txt) - $(wc -l < keep.txt) ))
    if [ $nd -gt 0 ]; then echo "chunk $nc: dropped $nd empty or unreadable input(s) (see stderr)"; fi
    if [ ! -s keep.txt ]; then echo "chunk $nc: only empty files, skipped"; rm -rf input; mkdir -p input; : > local.txt; return 0; fi
    (grep '^#' list.orig; cat keep.txt) > $list
    local mb=$(du -sm input | cut -f1) yr tlog=""
    for yr in $years; do
      local t1=$(date +%s) one=$(outof $yr 0)
      python3 wzzAnalysis.py --process=$S --year=$yr --whichJob=0 --group=1 < /dev/null > chunk.log
      local st=$?
      cat chunk.log
      # wzzAnalysis prints FAILED on an exception and may still leave an (empty) output file
      if [ $st -ne 0 ] || grep -q "^FAILED" chunk.log || [ ! -s $one ]; then fail "chunk $nc year $yr: wzzAnalysis status $st"; fi
      mv $one chunk_${yr}_$nc.root
      local ta=$(( $(date +%s) - t1 ))
      tana[$yr]=$(( ${tana[$yr]:-0} + ta )); tlog="$tlog, analysis $ta s ($yr)"
    done
    echo "chunk $nc: $(wc -l < local.txt) files, $mb MB$tlog"
    mbtot=$((mbtot + mb)); nc=$((nc + 1))
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
    for src in "$f" "${f/cmsxrootd.fnal.gov/cms-xrd-global.cern.ch}"; do
      t2=$(date +%s); timeout $tmo xrdcp -s -f "$src" "$lf" < /dev/null; xs=$?
      [ $xs = 0 ] && { ok=1; break; }
      echo "copy attempt failed: status $xs (124 = deadline $tmo s, i.e. < 2 MB/s) after $(( $(date +%s) - t2 )) s: $src"
      rm -f "$lf"; sleep 20
    done
    tcopy=$((tcopy + $(date +%s) - t1)); nfiles=$((nfiles + 1))
    # a file that cannot be copied is streamed by its chunk instead of failing the job (v2: 5-6 h jobs
    # lost to one file on their last copy); an unreadable stream still fails (input check, wzzAnalysis)
    if [ $ok = 1 ]; then echo "$lf" >> local.txt; else echo "streaming instead: $f"; echo "$f" >> local.txt; nstream=$((nstream + 1)); fi
    if [ $(du -sm input | cut -f1) -ge ${WZZ_CHUNK_MB:-6000} ]; then run_chunk; fi
  done
  if [ -s local.txt ]; then run_chunk; fi
  echo "copied $nfiles files, $mbtot MB in $tcopy s ($nstream streamed)"
  # one line per year: "analysis <s> s in <n> chunks" for $Y (plan_splitting.py reads the first),
  # "analysis[<year>] <s> s ..." for the second year
  echo "analysis ${tana[$Y]:-0} s in $nc chunks"
  if [ -n "$ALSO" ]; then echo "analysis[$ALSO] ${tana[$ALSO]:-0} s in $nc chunks"; fi
  if [ $nc = 0 ]; then fail "no non-empty files for job $J of $G ($nfiles copied)"; fi
  for yr in $years; do
    if [ $nc = 1 ]; then mv chunk_${yr}_0.root $(outof $yr $J)
    else python3 wzz_merge_chunks.py $(outof $yr $J) $kind chunk_${yr}_*.root < /dev/null || fail "merge $yr"
    fi
  done
  rm -rf input chunk_*.root
else
  for yr in $years; do
    t1=$(date +%s)
    python3 wzzAnalysis.py --process=$S --year=$yr --whichJob=$J --group=$G < /dev/null > run.log
    st=$?
    cat run.log
    if [ $st -ne 0 ] || grep -q "^FAILED" run.log; then status=1; fi
    if [ $yr = $Y ]; then echo "analysis $(( $(date +%s) - t1 )) s"; else echo "analysis[$yr] $(( $(date +%s) - t1 )) s"; fi
  done
fi
times > times.txt   # (not in a pipe: a subshell would report its own, empty, child times)
echo "cpu (user sys) of the payload: $(tail -n 1 times.txt)"
if [ $status -ne 0 ]; then fail "status=$status"; fi
for yr in $years; do [ -s $(outof $yr $J) ] || fail "no output for year $yr"; done
echo DONE
"""
SUBMIT = """universe = vanilla
executable = {area}/wzz_condor.sh
request_memory = 4000
+MaxWallTimeMins = {maxwall}
request_cpus = 1
request_disk = {disk}GB
environment = "WZZ_COPY_INPUT={copy} WZZ_CHUNK_MB={chunk_mb}"
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_input_files = {area}/wzzAnalysis.tgz
log = {area}/logs/$(sample)_$(year)_$(job).log
output = {area}/logs/$(sample)_$(year)_$(job).out
error = {area}/logs/$(sample)_$(year)_$(job).err
+REQUIRED_OS = "rhel9"
{sites}use_x509userproxy = True
x509userproxy = {proxy}
max_retries = 2
# a failed payload leaves no output: condor then holds the job (output transfer, code 12) before
# max_retries applies; 26: site policy (v2: CPU usage above the request with implicit MT, now off).
# Release such holds up to 3 starts, later ones stay held for inspection
periodic_release = (HoldReasonCode == 12 || HoldReasonCode == 13 || HoldReasonCode == 26) && (NumJobStarts < 3)
"""
OUT = "fillhisto_wzzAnalysis_sample$(sample)_year$({year})_job$(job).root"
QUEUE_SINGLE = """arguments = $(sample) $(year) $(job) $(group)
transfer_output_files = {o}
transfer_output_remaps = "{o} = {area}/output/{o}"
queue sample, year, job, group from {jobs}
""".format(o=OUT.format(year="year"), area="{area}", jobs="{jobs}")
# one copy of the inputs, two years (wrapper $5): both outputs come back
QUEUE_DUAL = """arguments = $(sample) $(year) $(job) $(group) $(also)
transfer_output_files = {o},{o2}
transfer_output_remaps = "{o} = {area}/output/{o}; {o2} = {area}/output/{o2}"
queue sample, year, job, group, also from {jobs}
""".format(o=OUT.format(year="year"), o2=OUT.format(year="also"), area="{area}", jobs="{jobs}")
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
    ap.add_argument("--sites", help="comma-separated +DESIRED_Sites (default: CMS Connect's, all sites). v2: copies ran at "
                                    "30-55 MB/s at the US T1/T2s vs 11-17 at JINR/CNAF, where the slowest jobs ran")
    ap.add_argument("--jobs-list", help="explicit 'sample year job group [second year]' rows (benchmarks, duplicates), "
                                        "instead of the config")
    ap.add_argument("--name", help="label of the jobs_<name>.txt / submit_<name>.jdl files (default: --kind)")
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
    jobs, per = [], {}     # jobs: (sample, year, job, group, second year or None)
    if args.jobs_list:
        for line in open(args.jobs_list):
            if line.strip() and not line.startswith("#"):
                p = [int(x) for x in line.split()[:5]]
                jobs.append(tuple(p[:4]) + (p[4] if len(p) > 4 else None,))
                per[(p[0], p[1])] = (0, p[3])
    for line in (open(args.config) if not args.jobs_list else []):
        m = ROW.match(line)
        if not m or m.group("no"):
            continue
        s, y = int(m.group("sample")), int(m.group("year"))
        also = int(m.group("also")) if m.group("also") else None
        if also is not None and s >= 1000:
            sys.exit("a second year is for MC rows only: " + line.strip())
        if (args.only_years and y not in args.only_years and also not in args.only_years) or \
                (args.only_samples and s not in args.only_samples):
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
            gs = plan_njobs(splitting, os.path.basename(fl), s, y, also)
            if gs is None:
                print("WARNING: no splitting entry for", fl, "-> files per job", fpj)
            else:
                g = gs
        per[(s, y)] = (n, g)
        for j in range(min(g, args.max_jobs_per_sample) if args.max_jobs_per_sample else g):
            outs = [os.path.join(area, "output", "fillhisto_wzzAnalysis_sample{0}_year{1}_job{2}.root".format(s, yr, j))
                    for yr in (y, also) if yr is not None]
            # a two-year job reruns when either output is missing (it rewrites both)
            if args.missing_only and all(os.path.exists(o) for o in outs):
                continue
            jobs.append((s, y, j, g, also))
    name = args.name or args.kind
    jobs_file = os.path.join(area, "jobs_{0}.txt".format(name))
    dual_file = os.path.join(area, "jobs_{0}_dual.txt".format(name))
    single = [r for r in jobs if r[4] is None]
    dual = [r for r in jobs if r[4] is not None]
    with open(jobs_file, "w") as f:
        for r in single:
            f.write("{0} {1} {2} {3}\n".format(*r))
    if dual:
        with open(dual_file, "w") as f:
            for r in dual:
                f.write("{0} {1} {2} {3} {4}\n".format(*r))
    elif os.path.exists(dual_file):
        os.remove(dual_file)
    # written aside and renamed: queued jobs of running clusters read the wrapper / tarball at start
    tmp = os.path.join(area, ".wzz_condor.sh.new")
    open(tmp, "w").write(WRAPPER)
    os.chmod(tmp, 0o755)
    os.replace(tmp, os.path.join(area, "wzz_condor.sh"))
    proxy = os.path.expanduser(args.proxy)
    if not os.path.exists(proxy):
        sys.exit("no grid proxy at {0}".format(proxy))
    jdl = os.path.join(area, "submit_{0}.jdl".format(name))
    open(jdl, "w").write(SUBMIT.format(area=area, proxy=proxy, maxwall=args.max_wall,
                                       disk=args.disk, copy=0 if args.stream else 1, chunk_mb=args.chunk_mb,
                                       sites='+DESIRED_Sites = "{0}"\n'.format(args.sites) if args.sites else "")
                         + (QUEUE_SINGLE.format(area=area, jobs=jobs_file) if single else "")
                         + (QUEUE_DUAL.format(area=area, jobs=dual_file) if dual else ""))
    if not args.no_tarball and (not args.missing_only or not os.path.exists(os.path.join(area, "wzzAnalysis.tgz"))):
        items = " ".join(TAR_ITEMS)
        subprocess.run("tar czf {0}/.wzzAnalysis.tgz.new {1} && gzip -t {0}/.wzzAnalysis.tgz.new && "
                       "mv {0}/.wzzAnalysis.tgz.new {0}/wzzAnalysis.tgz".format(area, items), shell=True, check=True)
    nmc = sum(1 for r in jobs if r[0] < 1000)
    print("samples {0}  jobs {1} (MC {2}, data {3}; {4} of them write two years)  files {5}".format(
        len(per), len(jobs), nmc, len(jobs) - nmc, len(dual), sum(n for n, _ in per.values())))
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
