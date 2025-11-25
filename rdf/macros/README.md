# Analysis Framework README

This directory contains the analysis framework for Run 3 CMS analyses. The framework uses ROOT's RDataFrame to process NanoAOD files and produce histograms for various physics analyses.

## Available Analyses

The following analyses are available:

| ID | Analysis Name | Description |
|----|--------------|-------------|
| 0 | `zAnalysis` | Z boson analysis |
| 1 | `wzAnalysis` | WZ diboson analysis |
| 2 | `zzAnalysis` | ZZ diboson analysis |
| 3 | `sswwAnalysis` | Same-sign WW analysis |
| 4 | `zmetAnalysis` | Z+MET analysis |
| 5 | `fakeAnalysis` | Fake lepton rate analysis |
| 6 | `triggerAnalysis` | Trigger efficiency analysis |
| 7 | `metAnalysis` | MET analysis |
| 8 | `wwAnalysis` | WW diboson analysis |
| 9 | `puAnalysis` | Pileup analysis |
| - | `gammaAnalysis` | Photon analysis |
| - | `genAnalysis` | Generator-level analysis |

## Prerequisites

1. **CMSSW Environment**: The analyses require CMSSW_13_3_1 or compatible environment
2. **ROOT**: With Python bindings enabled
3. **VOMS Proxy**: For accessing CMS data (required for Condor jobs)
4. **Data Files**: Various correction files in the `data/` directory:
   - Fake rate histograms (`histoFakeEtaPt_*.root`)
   - Lepton scale factors (`histoLepSFEtaPt_*.root`)
   - Trigger scale factors (`histoTriggerSFEtaPt_*.root`)
   - B-tagging efficiency (`histoBtagEffSelEtaPt_*.root`)
   - Pileup weights (`histoPUWeights_*.root`)
   - W+jets scale factors (`histoWSSF_*.root`)

## Running Analyses

### Method 1: Interactive SLURM Jobs

For running jobs interactively on a SLURM cluster:

```bash
./prepare_jobs_run_interactive.sh <analysis_id>
```

This script generates job submission commands for all samples in the corresponding `*_input_condor_jobs.cfg` file. The generated commands are saved to files like `lll_z`, `lll_wz`, etc.

**Example:**
```bash
# Generate commands for Z analysis
./prepare_jobs_run_interactive.sh 0

# Execute the generated commands
bash lll_z
```

### Method 2: Batch Submission (SLURM)

For submitting jobs to SLURM:

```bash
./analysis_submit_slurm.sh <analysis_id> [condor_job_id]
```

**Parameters:**
- `analysis_id`: Analysis number (0-9, see table above)
- `condor_job_id`: Optional job identifier (default: 1001)

**Example:**
```bash
# Submit WZ analysis with default job ID 1001
./analysis_submit_slurm.sh 1

# Submit Z analysis with custom job ID 2001
./analysis_submit_slurm.sh 0 2001
```

The script:
1. Reads sample configurations from `*_input_condor_jobs.cfg`
2. Creates SLURM job scripts for each sample and job group
3. Submits jobs using `sbatch`
4. Uses Singularity containers for environment isolation

### Method 3: Batch Submission (Condor)

For submitting jobs to HTCondor:

```bash
./analysis_submit_condor.sh <analysis_id> [condor_job_id]
```

**Prerequisites:**
- Valid VOMS proxy (initialized automatically)
- Access to CMS data storage

**Example:**
```bash
# Submit WZ analysis
./analysis_submit_condor.sh 1

# Submit with custom job ID
./analysis_submit_condor.sh 1 2001
```

The script:
1. Creates a tarball with analysis code and dependencies
2. Initializes VOMS proxy
3. Submits Condor jobs for each sample/job combination
4. Uses Singularity containers via `analysis_singularity_condor.sh`

### Method 4: Direct Execution

For running a single job directly:

```bash
./analysis_slurm.sh <process> <year> <whichJob> <condorJob> <analysisName>
```

**Parameters:**
- `process`: Sample ID (from config file)
- `year`: Year code (20220=2020, 20221=2021, 20230=2022, 20231=2023, 20240=2024, 20250=2025)
- `whichJob`: Job index within the group (0 to group size)
- `condorJob`: Job identifier
- `analysisName`: Name of analysis (e.g., `zAnalysis`, `wzAnalysis`)

**Example:**
```bash
# Run Z analysis for sample 100, year 2020, job 0
./analysis_slurm.sh 100 20220 0 1001 zAnalysis
```

## Configuration Files

Each analysis has a corresponding configuration file `*_input_condor_jobs.cfg` that lists the samples to process:

**Format:**
```
<process_id> <year_code> [no]
```

**Example (`zAnalysis_input_condor_jobs.cfg`):**
```
100 20220
104 20220
105 20220
200 20221
...
```

