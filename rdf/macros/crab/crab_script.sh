#!/bin/bash

# CRAB scriptExe for the RDataFrame analyses (see crab/README.md).
#
# Runs inside the CMSSW environment CRAB sets up from the submitter's release.
# The input files CRAB assigned to this job come from PSet.py; they are written
# to a direct-mode file list and the analysis runs on all of them (whichJob=-1).
#
# Arguments (CRAB passes JobType.scriptArgs as key=value; the first argument is
# the CRAB job number):
#   process=<sample ID>  year=<year code>  ana=<wzAnalysis|...>  ntuples=<0|1>
#   normlist=<file in payload, MC only>    redirector=<root://host/>

set -o pipefail

jobNumber=$1
shift
for kv in "$@"; do
  case "$kv" in
    process=*)    process=${kv#process=} ;;
    year=*)       year=${kv#year=} ;;
    ana=*)        ana=${kv#ana=} ;;
    ntuples=*)    ntuples=${kv#ntuples=} ;;
    normlist=*)   normlist=${kv#normlist=} ;;
    redirector=*) redirector=${kv#redirector=} ;;
  esac
done
ana=${ana:-wzAnalysis}
ntuples=${ntuples:-1}
redirector=${redirector:-root://cms-xrd-global.cern.ch/}

echo "crab_script: job=${jobNumber} process=${process} year=${year} ana=${ana} ntuples=${ntuples}"
echo "hostname: $(hostname)  CMSSW: ${CMSSW_VERSION}  python3: $(python3 --version 2>&1)"

# Minimal job report: CRAB requires one, cmsRun never runs.
writeFJR() {
  cat > FrameworkJobReport.xml << EOF
<FrameworkJobReport>
<ReadBranches>
</ReadBranches>
<PerformanceReport>
  <PerformanceSummary Metric="StorageStatistics">
    <Metric Name="Parameter-untracked-bool-enabled" Value="true"/>
    <Metric Name="Parameter-untracked-bool-stats" Value="true"/>
    <Metric Name="Parameter-untracked-string-cacheHint" Value="application-only"/>
    <Metric Name="Parameter-untracked-string-readHint" Value="auto-detect"/>
    <Metric Name="ROOT-tfile-read-totalMegabytes" Value="0"/>
    <Metric Name="ROOT-tfile-write-totalMegabytes" Value="0"/>
  </PerformanceSummary>
</PerformanceReport>
<GeneratorInfo>
</GeneratorInfo>
</FrameworkJobReport>
EOF
}

fail() {
  echo "crab_script FAILED: $2"
  writeFJR
  exit $1
}

[ -n "${process}" ] && [ -n "${year}" ] || fail 81 "process and year are required"

tar xzf payload.tgz || fail 82 "cannot extract payload.tgz"

export XRD_NETWORKSTACK=IPv4
export XRD_REQUESTTIMEOUT=600
export XRD_REDIRECTLIMIT=255
export XRD_CONNECTIONRETRY=4
export XRD_STREAMTIMEOUT=120

# Input files assigned by CRAB -> direct-mode file list
mkdir -p crab_filelists
if [ ${process} -lt 1000 ]; then
  listName="crab_filelists/${process}.txt"
else
  listName="crab_filelists/data_${process}_$((year / 10)).txt"
fi
# Prefer the site's own copy (CRAB runs jobs where the data are), fall back to the
# redirector: the global redirector sometimes sends the open to a remote site that
# times out (exit 5 for ~7% of the v1 jobs, with the file on disk at the running site).
# The local PFN prefix comes from the site-local config via edmFileUtil.
python3 -c "
import PSet
for f in PSet.process.source.fileNames:
    print(f)
" > crab_lfns.txt || fail 83 "cannot read input files from PSet.py"
[ -s crab_lfns.txt ] || fail 83 "no input files in PSet.py"
firstLFN=$(grep -m1 '^/store/' crab_lfns.txt)
localPrefix=""
if [ -n "${firstLFN}" ]; then
  firstPFN=$(edmFileUtil -d ${firstLFN} 2>/dev/null | tail -1)
  case "${firstPFN}" in
    *"${firstLFN}") localPrefix=${firstPFN%"${firstLFN}"} ;;
  esac
fi
echo "site-local prefix: '${localPrefix}'"

# resolveLFN <lfn>: local PFN if the site has the file, else the redirector URL
resolveLFN() {
  local lfn=$1
  case "${lfn}" in
    root://*) echo "${lfn}"; return ;;
  esac
  if [ -n "${localPrefix}" ]; then
    case "${localPrefix}" in
      root://*)
        local host=${localPrefix#root://}; host=${host%%/*}
        local path=${localPrefix#root://${host}}${lfn}
        if timeout 30 xrdfs ${host} stat ${path} > /dev/null 2>&1; then
          echo "${localPrefix}${lfn}"; return
        fi ;;
      *)
        local pfn=${localPrefix#file:}${lfn}
        if [ -r "${pfn}" ]; then echo "${pfn}"; return; fi ;;
    esac
  fi
  echo "${redirector}${lfn}"
}

while read lfn; do resolveLFN ${lfn}; done < crab_lfns.txt > ${listName}
echo "Input files for this job:"
cat ${listName}
[ -s ${listName} ] || fail 83 "no input files in PSet.py"

# use the release's python packages only (a user-site correctionlib breaks the JIT link)
export PYTHONNOUSERSITE=1
export USE_DIRECT_NANOAOD=1
export FILELIST_DIR=crab_filelists
if [ ${process} -lt 1000 ]; then
  [ -n "${normlist}" ] && [ -s "${normlist}" ] || fail 84 "MC job without normalization list (${normlist})"
  # the list holds bare LFNs from DAS; resolve them like the job's own input files
  while read lfn; do resolveLFN ${lfn}; done < ${normlist} > crab_normlist_xrd.txt
  echo "Normalization files: $(wc -l < crab_normlist_xrd.txt), site-local: $(grep -c -v "^${redirector}" crab_normlist_xrd.txt)"
  export NORM_FILELIST=$(pwd)/crab_normlist_xrd.txt
fi

if [ "${ntuples}" = "1" ]; then
  sed -i 's/^doNtuples = False/doNtuples = True/' ${ana}.py
fi
grep -n "^doNtuples" ${ana}.py

time python3 ${ana}.py --process=${process} --year=${year} --whichJob=-1 2>&1 | tee analysis.log
status=$?
[ ${status} -eq 0 ] || fail 85 "${ana}.py exited with ${status}"
# the analyses catch exceptions in __main__ and only print FAILED
grep -q "^FAILED" analysis.log && fail 86 "${ana}.py reported $(grep '^FAILED' analysis.log | head -1)"

# Fixed output names (CRAB appends _<jobNumber>); validate before stage-out
histoFile="fillhisto_${ana}_sample${process}_year${year}_job-1.root"
[ -f ${histoFile} ] || fail 87 "missing ${histoFile}"
mv ${histoFile} fillhisto.root

if [ "${ntuples}" = "1" ]; then
  ntupleFile=$(ls ntuple*Ana_sample${process}_year${year}_job-1.root 2>/dev/null | head -1)
  [ -n "${ntupleFile}" ] || fail 88 "no ntuple written for sample ${process} year ${year}"
  mv ${ntupleFile} ntuple.root
fi

# Truncated outputs have been seen in production (zero keys after a crash at
# finalisation): require readable files, and an events tree in the ntuple.
python3 - "${ntuples}" << 'EOF' || fail 89 "output integrity check failed"
import sys, ROOT
files = ["fillhisto.root"] + (["ntuple.root"] if sys.argv[1] == "1" else [])
for name in files:
    f = ROOT.TFile.Open(name)
    if not f or f.IsZombie() or f.TestBit(ROOT.TFile.kRecovered) or f.GetNkeys() == 0:
        sys.exit("bad output file: " + name)
    if name == "ntuple.root":
        t = f.Get("events")
        if not t:
            sys.exit("ntuple.root has no events tree")
        print("ntuple.root: {0} entries".format(t.GetEntries()))
    f.Close()
EOF

writeFJR
ls -l
echo "crab_script DONE"
