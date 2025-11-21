# MitAnalysisRunIII

A comprehensive high-energy physics analysis framework for studying diboson production and vector boson scattering processes using CMS detector data from LHC Run 3 at 13.6 TeV.

## Overview

This repository contains analysis code for studying:
- **WW production** (W boson pairs)
- **Same-sign WW (SSWW)** production (VBS signature)
- **WZ production**
- **ZZ production**
- **Vector Boson Scattering (VBS)** processes
- **Electroweak (EWK) and QCD** processes

The framework processes NanoAOD format data from Run 3 (2022-2024 data-taking periods) using ROOT's RDataFrame for efficient parallel processing.

## Repository Structure

### `rdf/` - Main Analysis Framework

The core analysis infrastructure using ROOT RDataFrame:

#### `rdf/macros/` - Analysis Scripts
Python-based analysis using PyROOT and RDataFrame:
- `wwAnalysis.py` - WW diboson production analysis
- `sswwAnalysis.py` - Same-sign WW analysis (VBS signature)
- `wzAnalysis.py` - WZ production analysis
- `zzAnalysis.py` - ZZ production analysis
- `zAnalysis.py` - Z boson analysis
- `zmetAnalysis.py` - Z+MET analysis
- `fakeAnalysis.py` - Non-prompt lepton (fake) background estimation
- `gammaAnalysis.py` - Photon analysis
- `triggerAnalysis.py` - Trigger efficiency studies
- `puAnalysis.py` - Pileup analysis
- `genAnalysis.py` - Generator-level analysis
- `metAnalysis.py` - Missing transverse energy analysis

Utility modules:
- `utilsAna.py` - Analysis utilities (MC/data lists, sample handling)
- `utilsSelection.py` - Selection functions (leptons, jets, MET, triggers, weights)
- `utilsCategory.py` - Plot category definitions
- `utilsMVA.py` - MVA variable definitions
- `functions.h` - C++ helper functions for RDataFrame operations
- `mysf.h/py` - Scale factor handling using correctionlib

Efficiency computations:
- `computeLeptonEff.py` / `computeLeptonEff_2d.py` - Lepton efficiency
- `computeTriggerEff.py` - Trigger efficiency
- `computeBtaggingEff_2d.py` - B-tagging efficiency
- `computeFakeRates.py` - Fake rate measurement
- `computeYields.py` - Yield calculations

Datacard generation for statistical analysis:
- `makeWWDataCards.C` - WW datacards
- `makeSSWWDataCards.C` - Same-sign WW datacards
- `makeVVDataCards.C` - Diboson datacards
- `makeGammaDataCards.C` - Photon datacards

Configuration:
- `config/selection.json` - Central JSON configuration for selections, triggers, and working points

Data:
- `data/` - ROOT files with scale factors, theory corrections, pileup weights, and efficiency histograms
- `jsonpog-integration/POG/` - Official CMS POG corrections for leptons, jets, b-tagging, MET

#### `rdf/skimming/` - NanoAOD Skimming
Framework to reduce NanoAOD file size:
- `skim.py` - Main skimming script
- `functions_skim.h` - C++ functions for skimming
- `make_skim_input_files.py` - Create input file lists
- `skim_input_samples_*.cfg` - Configuration files for different run periods

#### `rdf/makePlots/` - Plotting and Visualization
- `makeAllPlots.C` - Master plotting script
- `finalPlot.C` - Final plot production with CMS style
- `StandardPlot.C` - Standard plot formatting
- `CMS_lumi.C/h` - CMS luminosity label handling
- `producingYields.C` - Yield table production

#### `rdf/mva_training/` - Machine Learning
MVA training for signal/background discrimination:
- `ewkvbsMVA.C` - MVA training for EWK VBS analysis
- `make_mva_training_ntuples.sh` - Ntuple preparation for training

### `macros/` - Legacy and Specialized Tools

Supporting macros and utilities:

#### `macros/nanoaod/` - NanoAOD Handling
- `sswwAnalysis.C` - C++ version of SSWW analysis
- `nanoAOD.C/h` - NanoAOD tree reader classes
- `makeGoodRunSample.C` - Good run selection

#### `macros/gen/` - Generator-level Calculations
- `computeGenWWXS.C` - WW cross-section with theory uncertainties
- `computeGenVBSVVXS.C` - VBS diboson cross-section
- `computeGenPtWWUnc.C` - pT(WW) uncertainties

#### `macros/trigger/` - Trigger Efficiency Inputs
Organized by year and data/MC with trigger efficiency tables