- Lines starting with `#` or empty lines are ignored
- Lines ending with `no` are skipped
- `process_id`: Sample identifier (0-999 for MC, 1000+ for data)
- `year_code`: Year encoding (20220=2020, 20221=2021, 20230=2022, 20231=2023, 20240=2024, 20250=2025)

### How to Configure Analysis Input

#### Understanding Sample IDs

Sample IDs map to specific MC samples or data streams. The mapping is defined in `utilsAna.py` in the `SwitchSample()` function:

- **MC Samples (0-999)**: Each ID corresponds to a specific MC dataset
  - Example: `100` = DYto2L-2Jets_MLL-10to50 for 2022
  - Example: `103` = WZto3LNu (POWHEG) for 2022
  - Example: `179` = WZto3LNu-2Jets_QCD (MadGraph) for 2022
  - The full mapping is in `utilsAna.py` starting around line 809

- **Data Samples (1000+)**: 
  - `1000-1009`: SingleMuon
  - `1010-1019`: DoubleMuon
  - `1020-1029`: MuonEG
  - `1030-1039`: EGamma
  - `1040-1049`: Muon
  - `1050-1059`: MET

#### Editing Configuration Files

To add or remove samples from an analysis:

1. **Edit the config file directly:**
   ```bash
   # Edit the config file for your analysis
   vim zAnalysis_input_condor_jobs.cfg
   ```

2. **Add a new sample:**
   ```
   <sample_id> <year_code>
   ```
   Example: To add WZ POWHEG sample for 2022:
   ```
   103 20230
   ```

3. **Skip a sample (temporarily):**
   Add `no` at the end of the line:
   ```
   100 20220 no
   ```

4. **Comment out a sample:**
   Add `#` at the beginning:
   ```
   # 100 20220
   ```

#### Regenerating Configuration Files

For WZ and ZZ analyses, you can regenerate configs to switch between POWHEG and MadGraph samples:

```bash
python3 remake_Analysis_input_condor_jobs.py --ana=wz --isWZMG=0 --isZZMG=0
```

**Parameters:**
- `--ana`: Analysis name (`wz` or `zz`)
- `--isWZMG`: Use MadGraph WZ (1) or POWHEG (0)
- `--isZZMG`: Use MadGraph ZZ (1) or POWHEG (0)

This script:
- Reads the existing config file
- Replaces WZ/ZZ sample lines with the specified generator
- Outputs to `*_input_condor_jobs_new.cfg`

**Example workflow:**
```bash
# Generate config with POWHEG samples
python3 remake_Analysis_input_condor_jobs.py --ana=wz --isWZMG=0 --isZZMG=0
mv wzAnalysis_input_condor_jobs_new.cfg wzAnalysis_input_condor_jobs.cfg

# Or use MadGraph samples
python3 remake_Analysis_input_condor_jobs.py --ana=wz --isWZMG=1 --isZZMG=1
mv wzAnalysis_input_condor_jobs_new.cfg wzAnalysis_input_condor_jobs.cfg
```

#### Finding Available Sample IDs

To see what sample IDs are available:

1. **Check `utilsAna.py`**: The `SwitchSample()` function (starting around line 799) contains the full mapping of sample IDs to dataset paths.

2. **Common sample IDs:**
   - `100-189`: 2022 MC samples (Run3Summer22)
   - `200-289`: 2022EE MC samples (Run3Summer22EE)
   - `300-389`: 2023 MC samples (Run3Summer23)
   - `400-489`: 2023BPix MC samples
   - `500-589`: 2024 MC samples
   - `1000+`: Data samples

3. **Dataset paths**: Sample IDs map to directories under:
   ```
   /ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/<skimType>/
   ```
   Where `<skimType>` is typically `2l`, `3l`, `met`, or `pho` depending on the analysis.

#### Verifying Sample Configuration

Before submitting jobs, verify your config file:

```bash
# Check that all lines are valid
grep -v "^#" zAnalysis_input_condor_jobs.cfg | grep -v "^$" | awk '{print $1, $2}'

# Count samples per year
grep -v "^#" zAnalysis_input_condor_jobs.cfg | grep -v "^$" | grep -v " no$" | awk '{print $2}' | sort | uniq -c
```

## Output Files

Each job produces a ROOT file with histograms:

```
fillhisto_<analysis><condorJob>_sample<process>_year<year>_job<job>.root
```

**Example:**
```
fillhisto_zAnalysis1001_sample100_year20220_job0.root
```

## Merging Histograms

After all jobs complete, merge the output files:

```bash
python3 mergeHistograms.py --path=fillhisto_<analysis><condorJob> --year=<year> --output=<output_dir>
```

**Example:**
```bash
# Merge Z analysis outputs for 2020
python3 mergeHistograms.py --path=fillhisto_zAnalysis1001 --year=2020 --output=anaZ_2020
```

## Monitoring Jobs

### Check Job Status (SLURM)

```bash
./checkJobs.sh <analysis_name> <condor_job_id> <year> slurm
```

