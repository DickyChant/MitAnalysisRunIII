# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MitAnalysisRunIII is a CMS particle physics analysis framework for LHC Run 3 data, focused on VBS-WZ (vector boson scattering in the WZ channel) using ROOT RDataFrame in Python+C++. Data spans 2022-2025 eras in NanoAOD format (v12 for ≤2023, v15 for ≥2024).

## Repository Structure

- **`rdf/macros/`** — Primary analysis code. The main analysis is `wzAnalysis.py`, with supporting analyses for fake rates (`fakeAnalysis.py`), triggers (`triggerAnalysis.py`), pileup (`puAnalysis.py`), MET (`metAnalysis.py`), and generator-level studies (`genAnalysis.py`). Core C++ functions live in `functions.h`, scale factors in `mysf.h`.
- **`rdf/skimming/`** — Data reduction pipeline. `skim.py` reads NanoAOD from XRootD and applies loose preselection. Input sample lists are in `skim_inputfiles_*` directories organized by year/era.
- **`rdf/makePlots/`** — Plotting. `finalPlot.C` generates CMS-style plots, driven by `makePlots.sh`.
- **`rdf/mva_training/`** — BDT training for VBS jet tagging (`ewkvbsMVA.C`).

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

The submission script reads sample lists from `<analysis>_input_condor_jobs.cfg` (format: `sampleID year [no]`). Rows marked `no` are skipped. See `WZ_ANALYSIS_GUIDE.md` for full CMS Connect workflow.

### Regenerate job config files
```bash
python3 remake_Analysis_input_condor_jobs.py --ana=wz
```

### Merge output histograms
```bash
python3 mergeHistograms.py --path=fillhisto_wzAnalysis --year=20220 --output=anaWZ
```

### Compute yields and results
```bash
python3 computeYields.py --path=fillhisto_wzAnalysis1001 --year=2022 --output=anaWZ
```

### Run skimming
```bash
cd rdf/skimming
python3 skim.py --process=<sampleID> --year=<year> --whichJob=<job>
```

### Generate plots
```bash
./makePlots.sh <analysis> <applyScaling> <year>
# Example: ./makePlots.sh wz 0 20220
```

## Architecture Details

### Year encoding
Years encode sub-eras: `20220` = 2022 CD, `20221` = 2022 EFG, `20230` = 2023 BCD, `20231` = 2023 D, `20240` = 2024 BCDEFGHI, `20250` = 2025 (when available).

### Sample numbering
Sample IDs are integers in the `*_input_condor_jobs.cfg` files. The hundreds digit generally encodes the era (1xx=20220, 2xx=20221, 3xx=20230, etc.). IDs ≥1000 are MC samples; IDs < 1000 with specific patterns are data.

### Selection flow (in `wzAnalysis.py`)
1. Trigger selection → `selectionTrigger2L()`
2. Lepton ID/isolation → `selectionElMu()` with working points from `config/selection.json`
3. 3-lepton WZ selection (Z candidate + W lepton)
4. Tau veto, photon selection, jet/MET cuts
5. VBS-specific variables (mjj, Δηjj, etc.) for VBS categories
6. Weight application (scale factors, pileup, fake rates, EWK corrections)
7. Histogram filling and optional ntuple output

### Key shared modules
- **`utilsAna.py`** — Sample switching (`SwitchSample`), file grouping, luminosity values, trigger/lepton selection JSON parsing, correctionlib loading
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

## Dependencies

- ROOT with PyROOT and RDataFrame (Python 3)
- correctionlib (C++ library + Python bindings)
- XRootD client (for remote data access)
- VOMS proxy (for CMS grid authentication)
- Condor for batch submission (CMS Connect)
- Singularity for containerized execution
