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

- A file that no site can serve intact (truncated replica, or none reachable) fails every
  job of its MC task, because each job also reads the whole dataset for the normalization.
  Resubmit such a task under a new tag with `--exclude-lfns=<list>`: the files are dropped
  from both the normalization list and the job inputs, so the yield stays consistent.

- Data years need their golden JSON in `jsns/` (the name is in `getDATAlist`).
  Without it `loadJSON` only warns and the lumi filter then rejects every event.
  The submitter refuses such years.
- Data events that fire several PDs are written once per PD in the ntuple path,
  so de-duplicate on `(run, luminosityBlock, eventNum)` after merging data tasks.
  The WZ ntuples carry `run` and `luminosityBlock` from this version on; outputs from
  earlier campaigns (v1/v2) do not.

## Run 2 WZ catalog

Run 2 year codes are `20160` (UL16 preVFP/APV), `20161` (UL16 postVFP),
`20170` (UL17), and `20180` (UL18). New MC definitions use the exact nominal
NanoAODv15/150X datasets in the supplied `run2_survey.out`, except the four
official WZ helicity samples, which use NanoAODv9/106X. No DAS queries were
used to construct this catalog.

| Era | Year | Main block | Overflow block | Preserved DY/DY/TT ids |
|---|---:|---|---|---|
| 2016APV | 20160 | 800–819 | 720–739 | 800 / 801 / 808 |
| 2016 | 20161 | 820–839 | 740–759 | 820 / 821 / 828 |
| 2017 | 20170 | 840–859 | 760–779 | 840 / 841 / 848 |
| 2018 | 20180 | 860–879 | 780–799 | 860 / 861 / 868 |

The 17 free main-block positions are filled first, then overflow offsets 0–18;
overflow offset 19 is spare. All MC ids remain below 1000. The overflow starts
above private Run 2 ids 700–719, avoids 600–643, and leaves existing 9xx test
samples untouched. DY/TT definitions and normalization are unchanged.

[run2_samples.csv](run2_samples.csv) is the complete 144-row report: every id,
era, exact DAS name, cross section in pb, expression, category, source and cfg
status. `SwitchSample` converts pb to fb with `*1000`, for luminosity in fb⁻¹.
The CSV is a review manifest, not a second input to the submitter.

The default cfg enables 30 new MC processes per era. The four helicity samples
and `InclusivePolarization` are **alternative signal productions**, and have
`no` rows: remove `no` in a dedicated polarization cfg to submit them. They use
`kPlotEWKWZ`, like Run 3 WZjj; never add their histograms to nominal WLLJJ or add
the inclusive polarization sample to the four helicities. The lowMLL/lowGPt
Zγ sample is also defined but disabled pending phase-space/overlap validation;
it is not an exact replacement for Run 3 x39. DY/TT are already available and
are not added to the default WZ cfg, which estimates nonprompt from data.

Dataset choices and omissions:

- QCD WZ is the requested POWHEG `WZTo3LNu_mllmin4p0` sample.
- `ZZJJTo4L_TuneCP5_13TeV-madgraph-pythia8` **does** exist in v15 for all eras.
  It overlaps inclusive QCD ZZ and is not added alongside `ZZTo4L`.
- Only nominal M125 Higgs tunes are used; ggH is not minloHJJ. VH covers the
  three H→ZZ samples and `HZJ_HToWWTo2L2Nu_ZTo2L`. These do not exhaust VH non-bb.
- `HWplusJ`/`HWminusJ` H→WW appear only in older v2/v9 campaigns in this survey;
  they are omitted to respect the v15 rule (whose only exception is polarized WZ).
- No WZ interference dataset is in the survey; no x90 equivalent is invented.
- Extensions are not independently normalized/added. Exact exceptional versions
  include UL16 postVFP ZZ `-v2`, APV ggZZ→4τ `-v2`, and APV LL/TL v9 `-v2`.

### Cross-section provenance and open normalization questions

The survey contains no cross sections. Sources checked are the
[CMS Run 2 sample table in Guiang's VBS presentation](https://uaf-10.t2.ucsd.edu/~jguiang/presentations/vbswh/vbswh_02-10-2023.pdf)
(tribosons), the [LHCHXSWG YR4 13 TeV tables](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageAt13TeV)
(Higgs production), and [CMS Open Data cms-72727](https://opendata.cern.ch/record/cms-72727)
(0.01630 pb inclusive polarized WZ, generator cross section). Higgs H→4l uses
BR=0.0002745 for e/μ/τ; ttH non-bb uses BR(bb)=0.5824. The 4LFilter ZH value
includes an extra filter and must not be replaced by an unfiltered ZH×BR blindly.

Other entries carry remembered CMS Run 2 generator/convention values, explicitly
marked `TODO verify xsec` where an exact XSDB/GenXSecAnalyzer record could not be
confirmed. These are provisional inputs, not newly measured generator results.
In particular the LL/LT/TL/TT rates (0.0016/0.0033/0.0033/0.0081 pb) are only
rounded estimates at the inclusive 0.0163 pb scale; their fractions were **not**
verified. Obtain all four generator rates before using polarization yields or
fractions. The disabled cfg rows allow defining/submitting these samples without
silently putting the estimates into a nominal prediction. Also verify WZG decay
filters, Zγ lowMLL overlap, ZH 4LFilter efficiency, HZJ branching fractions, ggZZ
K factors, and whether QCD WZ/ZZ require analysis-specific higher-order factors.
No extra K factor is applied to ggZZ.

### Run 2 data mapping

`getDATAlist` reduces the year code with `year // 10`; the **id** carries the
2016 HIPM split. The cfg therefore uses suffixes 1–5 (B–F HIPM) only with
`20160`, and suffixes 6–8 (F non-HIPM/G/H) only with `20161`. For each suffix,
100x/101x/102x/103x/104x are SingleMuon/DoubleMuon/MuonEG/DoubleEG/SingleElectron.
The typo `10388` for 2016 DoubleEG H is corrected to `1038`.
2017 uses suffixes 1–5, and 2018 uses 0–3 with 103x=EGamma and no separate
SingleElectron. MET is excluded. [run2_data.csv](run2_data.csv) lists every data id/year/DAS mapping.
The 81 data cfg rows expand to 86 datasets
because 2016B has two HIPM processing chunks per PD. They all occur in the
survey. As before, do not reuse an APV data id with the postVFP year code:
`getDATAlist` itself does not enforce that pairing.

### Offline validation

From the repository root (standard-library Python only):

```bash
python3 rdf/macros/crab/validate_run2.py --survey ../run2/run2_survey.out
```

This executes `SwitchSample` and `getDATAlist` with file discovery intercepted,
uses the actual submitter's `DAS_DIR` regex, checks every cfg id/year including
`no` rows, rejects duplicate MC ids and reserved-range additions, and checks
all new MC and Run 2 lepton-data names against the survey verbatim. It does not
establish physics validity or substitute for an event-level CMSSW run.
