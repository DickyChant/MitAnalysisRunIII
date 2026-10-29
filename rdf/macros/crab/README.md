# CRAB submission (official CMS samples)

Runs the RDataFrame analyses (default `wzAnalysis`, ntuple mode) on the grid with
CRAB, reading NanoAOD straight from DAS datasets — no skims. Use it for every
sample that exists in DAS. Private samples (not in DAS) keep using the condor
direct mode, `direct/submit_condor.sh`; `submit_crab.py` lists them for you.

## How it works

- `submit_crab.py` reads `<ana>_input_condor_jobs.cfg` and asks `utilsAna.py`
  which skim directories each `(sample, year)` uses (`SwitchSample` for MC,
  `getDATAlist` for data). The directory names are DAS names with `/` → `+`, so
  the DAS dataset list is derived, never maintained by hand. One CRAB task per
  dataset: data samples spanning several PDs/eras (e.g. `1030` = EGamma0–5)
  become several tasks with the same sample ID.
- The sandbox (`build/payload.tgz`) holds the code, `config/`, `data/`, `jsns/`
  (without the large `lumi_*.csv`) and only the `jsonpog-integration` eras of
  the submitted years (same mapping as `subDirName` in `mysf.h`). The script
  aborts if it gets close to CRAB's 120 MB limit.
- `crab_script.sh` (scriptExe; `PSet.py` is a placeholder, cmsRun never runs)
  writes the job's input files into a direct-mode file list and runs
  `<ana>.py --whichJob=-1` with `USE_DIRECT_NANOAOD=1`, after setting
  `doNtuples = True` in its own copy (unless `--no-ntuples`).
- **MC normalization**: the analyses normalise with `genEventSumw` from the
  `Runs` tree of the files they read. A CRAB job only reads a slice, so the
  submitter writes the full dataset's file list into the sandbox and the job
  sets `NORM_FILELIST` (see `getMCnormList` in `utilsAna.py`). Each job then
  opens every file's small `Runs` tree once over xrootd; that cost scales with
  dataset size.
- Outputs per job: `fillhisto_<N>.root` and `ntuple_<N>.root` under
  `<lfn-base>/<tag>/<primary dataset>/<task name>/<timestamp>/0000/`. Before
  stage-out the job checks that both are readable, not empty, and that the
  ntuple has an `events` tree (truncated zero-key outputs were seen in condor
  production). Analysis failures that are only printed (`FAILED ...`, exit 0)
  are turned into job failures.

Exit codes of `crab_script.sh`: 81 bad args, 82 payload, 83 no input files,
84 MC without normalization list, 85 analysis crashed, 86 analysis printed
FAILED, 87 no fillhisto, 88 no ntuple, 89 integrity check.

## Usage

```bash
# CMSSW area: CMSSW_16_0_10 (el9_amd64_gcc13) and CMSSW_15_0_22 are tested; 13_3_1
# fails (its boost rejects muonCrystalBall.h). CRAB ships the submitter's release.
cmsenv
export PYTHONNOUSERSITE=1   # a ~/.local correctionlib breaks the functions.h JIT link
source /cvmfs/cms.cern.ch/common/crab-setup.sh
voms-proxy-init --voms cms --valid 168:00
cd rdf/macros/crab

python3 submit_crab.py --tag=v1 --years=20240 --dry-run         # list tasks, build payload
python3 submit_crab.py --tag=v1 --years=20240 --site=T2_XX_Site  # submit
python3 submit_crab.py --tag=v1 --processes=503,510 --site=T2_XX_Site
python3 submit_crab.py --help                                    # all options

crab status -d crab_projects/crab_<task>
crab resubmit -d crab_projects/crab_<task>
```

The dry run imports `utilsAna` (needs ROOT + correctionlib) but makes no DAS or
CRAB calls. The worker reads input through `--redirector` (default
`root://cms-xrd-global.cern.ch/`).

## Merging

Same as the condor outputs: `hadd` the `ntuple_*.root` of all tasks of a
sample/year (several tasks for multi-PD data), and the `fillhisto_*.root` with
`hadd` too. Each MC job is already weighted to the full-dataset
normalization, so a plain sum is correct.

## Known limitations

- Data years need their golden JSON in `jsns/` (the name is in `getDATAlist`).
  Without it `loadJSON` only warns and the lumi filter then rejects every event.
  The submitter refuses such years.
- Data events that fire several PDs are written once per PD in the ntuple path,
  so de-duplicate on `(run, luminosityBlock, event)` after merging data tasks.
