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

### NanoAODv9 compatibility and physics differences

`wzAnalysis.selectionLL` calls `prepareWZNanoAOD` before booking selections.
Every alias/default is guarded by `HasColumn`; existing v15 columns survive
unchanged. The audit expands the actual selection/weight helper expressions,
including formatted branch names, against `branches_v9.txt`, `branches_v15.txt`
and `only_in_v15.txt`. The required missing columns and treatments are:

| Missing v15 column(s) | v9 treatment | Physics consequence |
|---|---|---|
| `Rho_fixedGridRhoFastjetAll` | Alias `fixedGridRhoFastjetAll` | Naming change; same event density input. |
| `Electron_mvaIso`, `Electron_mvaNoIso` | Alias `Electron_mvaFall17V2Iso`, `Electron_mvaFall17V2noIso` | Legacy electron ID scores; no new classifier inferred. |
| `Electron_mvaIso_WP80`, `Electron_mvaIso_WP90`, `Electron_mvaNoIso_WP80` | Alias corresponding Fall17V2 working points | Retains published legacy working points. |
| `Electron_superclusterEta` | `Electron_eta + Electron_deltaEtaSC` | Reconstructs the supercluster direction. |
| `Electron_promptMVA`, `Muon_promptMVA` | Alias legacy `Electron_mvaTTH`, `Muon_mvaTTH` | **Not equivalent trainings.** For v9, select existing version-12 lepton definitions (electron threshold 0.0 instead of v15 0.8; muon threshold stays 0.7). Fake rates and SFs must be validated for this selection. |
| `Muon_mvaMuID` | Float vector filled with -1 | No continuous-score equivalent; `Muon_mvaId` is not that score. Diagnostic unavailable; no effect on the default WZ ID cuts. |
| `Tau_idDeepTau2018v2p5VSjet`, `Tau_idDeepTau2018v2p5VSe`, `Tau_idDeepTau2018v2p5VSmu` | Decode cumulative v9 `Tau_idDeepTau2017v2p1*` WP bits to ordinal WP indices | Preserves the named Tight working points (6/6/4), **not** the new training. Tau-veto acceptance can differ; do not compare raw bit masks to ordinal cut values. |
| `Jet_chMultiplicity`, `Jet_neMultiplicity` | When absent, use stored `Jet_jetId` tight (bit 2) and tight-lepton-veto (bit 4) decisions | Multiplicities cannot be reconstructed. No fabricated counts; the stored UL jet ID is used. |
| `Jet_btagUParTAK4B` (formatted name in helper) | Use `Jet_btagDeepFlavB` with UL DeepJet T/M/L thresholds for **all Run 2** samples | UParT cannot be emulated. A common tagger across v9 and v15 changes Run 2 b-veto acceptance relative to the previous Run 3-style selection; requires UL DeepJet SFs and efficiencies. |

The un-emulatable quantities are the v15 prompt-MVA/DeepTau/UParT responses,
`Muon_mvaMuID`, and the two jet multiplicities. Their explicit substitutions
above are an executable schema bridge, not a claim of identical efficiencies.
No other branches unique to v15 are consumed by the default WZ graph. In
particular its MET uses PuppiMET branches already present in v9, not PFMET.

Missing HLT paths are replaced with `false` before composing the trigger ORs
and data-PD vetoes; an absent whole group yields false. Run 2 trigger definitions
already exist. The 2016/2017 DoubleEG and SingleElectron labels in `readDASample`
are repaired so the existing exclusive PD trigger logic actually applies.
The provided lists cover UL18 only; pruning is tested for every year code but
trigger efficiencies/menu completeness still need per-era event validation.

### Year/correction audit: production is not yet physics-ready

The catalog and graph can be resolved offline. **The checked-in Run 2 correction
payloads are incomplete/partly Run 3 placeholders, so a full Run 2 job still
needs external calibration work.** In particular, the corrected code requests
UL `deepJet_incl`, absent from the bundled BTV files; initialization will fail
until genuine UL BTV payloads are provided. This is preferable to evaluating
an unrelated Run 3 tagger/SF on the polarized samples. No SF files were changed.

Trivial wiring fixes included with the compatibility change:

