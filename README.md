# MitAnalysisRunIII — VBS WZ Analysis Framework

CMS vector boson scattering (VBS) analysis in the WZ channel for LHC Run 3 data, built on ROOT RDataFrame in Python + C++. Covers data from 2022 through 2025 in NanoAOD format (v12 for 2022–2023, v15 for 2024+).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Repository Layout](#repository-layout)
- [Environment Setup](#environment-setup)
- [Quick Start](#quick-start)
- [Skimming](#skimming)
- [Analysis Scripts](#analysis-scripts)
- [Batch Submission (CMS Connect Condor)](#batch-submission-cms-connect-condor)
- [Merging and Post-Processing](#merging-and-post-processing)
- [Plotting](#plotting)
- [MVA Training](#mva-training)
- [Datacard Production](#datacard-production)
- [Year and Sample Encoding](#year-and-sample-encoding)
- [Configuration Reference](#configuration-reference)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Dependency | Purpose |
|---|---|
| ROOT with PyROOT + RDataFrame | Analysis framework (Python 3) |
| correctionlib | POG-approved scale factor evaluation |
| XRootD client | Remote file access to CMS storage |
| VOMS proxy (`voms-proxy-init --voms cms`) | CMS grid authentication |
| HTCondor | Batch submission via CMS Connect |
| Singularity/Apptainer | Containerised job execution on worker nodes |

A standard CMS environment (e.g. `CMSSW_13_3_1`) provides all of the above.

---

## Repository Layout

```
MitAnalysisRunIII/
├── rdf/
│   ├── macros/                  # Primary analysis code
│   │   ├── wzAnalysis.py        # Main WZ VBS analysis
│   │   ├── fakeAnalysis.py      # Fake-rate measurement (supporting)
│   │   ├── triggerAnalysis.py   # Trigger efficiency (supporting)
│   │   ├── puAnalysis.py        # Pileup reweighting (supporting)
│   │   ├── metAnalysis.py       # MET corrections (supporting)
│   │   ├── genAnalysis.py       # Generator-level studies
│   │   ├── functions.h          # C++ helpers (JIT-compiled by ROOT)
│   │   ├── mysf.h               # correctionlib scale-factor interface
│   │   ├── utilsAna.py          # Sample lookup, file grouping, luminosity
│   │   ├── utilsSelection.py    # RDataFrame selection/define chains
│   │   ├── utilsCategory.py     # Plot category enum
│   │   ├── utilsMVA.py          # MVA variable redefinitions for systematics
│   │   ├── tmva_helper_xml.{h,py}  # TMVA XML inference on RDataFrame
│   │   ├── config/selection.json    # Lepton WPs, triggers, VBS cuts
│   │   ├── data/                # Reference histograms (fake rates, SFs, etc.)
│   │   ├── jsns/                # Golden JSON lumi files
│   │   ├── jsonpog-integration/ # POG correction JSONs (BTV, EGM, JME, LUM, MUO, TAU)
│   │   ├── weights_mva/         # BDT weight files (initially empty)
│   │   ├── submit_condor.sh     # CMS Connect Condor submission
│   │   ├── analysis_singularity_condor.sh  # Singularity wrapper
│   │   ├── analysis_condor.sh   # Worker-node environment setup
│   │   ├── analysis_runner.sh   # Generic job runner
│   │   ├── collect_files_for_job.py  # Resolves file lists for transfer
│   │   ├── check_skim_completeness.py  # Pre-submission skim validation
│   │   ├── direct/                 # Direct NanoAOD mode (no skims needed)
│   │   │   ├── submit_condor.sh    # Condor submission (XRootD streaming)
│   │   │   ├── resolve_sample_files.py  # Generate XRootD file lists
│   │   │   ├── filelists/          # Pre-built XRootD file lists
│   │   │   └── README.md           # Direct mode instructions
│   │   ├── *_input_condor_jobs.cfg   # Per-analysis sample lists
│   │   ├── mergeHistograms.py   # Merge per-job ROOT outputs
│   │   ├── computeYields.py     # Yield tables from merged histograms
│   │   ├── makeAnalysisFolders.sh   # Create datacard working areas
│   │   ├── checkJobs.sh         # Monitor job completion
│   │   └── ...
│   ├── skimming/                # NanoAOD skimming pipeline
│   │   ├── skim.py              # Skimming script
│   │   ├── skim_condor.sh       # Condor submission for skimming
│   │   ├── functions_skim.h     # C++ skim-level helpers
│   │   ├── skim_input_samples_*_fromDAS.cfg  # DAS dataset lists
│   │   └── ...
│   ├── makePlots/               # Plotting
│   │   ├── finalPlot.C          # CMS-style plot macro
│   │   ├── makePlots.sh         # Driver script
│   │   ├── common.h             # Plot category definitions
│   │   ├── merge_histograms_year.sh  # Merge across years (→ "2027")
│   │   └── ...
│   └── mva_training/            # BDT training for VBS tagging
│       ├── ewkvbsMVA.C          # TMVA BDT training macro
│       └── make_mva_training_ntuples.sh  # Ntuple production driver
```

---

## Environment Setup

### 1. Configure paths

The framework uses environment variables with sensible defaults. Override them if your storage layout differs:

```bash
# Where skimmed NanoAOD files live (organised by skim type: 1l/, 2l/, 3l/, met/)
export SKIM_BASE_DIR="/home/scratch/$USER/skims_submit"

# Scratch area for special/test samples
export SCRATCH_SAMPLE_DIR="/home/scratch/$USER/samples"

# Output directory for analysis histograms
export ANALYSIS_OUTPUT_DIR="/home/scratch/$USER/analysis"

# Output directory for skimming
export SKIM_OUTPUT_DIR="/home/scratch/$USER/skims"

# XRootD redirector (leave empty for local file access)
export XRD_SERVER=""
```

Defaults are defined in `rdf/macros/utilsAna.py`.

### 2. Ensure VOMS proxy

```bash
voms-proxy-init --voms cms --valid 168:00
```

### 3. Verify file access

```bash
cd rdf/macros
python3 -c "from utilsAna import SwitchSample; print(SwitchSample(179, '3l', 20220)[0])"
```

This should print the path to skimmed files for WZ MadGraph, era 2022CD. If empty, check `SKIM_BASE_DIR`.

---

## Quick Start

All analysis commands run from `rdf/macros/`. There is no build step — C++ headers are JIT-compiled by ROOT at runtime.

### Run a single job interactively

```bash
cd rdf/macros
python3 wzAnalysis.py --process=179 --year=20220 --whichJob=0
```

| Argument | Description |
|---|---|
| `--process` | Sample ID from `*_input_condor_jobs.cfg` |
| `--year` | Year-era code (see [Year Encoding](#year-and-sample-encoding)) |
| `--whichJob` | File group index (0-based), or `-1` for all files |

Output: `fillhisto_wzAnalysis_sample179_year20220_job0.root`

### Run all files for a sample

```bash
python3 wzAnalysis.py --process=179 --year=20220 --whichJob=-1
```

---

## Skimming

**Skimming is a prerequisite for standard mode.** The analysis code reads pre-skimmed NanoAOD files by default. Skimming reduces NanoAOD to manageable size by applying loose trigger + preselection. Output is split into skim types used by different analyses:

> **Alternative: Direct NanoAOD mode** — Skip skimming entirely. Set `USE_DIRECT_NANOAOD=1` and pre-generate XRootD file lists with `direct/resolve_sample_files.py`. Worker nodes read raw NanoAOD from the CMS grid via XRootD streaming. See `rdf/macros/direct/README.md`.

| Skim type | Directory | Used by |
|---|---|---|
| `1l` | `$SKIM_BASE_DIR/1l/` | fakeAnalysis |
| `2l` | `$SKIM_BASE_DIR/2l/` | triggerAnalysis, puAnalysis |
| `3l` | `$SKIM_BASE_DIR/3l/` | wzAnalysis |
| `met` | `$SKIM_BASE_DIR/met/` | metAnalysis |

On CMS Connect, Condor worker nodes **do not have direct filesystem access** to the skim files. Instead, `submit_condor.sh` resolves file paths at submission time and includes them in `transfer_input_files`, so Condor ships them to worker nodes. This means **all skim files must be present on the submission node's local storage before submitting analysis jobs.**

### Submit skimming jobs

```bash
cd rdf/skimming
./skim_condor.sh <YEAR>
```

Where `<YEAR>` selects the config file `skim_input_samples_<YEAR>_fromDAS.cfg` (e.g. `2022a`, `2023b`, `2024d`).

### Run skimming interactively

```bash
python3 skim.py --whichSample=0 --whichJob=0 --group=5 \
  --inputSamplesCfg=skim_input_samples_2022a_fromDAS.cfg \
  --inputFilesCfg=skim_inputfiles_2022a
```

### Check for missing skim files (skimming-level)

```bash
python3 check_missing_skim_files.py
```

This checks whether all expected skim output files exist in `$SKIM_OUTPUT_DIR`.

### Validate skims for analysis (pre-submission check)

Before submitting analysis jobs, verify that the skims needed by each analysis are complete:

```bash
cd rdf/macros

# Check skims for a specific analysis
python3 check_skim_completeness.py --ana=wz
python3 check_skim_completeness.py --ana=fake

# Check all analyses at once
python3 check_skim_completeness.py --ana=all

# Verbose mode (shows individual file paths)
python3 check_skim_completeness.py --ana=wz --verbose
```

This resolves the same file paths that `submit_condor.sh` will use and reports any missing or empty files. A non-zero exit code means some skims are missing. The submission script also runs this check automatically and prompts for confirmation if problems are found.

### Create a new skim folder structure

```bash
./make_newskimfolder.sh
```

---

## Analysis Scripts

### WZ analysis (main)

```bash
python3 wzAnalysis.py --process=179 --year=20220 --whichJob=-1
```

The WZ analysis flow:
1. Trigger selection (`selectionTrigger2L`)
2. Lepton ID/isolation (`selectionElMu`) with working points from `config/selection.json`
3. Require exactly 3 leptons (Z candidate + W lepton)
4. Tau veto, photon selection, jet/MET cuts
5. VBS jet pair selection (highest m_jj pair with pt > 50, |eta| < 4.9)
6. Compute VBS discriminant variables (m_jj, Delta_eta_jj, zeppenfeld, etc.)
7. Apply event weights (pileup, lepton SF, b-tag, fake rates, EWK corrections)
8. Fill histograms in signal/control regions; optionally save training ntuples

### Supporting analyses

These produce inputs needed by the WZ analysis (fake rates, trigger SFs, pileup weights, MET corrections). They must run **before** the WZ analysis.

| Script | Code | Skim type | Purpose |
|---|---|---|---|
| `fakeAnalysis.py` | 5 | 1l | Fake-rate measurement |
| `triggerAnalysis.py` | 6 | 2l | Trigger efficiency |
| `puAnalysis.py` | 9 | 2l | Pileup reweighting |
| `metAnalysis.py` | 7 | met | MET corrections |

### Other utilities

| Script | Purpose |
|---|---|
| `genAnalysis.py` | Generator-level comparisons (EWK NLO, QCD NLO, etc.) |
| `lumiAnalysis.py` | Luminosity cross-checks |
| `checkFilesAnalysis.py` | Verify file availability |

---

## Batch Submission (CMS Connect Condor)

Jobs run on CMS Connect via Condor. There are **two submission modes**:

| Mode | Script | Data access | Needs skims? |
|---|---|---|---|
| **Standard** | `submit_condor.sh` | File transfer (skim files shipped to worker) | Yes |
| **Direct** | `direct/submit_condor.sh` | XRootD streaming (reads CMS grid directly) | No |

**Standard mode**: The submission script creates a tarball of analysis code, resolves input file lists, and submits jobs inside Singularity containers. It automatically runs `check_skim_completeness.py` before submitting.

**Direct mode**: No skim files needed. Workers read raw NanoAOD directly from the CMS grid via XRootD. See `rdf/macros/direct/README.md` for setup. Much lighter jobs (just code tarball, no data transfer), but slightly slower per-job due to network I/O.

### Two-round workflow

**Round 1** — Supporting analyses (independent, submit in any order):
```bash
cd rdf/macros
./submit_condor.sh 5       # fakeAnalysis
./submit_condor.sh 6       # triggerAnalysis
./submit_condor.sh 7       # metAnalysis
./submit_condor.sh 9       # puAnalysis
```

Wait for Round 1 to complete, then merge results (see [Merging](#merging-and-post-processing)).

**Round 2** — WZ analysis (depends on Round 1 outputs):
```bash
./submit_condor.sh 1       # wzAnalysis
```

### Submission syntax

```bash
./submit_condor.sh <anaCode> [condorJob] [group]
```

| Parameter | Default | Description |
|---|---|---|
| `anaCode` | (required) | 1=wz, 5=fake, 6=trigger, 7=met, 9=pu |
| `condorJob` | 1001 | Job ID prefix — appears in output filenames |
| `group` | 1 (wz) or 9 (others) | Number of file groups per sample |

Examples:
```bash
./submit_condor.sh 1          # WZ, condorJob=1001, group=1
./submit_condor.sh 1 1001 2   # WZ, condorJob=1001, group=2 (more jobs per sample)
./submit_condor.sh 5 1001 9   # fake, condorJob=1001, group=9
```

### Direct mode submission (no skims)

```bash
cd direct

# One-time: generate XRootD file lists
python3 resolve_sample_files.py --config=../wzAnalysis_input_condor_jobs.cfg

# Submit
./submit_condor.sh 1 1001
```

### Job configuration files

Each analysis reads a sample list from `<analysis>_input_condor_jobs.cfg`:
```
179 20220         # WZ MadGraph, 2022CD — will be submitted
183 20220         # WZ data, 2022CD
579 20250 no      # WZ MadGraph, 2025 — skipped (marked 'no')
```

Format: `<sampleID> <yearCode> [no]`

To regenerate config files:
```bash
python3 remake_Analysis_input_condor_jobs.py --ana=wz
```

### Monitoring jobs

```bash
# Watch job queue
condor_q -submitter $USER

# Check completion
./checkJobs.sh wz 1001 20220

# Check logs
tail -f logs/wzAnalysis_1001_179_20220_0.out
grep FAILED logs/*.out
grep -c DONE logs/*.out
```

### Resubmitting failed jobs

```bash
# Identify failures
grep FAILED logs/*.out

# Re-run interactively
python3 wzAnalysis.py --process=179 --year=20220 --whichJob=0

# Or resubmit via condor
./submit_condor.sh 1 1001
```

### Running all jobs interactively (without Condor)

```bash
./prepare_jobs_run_interactive.sh 1    # generates nohup commands for wzAnalysis
```

This writes a script file `lll_wzAnalysis` with one `nohup python3 wzAnalysis.py ...` command per sample.

### Execution chain on worker nodes

```
submit_condor.sh  →  Condor  →  analysis_singularity_condor.sh
                                    → analysis_condor.sh  (sets up CMSSW, extracts tarball)
                                        → analysis_runner.sh  (runs python3 <analysis>.py)
```

---

## Merging and Post-Processing

The analysis produces two types of output per job, and they require **different merging tools**:

| Output type | Files | Merging tool | Contents |
|---|---|---|---|
| **Histograms** | `fillhisto_wzAnalysis1001_sample*_year*_job*.root` | `mergeHistograms.py` | TH1D/TH2D histograms for yields, plots, datacards |
| **Ntuples** | `ntupleWZAna_sample*_year*_job*.root` | `hadd` (ROOT) | Flat TTree (`events`) with 51 branches for XGBoost/BDT training |

Ntuples are only produced when `doNtuples = True` in `wzAnalysis.py`.

### Merge per-job histograms

After batch jobs complete, merge output ROOT files per year:

```bash
python3 mergeHistograms.py --path=fillhisto_wzAnalysis1001 --year=20220 --output=anaWZ
python3 mergeHistograms.py --path=fillhisto_wzAnalysis1001 --year=20221 --output=anaWZ
python3 mergeHistograms.py --path=fillhisto_wzAnalysis1001 --year=20230 --output=anaWZ
python3 mergeHistograms.py --path=fillhisto_wzAnalysis1001 --year=20231 --output=anaWZ
python3 mergeHistograms.py --path=fillhisto_wzAnalysis1001 --year=20240 --output=anaWZ
```

Output goes to `anaWZ/fillhisto_wzAnalysis1001_<year>_<histoIdx>.root`.

> **Note**: `mergeHistograms.py` only handles histograms (TH1D, TH2D). It does **not** merge ntuples/TTrees. For ntuples, use `hadd` (see below).

### Merge per-job ntuples (for training)

If you ran with `doNtuples = True` in batch mode (`whichJob >= 0`), each job produces a separate ntuple file. Merge them with `hadd`:

```bash
# Merge all ntuple jobs for a single sample
hadd -f ntupleWZAna_sample179_year20220.root ntupleWZAna_sample179_year20220_job*.root

# Or merge ALL samples+years into one training file
hadd -f ntupleWZAna_year2027.root ntupleWZAna_*.root
```

For **XGBoost training**, you don't strictly need to merge — you can load multiple files directly:

```python
import uproot
import numpy as np

# Load multiple ntuple files without merging
files = glob.glob("ntupleWZAna_sample*_year*_job*.root")
arrays = [uproot.open(f)["events"].arrays(library="np") for f in files]
# Or use ROOT.TChain:
chain = ROOT.TChain("events")
for f in files: chain.Add(f)
```

### Merge across years (Run 3 combination)

```bash
cd rdf/makePlots
./merge_histograms_year.sh wzAnalysis 1001 2027
```

Year code `2027` is a special convention meaning "all Run 3 eras combined" (2022+2023+2024).

### Compute yield tables

```bash
python3 computeYields.py --path=fillhisto_wzAnalysis1001 --year=2022 --output=anaWZ
```

Prints a LaTeX-formatted yield table for signal and background categories.

---

## Plotting

```bash
cd rdf/makePlots
./makePlots.sh wz 0 20220
```

| Argument | Description |
|---|---|
| 1st | Analysis name: `wz`, `fake`, `trigger`, etc. |
| 2nd | Apply scaling: `0` = no, `1` = yes |
| 3rd | Year code |

This calls `finalPlot.C` (CMS-style ROOT macro) for each histogram type defined in the script. Output is PNG/PDF plots.

---

## MVA Training

The VBS EWK WZ vs QCD WZ BDT discriminant uses 15+ kinematic variables. Training uses TMVA with ntuples from the WZ analysis.

### Step 1: Produce training ntuples

**Option A: Interactive (from login node)** — uses `make_mva_training_ntuples.sh`:
```bash
cd rdf/mva_training
./make_mva_training_ntuples.sh 1    # runs all samples with --whichJob=-1 (all files at once)
# Wait for all nohup jobs to finish, then:
./make_mva_training_ntuples.sh 10   # restores wzAnalysis.py + hadd → ntupleWZAna_year2027.root
```

This runs each sample as one job (`--whichJob=-1`), so each produces a single ntuple file. The final `hadd` merges all samples into one file.

**Option B: Batch (Condor)** — for larger datasets or CMS Connect:
1. Set `doNtuples = True` and `useFR = 0` in `wzAnalysis.py`
2. Submit via `./submit_condor.sh 1` (or `direct/submit_condor.sh 1` for direct mode)
3. Each job produces `ntupleWZAna_sample{id}_year{year}_job{N}.root`
4. After all jobs complete, merge with `hadd`:
```bash
hadd -f ntupleWZAna_year2027.root ntupleWZAna_*.root
```
5. Restore `wzAnalysis.py` (`doNtuples = False`, `useFR = 1`)

> **For XGBoost**: You can skip the `hadd` step and load multiple files directly with `uproot` or `ROOT.TChain`. This is often more convenient for Python-based training.

### Step 2: Train the BDT

```bash
root -q -b -l ewkvbsMVA.C
```

- Signal: EW WZ events (`theCat == 8`)
- Background: QCD WZ events (`theCat == 9`)
- VBS jet cuts: `vbs_ptj1 > 50 && vbs_ptj2 > 50`
- Train/test split: `eventNum % 10 < 5` for training
- Output: `weights_mva/bdt_BDTG_vbfinc_v0.weights.xml`

### Ntuple contents

The training ntuples contain 51 branches:

| Group | Variables |
|---|---|
| Event | `eventNum`, `weight`, `theCat`, `ngood_jets` |
| VBS kinematics | `vbs_mjj`, `vbs_ptjj`, `vbs_detajj`, `vbs_dphijj`, `vbs_zepvv`, `vbs_zepmax`, `vbs_sumHT`, `vbs_ptvv`, `vbs_pttot`, `vbs_detavvj1`, `vbs_detavvj2`, `vbs_ptbalance` |
| VBS jet p4 + tagger | `vbs_ptj1/j2`, `vbs_etaj1/j2`, `vbs_phij1/j2`, `vbs_massj1/j2`, `vbs_btagj1/j2` |
| Z leptons (p4 + flavor) | `ptl1Z/l2Z`, `etal1Z/l2Z`, `phil1Z/l2Z`, `massl1Z/l2Z`, `flavorl1Z/l2Z` |
| W lepton (p4 + flavor) | `ptlW`, `etalW_signed`, `philW`, `masslW`, `flavorlW` |
| MET | `PuppiMET_ptDef`, `PuppiMET_phiDef` |
| Additional | `mll` (Z mass), `m3l`, `mtW`, `TriLepton_flavor` |

Lepton flavor encoding: `0` = muon, `1` = electron. `TriLepton_flavor` encodes the 3-lepton combination: `(nMuons + 3*nElectrons - 3) / 2`.

### MVA loading in the analysis

When `weights_mva/bdt_BDTG_vbfinc_v0.weights.xml` exists and `doNtuples = False`, the BDT is loaded and evaluated per event. When the weights file is absent or `doNtuples = True`, a dummy `bdt_vbfinc = 0` is used (the analysis still runs, just without MVA categorisation).

---

## Datacard Production

For statistical inference with Combine:

### 1. Create analysis folder copies with different binning strategies

```bash
cd rdf/macros
./makeAnalysisFolders.sh 1
```

This creates 6 copies of the analysis code (`macros1001`–`macros1006`), each with a different `makeDataCards` setting:
- `macros1001`: BDT 2D (default, `makeDataCards=4`)
- `macros1002`: 3D (`makeDataCards=3`)
- `macros1003`: BDT 1D (`makeDataCards=5`)
- `macros1004`: m_jj (`makeDataCards=6`)
- `macros1005`: m_jj differential (`makeDataCards=7`)
- `macros1006`: lepton flavor (`makeDataCards=2`)

### 2. Run the WZ analysis in each folder

Submit jobs from each `macros100X/` folder with `./submit_condor.sh 1`.

### 3. Generate datacards

```bash
root -q -b -l makeVVDataCards.C'(0, 0, "anaWZ", "wzAnalysis1001", 20220)'
```

---

## Year and Sample Encoding

### Year codes

| Code | Era | Luminosity (fb⁻¹) | NanoAOD |
|---|---|---|---|
| `20220` | 2022 CD | 8.1 | v12 |
| `20221` | 2022 EFG | 26.7 | v12 |
| `20230` | 2023 BCD | 18.1 | v12 |
| `20231` | 2023 D | 9.7 | v12 |
| `20240` | 2024 BCDEFGHI | 109.6 | v15 |
| `20250` | 2025 | 105.0 | v15 |
| `2027` | All Run 3 combined | — | — |

### Sample ID conventions

IDs are integers in `*_input_condor_jobs.cfg`. The hundreds digit encodes the era:

| Prefix | Era |
|---|---|
| 1xx | 20220 |
| 2xx | 20221 |
| 3xx | 20230 |
| 4xx | 20231 |
| 5xx | 20240 |

IDs ≥ 1000 are data samples. Key MC sample IDs:

| ID (per era) | Process |
|---|---|
| x03 | WZ (Powheg) |
| x08 | WZ (MadGraph, EWK) |
| x49 | WZ (MadGraph, QCD) |
| x78, x79 | WZ data (Muon, EGamma) |
| x14–x21 | Top backgrounds (ttbar, tW, etc.) |
| x11–x13 | DY |

---

## Configuration Reference

### `config/selection.json`

Central JSON defining all analysis selections, versioned by NanoAOD version (v12 vs v15):

- **Lepton ID**: `FAKE_MU`, `TIGHT_MU0`–`MU8`, `FAKE_EL`, `TIGHT_EL0`–`EL9`
- **Triggers**: per-year dilepton trigger paths
- **VBS selection**: `VBSSEL`, `VBSQCDSEL` jet pair requirements
- **Photon criteria**: barrel and endcap photon ID

### Plot categories (`utilsCategory.py`)

| Category | Index | Description |
|---|---|---|
| `kPlotData` | 0 | Observed data |
| `kPlotqqWW` | 1 | qq → WW |
| `kPlotggWW` | 2 | gg → WW |
| `kPlotTT` | 3 | ttbar |
| `kPlotTW` | 4 | Single-top tW |
| `kPlotDY` | 5 | Drell-Yan |
| `kPlotEWKSSWW` | 6 | EWK same-sign WW |
| `kPlotQCDSSWW` | 7 | QCD same-sign WW |
| `kPlotEWKWZ` | 8 | **EWK WZ (signal)** |
| `kPlotWZ` | 9 | **QCD WZ** |
| `kPlotZZ` | 10 | ZZ |
| `kPlotNonPrompt` | 11 | Non-prompt leptons |
| `kPlotVVV` | 12 | Triboson |
| `kPlotTVX` | 13 | ttV, tZq |
| `kPlotVG` | 14 | V+gamma |
| `kPlotHiggs` | 15 | Higgs |
| `kPlotWS` | 16 | Wrong-sign |
| `kPlotOther` | 17 | Other |

---

## Environment Variables

| Variable | Default | Used by |
|---|---|---|
| `SKIM_BASE_DIR` | `/home/scratch/stqian/wz_guillermo/skims_submit` | `utilsAna.py` — base path for skimmed files |
| `SCRATCH_SAMPLE_DIR` | `/home/scratch/stqian/samples` | `utilsAna.py` — special/test sample storage |
| `XRD_SERVER` | `""` (empty = local) | `utilsAna.py` — XRootD redirector for remote access |
| `ANALYSIS_OUTPUT_DIR` | `/home/scratch/$USER/analysis` | `makeAnalysisFolders.sh` |
| `SKIM_OUTPUT_DIR` | `/home/scratch/$USER/skims` | `skim_condor.sh`, `skim.py` |

---

## Troubleshooting

### No input files found

```bash
# Test file resolution
python3 -c "from utilsAna import SwitchSample; print(SwitchSample(179, '3l', 20220)[0])"

# Test file collection for Condor
python3 collect_files_for_job.py 179 20220 0 3l 2
```

If empty, check `SKIM_BASE_DIR` and verify skim files exist at `$SKIM_BASE_DIR/3l/<sampleName>/`.

### Job fails on worker node

```bash
cat logs/wzAnalysis_1001_179_20220_0.error
cat logs/wzAnalysis_1001_179_20220_0.out
```

Common issues:
- **Missing VOMS proxy**: Renew with `voms-proxy-init --voms cms --valid 168:00`
- **File transfer failed**: Check that `collect_files_for_job.py` returns valid paths
- **Missing data files**: Ensure `data/` directory has all required histograms for the year
- **Disk space**: Increase `RequestDisk` in `submit_condor.sh` if jobs run out of space

### ROOT JIT compilation errors

`functions.h` and `mysf.h` are compiled at runtime by ROOT. If you see compilation errors:
- Check that `correctionlib` is available: `python3 -c "import correctionlib"`
- Ensure you're in a CMSSW environment: `cmsenv`

### Adding a new year/era

1. Add skim input configs in `rdf/skimming/skim_input_samples_<year>_fromDAS.cfg`
2. Add golden JSON to `rdf/macros/jsns/`
3. Update luminosity in `utilsAna.py` (`getLumi()`)
4. Add POG corrections to `jsonpog-integration/`
5. Add reference histograms (fake rates, SFs, pileup weights) to `data/`
6. Add sample entries to `*_input_condor_jobs.cfg` files
7. If NanoAOD version changes, add new lepton/trigger definitions to `config/selection.json`
