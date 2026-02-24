# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MitAnalysisRunIII is a CMS particle physics analysis framework for LHC Run 3 data, focused on VBS-WZ (vector boson scattering in the WZ channel) using ROOT RDataFrame in Python+C++. Data spans 2022-2025 eras in NanoAOD format (v12 for ≤2023, v15 for ≥2024).

## Repository Structure

- **`rdf/macros/`** — Primary analysis code. The main analysis is `wzAnalysis.py`, with supporting analyses for fake rates (`fakeAnalysis.py`), triggers (`triggerAnalysis.py`), pileup (`puAnalysis.py`), MET (`metAnalysis.py`), and generator-level studies (`genAnalysis.py`). Core C++ functions live in `functions.h`, scale factors in `mysf.h`.
- **`rdf/skimming/`** — Data reduction pipeline. `skim.py` reads NanoAOD from XRootD and applies loose preselection. Input sample lists are in `skim_inputfiles_*` directories organized by year/era.
- **`rdf/makePlots/`** — Plotting. `finalPlot.C` generates CMS-style plots, driven by `makePlots.sh`.
- **`rdf/mva_training/`** — BDT training for VBS jet tagging (`ewkvbsMVA.C`).

## Data Flow and Prerequisites

**Skimming → Supporting Analyses → WZ Analysis → Plotting/Datacards**

1. **Skimming is required first.** All analyses read pre-skimmed NanoAOD, not raw CMS data. Skims live in `$SKIM_BASE_DIR/{1l,2l,3l,met}/` organized by dataset name.
2. **Supporting analyses (Round 1)** produce fake rates, trigger SFs, pileup weights, MET corrections that the WZ analysis needs. These are independent of each other.
3. **WZ analysis (Round 2)** depends on Round 1 outputs stored in `rdf/macros/data/`.
4. On **CMS Connect**, Condor worker nodes have NO local filesystem access to skims. Files are transferred via `transfer_input_files`. The submission script resolves paths at submit time.

## Environment Variables

These configure where the framework looks for data. Override them for your storage layout:

```bash
export SKIM_BASE_DIR="/home/scratch/$USER/skims_submit"   # skimmed NanoAOD files
export SCRATCH_SAMPLE_DIR="/home/scratch/$USER/samples"    # special/test samples
export ANALYSIS_OUTPUT_DIR="/home/scratch/$USER/analysis"  # analysis output area
export SKIM_OUTPUT_DIR="/home/scratch/$USER/skims"         # skim job output
export XRD_SERVER=""                                       # XRootD redirector (empty = local)
```

Defaults are in `rdf/macros/utilsAna.py` (lines 14-16).

## Checking What's Available

Before running anything, check the state of skims and data:

```bash
cd rdf/macros

# Check if skim files exist for all samples needed by an analysis
python3 check_skim_completeness.py --ana=wz          # WZ analysis skims (3l)
python3 check_skim_completeness.py --ana=fake         # fake rate skims (1l)
python3 check_skim_completeness.py --ana=all          # all analyses
python3 check_skim_completeness.py --ana=wz --verbose # show individual missing files

# Check what reference data files exist (fake rates, SFs, pileup weights)
ls data/histoFakeEtaPt_*.root        # fake rate histograms by year
ls data/histoTriggerSFEtaPt_*.root   # trigger SFs by year
ls data/puWeights_UL_*.root          # pileup weights by year
ls data/histoLepSFEtaPt_*.root       # lepton SFs by year
ls data/histoBtagEffSelEtaPt_*.root  # b-tag efficiencies by year

# Check which years have data files (expected: 20220, 20221, 20230, 20231, 20240, 20250, 2027)
ls data/histoFakeEtaPt_*.root | sed 's/.*_//' | sed 's/\.root//' | sort -u

# Check what samples are configured for an analysis
wc -l *_input_condor_jobs.cfg                         # sample counts per analysis
grep -v "no$" wzAnalysis_input_condor_jobs.cfg | wc -l  # active WZ samples

# Verify file resolution works
python3 -c "from utilsAna import SwitchSample; print(SwitchSample(179, '3l', 20220)[0])"

# Test file collection for a specific job
python3 collect_files_for_job.py 179 20220 0 3l 2

# Check POG correction JSONs
ls jsonpog-integration/POG/   # should have BTV, EGM, JME, LUM, MUO, TAU

# Check golden JSON lumi files
ls jsns/Cert_Collisions*.json

# Check MVA weights (empty = need to train; present = ready for inference)
ls weights_mva/
```

## Running Analyses

All commands are run from `rdf/macros/`. There is no build step — Python scripts are executed directly and C++ headers are JIT-compiled by ROOT.

### Run a single analysis locally (interactive)
```bash
python3 wzAnalysis.py --process=179 --year=20220 --whichJob=0
```
Arguments: `--process` (sample ID from `*_input_condor_jobs.cfg`), `--year` (encoded as 2022**0**/2022**1**/2023**0**/etc. for sub-eras), `--whichJob` (file group index, -1 for all files).

### Submit batch jobs (CMS Connect Condor)
```bash
./submit_condor.sh <anaCode> [condorJob] [group]
```
Analysis codes: 1=wz, 5=fake, 6=trigger, 7=met, 9=pu

