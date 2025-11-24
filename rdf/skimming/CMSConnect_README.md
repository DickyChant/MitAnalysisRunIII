# CMS Connect Skimming Guide

This guide explains how to run the skimming analysis on CMS Connect.

## Quick Start

### 1. Prepare Input Files

First, generate the input file lists from DAS:

```bash
cd rdf/skimming/
python make_skim_input_files_fromDAS.py \
    --inputCfg=skim_input_samples_2022a_fromDAS.cfg \
    --outputCfg=skim_input_files_fromDAS.cfg \
    --outputForCondorCfg=skim_input_condor_jobs_fromDAS.cfg \
    --group=5
```

### 2. Prepare CMS Connect Package

Generate the tarball and submission scripts:

```bash
./submit_skim_cmsconnect.sh 2022a [outputDir]
```

This creates:
- `skim_cmsconnect_2022a.tgz` - Package with all necessary files
- `submit_cmsconnect_2022a.sh` - Job submission script
- `README_CMSConnect_2022a.txt` - Detailed instructions

### 3. Upload to CMS Connect

1. Go to [CMS Connect](https://cmsconnect.web.cern.ch/)
2. Upload the tarball: `skim_cmsconnect_2022a.tgz`
3. Upload the job script: `submit_cmsconnect_2022a.sh`

### 4. Run on CMS Connect

On CMS Connect, extract and run:

```bash
# Extract tarball
tar xzf skim_cmsconnect_2022a.tgz

# Make executable
chmod +x skim_cmsconnect.sh submit_cmsconnect_2022a.sh

# Run a single job
./skim_cmsconnect.sh 0 0 5 skim_input_samples_2022a_fromDAS.cfg skim_input_files_fromDAS.cfg ./output

# Or run all jobs (if using a job scheduler)
./submit_cmsconnect_2022a.sh
```

## Script Details

### `skim_cmsconnect.sh`

Main skimming script for CMS Connect. Automatically:
- Sets up CMS environment (CMSSW)
- Checks for ROOT and Python
- Validates required files
- Runs the skimming
- Handles output files

**Usage:**
```bash
./skim_cmsconnect.sh <whichSample> <whichJob> <group> <inputSamplesCfg> <inputFilesCfg> [outputDir]
```

**Arguments:**
- `whichSample`: Sample index (0-based) from inputSamplesCfg
- `whichJob`: Job index (-1 for all jobs, or specific job number)
- `group`: Number of input files per job
- `inputSamplesCfg`: Configuration file with sample names
- `inputFilesCfg`: Configuration file with input file paths
- `outputDir`: (optional) Output directory (default: ./output)

### `submit_skim_cmsconnect.sh`

Helper script to prepare CMS Connect submission package.

**Usage:**
```bash
./submit_skim_cmsconnect.sh <year> [outputDir]
```

**Example:**
```bash
./submit_skim_cmsconnect.sh 2022a
./submit_skim_cmsconnect.sh 2023b /store/user/yourusername/skims
```

## Requirements

### On Your Local Machine

- Python 3 with PyROOT
- Access to DAS (for generating file lists)
- CMS Connect account

### On CMS Connect

- CMSSW environment (script will set up automatically)
- ROOT with RDataFrame support
- Python 3
- Valid VOMS proxy for xrootd access:
  ```bash
  voms-proxy-init --voms cms
  ```

## Output Files

The skimming produces output files in the following structure:

```
output/
├── 1l/
│   └── <sampleName>/
│       └── output_1l_<sample>_<job>.root
├── 2l/
│   └── <sampleName>/
│       └── output_2l_<sample>_<job>.root
├── 3l/
│   └── <sampleName>/
│       └── output_3l_<sample>_<job>.root
├── met/
│   └── <sampleName>/
│       └── output_met_<sample>_<job>.root
└── pho/
    └── <sampleName>/
        └── output_pho_<sample>_<job>.root
```

## Troubleshooting

### VOMS Proxy Issues

If you get xrootd access errors:
```bash
voms-proxy-init --voms cms --valid 168:00
```

### CMSSW Setup Issues

The script automatically sets up CMSSW_14_1_4. If you need a different version, edit `skim_cmsconnect.sh` and change:
```bash
scramv1 project CMSSW CMSSW_14_1_4
```

### Missing Files

Ensure all required files are in the tarball:
- `skim.py`
- `functions_skim.h`
- `haddnanoaod.py`
- `config/` directory (with selection.json)
- `jsns/` directory (with JSON files)

### Output Directory

If using a remote storage (e.g., EOS), specify the full path:
```bash
./skim_cmsconnect.sh 0 0 5 input.cfg files.cfg root://eoscms.cern.ch//eos/cms/store/user/yourusername/skims
```

## Running Multiple Jobs

### Option 1: Manual Submission

Run each job individually:
```bash
for sample in {0..10}; do
    for job in {0..5}; do
        ./skim_cmsconnect.sh $sample $job 5 input.cfg files.cfg ./output
    done
done
```

### Option 2: Using CMS Connect Job Scheduler

If CMS Connect has a job scheduler, you can submit multiple jobs:
```bash
# Example with a simple job array
for job in $(cat job_list.txt); do
    ./skim_cmsconnect.sh $job ...
done
```

### Option 3: Using HTCondor on CMS Connect

If HTCondor is available, create a submit file:
```bash
# Create submit file
cat > skim.submit << EOF
executable = skim_cmsconnect.sh
arguments = \$(Process) 0 5 input.cfg files.cfg ./output
output = logs/job_\$(Process).out
error = logs/job_\$(Process).err
log = logs/job_\$(Process).log
queue 100
EOF

# Submit
condor_submit skim.submit
```

## Integration with Main Analysis

After skimming on CMS Connect:

1. Download the skimmed files to your local analysis area
2. Update the analysis configuration to point to the skimmed files
3. Run the main analysis scripts in `rdf/macros/`

## Support

For issues or questions:
- Check the main README.md
- Review error logs in the `logs/` directory
- Contact the MIT CMS group