**Example:**
```bash
./checkJobs.sh z 1001 2020 slurm
```

### Check Job Status (Condor)

```bash
./checkJobs.sh <analysis_name> <condor_job_id> <year> condor
```

### Check Output Files

```bash
# Count output files
ls fillhisto_<analysis><condorJob>*year<year>* | wc -l

# Check for failed jobs
grep FAILED logs/simple_<analysis>Analysis_<condorJob>_*_<year>_*
```

## Analysis-Specific Notes

### Fake Analysis (ID 5)

The fake analysis has special handling. When submitting with an additional parameter:

```bash
./analysis_submit_slurm.sh 5 1001 1
```

This runs additional special jobs for fake rate calculation.

### WZ and ZZ Analyses

These analyses use smaller job groups (group=1) due to larger file sizes.

### SSWW Analysis

Uses group=3 for job splitting.

## Job Grouping

Jobs are split into groups to parallelize processing. The group size varies by analysis:

- `zAnalysis`: group=10
- `wzAnalysis`: group=1
- `zzAnalysis`: group=1
- `sswwAnalysis`: group=3
- `zmetAnalysis`: group=10
- `fakeAnalysis`: group=4
- `triggerAnalysis`: group=10
- `metAnalysis`: group=4
- `wwAnalysis`: group=4
- `puAnalysis`: group=10

## Environment Setup

### For SLURM with Singularity

The framework uses Singularity containers. The `analysis_singularity_slurm.sh` script sets up:
- CMSSW environment via `cmssw-el9`
- Proper bind mounts for data access

### For Condor

The `analysis_condor.sh` script:
1. Sets up CMSSW_13_3_1 environment
2. Extracts the analysis tarball
3. Runs the analysis
4. Cleans up temporary files

## Data Cards

After merging histograms, data cards can be created using:

- `makeWWDataCards.C` - For WW analysis
- `makeSSWWDataCards.C` - For SSWW analysis
- `makeVVDataCards.C` - For VV analyses
- `makeFakeAnalysisDataCards.C` - For fake analysis
- `makeGammaDataCards.C` - For photon analysis

**Example:**
```bash
root -l -b -q 'makeWWDataCards.C'
```

## Utility Scripts

- `computeFakeRates.py` - Calculate fake lepton rates
- `computeLeptonEff.py` - Calculate lepton efficiencies
- `computeTriggerEff.py` - Calculate trigger efficiencies
- `computeYields.py` - Calculate event yields
- `checkFilesAnalysis.py` - Verify output files
- `remake_Analysis_input_condor_jobs.py` - Regenerate config files

## Troubleshooting

### Jobs Fail with "DONE NO FILES"

This indicates the job completed but produced no output (likely no events passed selection). This is normal for some samples.

### Jobs Fail with "FAILED"

Check the error logs:
```bash
cat logs/simple_<analysis>Analysis_<condorJob>_<sample>_<year>_<job>.error
```

Common issues:
- Missing input files
- Corrupted data files
- Insufficient memory (increase `RequestMemory` in Condor or `--mem-per-cpu` in SLURM)
- Missing correction files in `data/` directory

### VOMS Proxy Issues (Condor)

Ensure your proxy is valid:
```bash
voms-proxy-info
```

If expired, initialize:
```bash
voms-proxy-init --voms cms --valid 168:00
```

## Directory Structure

```
macros/
├── *Analysis.py              # Analysis scripts
├── *Analysis_input_condor_jobs.cfg  # Sample configurations
├── utils*.py                 # Utility functions
├── functions.h               # C++ helper functions
├── data/                     # Correction files and data
├── config/                   # Configuration JSON files
├── jsns/                     # Luminosity JSON files
├── jsonpog-integration/      # CMS POG corrections
├── weights_mva/              # MVA weights
├── logs/                     # Job logs (created during execution)
└── analysis_*.sh             # Job execution scripts
```

## Year Encoding

The framework uses a specific year encoding:
- `20220` = 2020 (Run 2)
- `20221` = 2021 (Run 2)
- `20230` = 2022 (Run 3)
- `20231` = 2023 (Run 3)
- `20240` = 2024 (Run 3)
- `20250` = 2025 (Run 3)

## Additional Resources

- Selection criteria are defined in `config/selection.json`
- Luminosity information is in `jsns/` directory
- CMS POG corrections are in `jsonpog-integration/`

## Connecting Custom Skimming Output

If you have custom skimming output (e.g., from `make_wz_guillermo_folder.sh`), see **[CONNECT_SKIMMING.md](CONNECT_SKIMMING.md)** for detailed instructions on how to connect your skimming output to the analysis framework.

**Quick summary:**
1. Modify `dirT2` in `utilsAna.py`'s `SwitchSample()` function to point to your skimming output directory
2. Ensure sample names match between your skimming config and the analysis expectations
3. Test with a single sample before submitting all jobs