#### Other Utilities
- `get_all_BTVSFs.py` - B-tagging scale factors
- `get_all_lepSFSystematics.py` - Lepton SF systematics
- `get_puWeights_JSON.py` - Pileup weights from JSON
- `make_rootfiles_vbs_theory.py` - VBS theory predictions (NLO/EWK k-factors)
- `remake_VVewkCorr.C` - Diboson EWK corrections

### `plotting/` - High-level Plotting Tools
- `makeAllPlots.C` - Comprehensive plotting script
- `finalPlot.C` - Final publication-quality plots
- `StandardPlot.C` - Standard plot templates

## Physics Analysis Workflow

### 1. Skimming
```bash
cd rdf/skimming/
python skim.py --config skim_input_samples_2022.cfg
```
- Input: CMS NanoAOD files from Run 3
- Apply loose preselection (triggers, leptons, jets)
- Reduce file size for faster analysis

### 2. Analysis
```bash
cd rdf/macros/
python wwAnalysis.py --year 2022 --mode data
python wwAnalysis.py --year 2022 --mode mc
```
- Event selection (triggers, lepton quality, jet requirements)
- Apply scale factors (lepton ID, triggers, b-tagging)
- Calculate weights (pileup, theory corrections)
- Fill histograms for different categories

### 3. Efficiency Calculations
```bash
python computeLeptonEff.py --year 2022
python computeTriggerEff.py --year 2022
python computeBtaggingEff_2d.py --year 2022
python computeFakeRates.py --year 2022
```

### 4. Plotting
```bash
cd rdf/makePlots/
root -l -b -q 'makeAllPlots.C("ww", "2022")'
```
- Create distributions for physics variables
- Apply CMS style formatting
- Generate publication-quality plots

### 5. Statistical Analysis
```bash
root -l -b -q 'makeWWDataCards.C("2022")'
```
- Generate datacards for HiggsCombine tool
- Measure cross-sections and fiducial regions

## Event Selections

The framework supports multiple final states:
- **2-lepton**: WW, Z+MET, same-sign WW
- **3-lepton**: WZ
- **4-lepton**: ZZ
- **Lepton+photon**: gamma analysis

### Physics Objects
- **Leptons**: Electrons and muons with multiple working points (tight/medium/loose)
- **Jets**: AK4 jets with b-tagging (DeepJet, ParticleNet)
- **MET**: Multiple MET definitions (PF, PUPPI, Calo, Track)
- **VBS jets**: Forward jets for vector boson scattering

## Systematic Uncertainties

The framework handles 100+ systematic uncertainties including:
- **Theory**: QCD scale, PDF, parton shower
- **Experimental**: Lepton SF, trigger, b-tagging, JEC/JER, pileup
- All systematics are propagated through to datacards

## Data Periods Supported

- **2022**: Run3Summer22 (eras 20220/20221)
- **2023**: Run3Summer23 (eras 20230/20231)
- **2024**: Run3-24 (era 20240)

## Dependencies

### Required Software
- **ROOT** (version 6+) with RDataFrame support
- **Python 3** with PyROOT bindings
- **correctionlib** for POG scale factors
- **TMVA** for MVA training

### External Tools
- **HiggsCombine** for statistical analysis (external dependency)

### Installation
```bash
# Setup CMSSW environment (if using LPC/LXPLUS)
cmsrel CMSSW_X_Y_Z
cd CMSSW_X_Y_Z/src
cmsenv

# Clone repository
git clone <repository-url> MitAnalysisRunIII
cd MitAnalysisRunIII

# Install correctionlib (if needed)
pip install correctionlib
```

## Batch Processing

The framework supports batch job submission:
- **SLURM** job submission scripts
- **HTCondor** support
- **Singularity** container integration

Example batch submission:
```bash
# Edit batch submission scripts in rdf/macros/
sbatch submit_analysis.sh  # for SLURM
condor_submit submit_analysis.jdl  # for HTCondor
```

## Configuration

Central configuration is managed through `rdf/macros/config/selection.json`:
- Lepton selection criteria (fake/tight working points)
- Trigger definitions by year
- VBS selection cuts
- MET filters
- Photon selections

Edit this file to modify analysis selections.

## Contributing

When contributing to this repository:
1. Follow the existing code structure
2. Document new physics selections
3. Update systematic uncertainties appropriately
4. Test with small samples before full production

## Contact

For questions or issues, please contact the MIT CMS group.

## License

This code is intended for CMS collaboration internal use.

## Acknowledgments

This analysis uses:
- CMS NanoAOD data format
- Official CMS POG scale factors and corrections
- ROOT RDataFrame framework
- Theory predictions from various generator groups