The submission script automatically runs `check_skim_completeness.py` and warns if skims are missing. It reads sample lists from `<analysis>_input_condor_jobs.cfg` (format: `sampleID year [no]`). Rows marked `no` are skipped. See `WZ_ANALYSIS_GUIDE.md` for full CMS Connect workflow.

### Two-round submission
```bash
# Round 1: supporting analyses (independent, run in any order)
./submit_condor.sh 5    # fakeAnalysis (skimType=1l)
./submit_condor.sh 6    # triggerAnalysis (skimType=2l)
./submit_condor.sh 7    # metAnalysis (skimType=met)
./submit_condor.sh 9    # puAnalysis (skimType=2l)
# Wait for Round 1 to finish, merge results, then:
# Round 2: WZ analysis
./submit_condor.sh 1    # wzAnalysis (skimType=3l)
```

### Regenerate job config files
```bash
python3 remake_Analysis_input_condor_jobs.py --ana=wz
```

### Merge output histograms
```bash
python3 mergeHistograms.py --path=fillhisto_wzAnalysis1001 --year=20220 --output=anaWZ
```

### Compute yields and results
```bash
python3 computeYields.py --path=fillhisto_wzAnalysis1001 --year=2022 --output=anaWZ
```

### Run skimming
```bash
cd rdf/skimming
./skim_condor.sh 2022a   # submit skim jobs for 2022 era A datasets
python3 check_missing_skim_files.py   # check for missing skim outputs
```

### Generate plots
```bash
cd rdf/makePlots
./makePlots.sh wz 0 20220
```

### MVA training ntuples
```bash
cd rdf/mva_training
./make_mva_training_ntuples.sh 1    # produce ntuples (sets doNtuples=True)
./make_mva_training_ntuples.sh 10   # hadd into single file + restore wzAnalysis.py
root -q -b -l ewkvbsMVA.C          # train BDT
```

## Architecture Details

### Year encoding
Years encode sub-eras: `20220` = 2022 CD, `20221` = 2022 EFG, `20230` = 2023 BCD, `20231` = 2023 D, `20240` = 2024 BCDEFGHI, `20250` = 2025. Special code `2027` = all Run 3 combined.

### Sample numbering
Sample IDs are integers in the `*_input_condor_jobs.cfg` files. The hundreds digit generally encodes the era (1xx=20220, 2xx=20221, 3xx=20230, etc.). IDs ≥1000 are data samples; IDs < 1000 are MC.

### Selection flow (in `wzAnalysis.py`)
1. Trigger selection → `selectionTrigger2L()`
2. Lepton ID/isolation → `selectionElMu()` with working points from `config/selection.json`
3. 3-lepton WZ selection (Z candidate + W lepton)
4. Tau veto, photon selection, jet/MET cuts
5. VBS-specific variables (mjj, Δηjj, etc.) for VBS categories
6. Weight application (scale factors, pileup, fake rates, EWK corrections)
7. Histogram filling and optional ntuple output (when `doNtuples = True`)

### Key shared modules
- **`utilsAna.py`** — Sample switching (`SwitchSample`), file grouping, luminosity values, trigger/lepton selection JSON parsing, correctionlib loading. **All file path resolution happens here.**
- **`utilsSelection.py`** — Reusable RDataFrame filter/define chains for triggers, leptons, jets, MET, VBS variables, weights
- **`utilsCategory.py`** — Plot category enum (data, signal, backgrounds)
- **`utilsMVA.py`** — MVA variable definitions for BDT-based analyses
- **`functions.h`** — All C++ helper functions (jet selection, b-tagging, lepton kinematics, VBS variable computation, fake rate application, scale factor lookups)
- **`mysf.h`** — Scale factor interface using `correctionlib` (muon/electron ID, isolation, tracking; b-tagging; pileup; JEC/JER)
- **`config/selection.json`** — Central JSON defining lepton working points, trigger paths, VBS selections, and photon criteria per NanoAOD version

### Corrections and scale factors
POG-approved JSON corrections are in `jsonpog-integration/`. Reference histograms (fake rates, b-tag efficiencies, trigger SFs, lepton SFs) are ROOT files in `data/`. The `mysf.h` module wraps `correctionlib` for standardized access.

### Job execution model
Batch jobs run on CMS Connect via Condor with file transfer. The submission script (`submit_condor.sh`) creates a tarball of analysis code, collects input file lists via `collect_files_for_job.py`, and submits jobs that run inside Singularity containers (`analysis_singularity_condor.sh` → `analysis_condor.sh` → `analysis_runner.sh`).

### Skim types per analysis
| Analysis | Code | Skim type | Default group |
|---|---|---|---|
| wzAnalysis | 1 | 3l | 1 |
| fakeAnalysis | 5 | 1l | 9 |
| triggerAnalysis | 6 | 2l | 9 |
| metAnalysis | 7 | met | 9 |
| puAnalysis | 9 | 2l | 9 |

## Dependencies

- ROOT with PyROOT and RDataFrame (Python 3)
- correctionlib (C++ library + Python bindings)
- XRootD client (for remote data access)
- VOMS proxy (for CMS grid authentication)
- Condor for batch submission (CMS Connect)
- Singularity for containerized execution