- DeepJet selection uses UL tight/medium/loose thresholds:
  APV 0.6502/0.2598/0.0508; postVFP 0.6377/0.2489/0.0480;
  2017 0.7476/0.3040/0.0532; 2018 0.7100/0.2783/0.0490.
  `mysf.h` requests the corresponding `deepJet_comb` / `deepJet_incl` SFs.
- JER no longer requests a separate `SFUncertainty` correction for Run 2;
  UL already supplies nominal/up/down inside its `ScaleFactor` correction.
- 2017 MC's jet-veto map index 0 is initialized (it was a null reference).
- Run 2 jet-ID evaluation selects CHS, and data id 1000 (UL18 SingleMuon A)
  is treated as data when choosing JEC, not as MC.
- 2016 postVFP points to `Summer19UL16_V7_MC`, `Summer20UL16_JRV3_MC`,
  and `Summer19UL16_RunFGH_V7_DATA`, with only the era's data slots loaded.
  Its bundled JSON must be replaced; it is byte-identical to the APV one.

Unresolved calibration/normalization questions, with evidence from local files:

- **BTV:** all four `POG/BTV/Run2-*/btagging.json.gz` files are byte-identical
  to Summer22 preEE (even their DeepJet WP table is 2022). All four
  `data/histoBtagEffSelEtaPt_201*.root` files are byte-identical to the Summer24
  files. Replace both SFs and efficiency maps for UL DeepJet before production.
- **Pileup:** all Run 2 POG LUM JSONs are byte-identical to Summer22 preEE;
  `mysf.h` consequently names a 2022 correction for all Run 2 eras. The default
  event weight uses `data/puWeights_UL_<year>.root`, which does exist and differs
  by year; the alternative JSON PU weight is not a valid Run 2 cross-check.
  Both the JSON and its key need updating together, not just renaming the key.
- **TAU:** all Run 2 DeepTau2018v2p5 SF JSONs are Summer22 copies. The default
  WZ tau veto leaves an empty selected-tau vector, but its v9/v15 veto-efficiency
  difference still needs a study; these files do not certify a v9 tau SF.
- **Leptons:** UL electron/photon SF files and muon files are present. The APV
  and postVFP `electron_mva.json.gz` only contain `2022Re-recoE+PromptFG`, so
  alternate MVA SF working points are invalid for 2016 (the default corrected
  WZ weight uses `Medium` from `electron.json.gz`). Non-correction
  `histoLepSFEtaPt_201*.root` are Summer22 copies. The default `_correction`
  histograms, fake-rate histograms and trigger SFs exist and differ from Run 3,
  but their provenance/working-point compatibility is not established here.
  v9 UL electron momentum calibration must also be checked for double correction
  because v9 stores `Electron_eCorr` and v15 reprocessing differs.
- **JME:** postVFP JEC/JER payload replacement is required as above. Jet-ID JSONs
  are common across eras and their UL validity needs checking. MET XY JSONs
  are Summer22 copies, but those calls are commented out in the default WZ graph.
- **Prefiring:** the Run 2 `L1PreFiringWeight_*` branches exist but the WZ event
  weight does not include them. Adding validated central/variation treatment
  is necessary for Run 2 yield precision; it is outside a schema fallback.
- **Luminosity:** `getLumi` already accepts all four codes, returning
  19.5/16.8/41.5/60.0 fb⁻¹. These rounded legacy numbers are left unchanged;
  confirm the exact certified luminosity for the chosen JSONs and PD coverage.
- **CRAB packaging:** `POG_SUBDIR` already maps all four eras, and their golden
  JSONs exist. No submitter change is needed. Payload size and a complete
  CMSSW/correctionlib event job were not tested here.

Compatibility checks, from the repository root:

```bash
python3 rdf/macros/crab/validate_run2_compat.py --inputs ../run2
# Optional: evaluates adapter expressions using installed ROOT, without data/grid
python3 rdf/macros/crab/validate_run2_compat.py --inputs ../run2 --root
python3 -m py_compile rdf/macros/{utilsAna,utilsNanoAOD,utilsSelection,wzAnalysis}.py rdf/macros/crab/validate_run2*.py
```

The graph audit covers 16 combinations (two schemas × four years × data/MC),
including systematics and weights; it also verifies v15 preservation and
idempotence. The ROOT smoke check evaluates the adapter on synthetic vectors,
including the threshold edge for the DeepTau bit decoder. It is not an
end-to-end analysis test or a validation of the substituted classifiers.
