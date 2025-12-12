# WZ Analysis Guide

This guide explains how to run the WZ analysis (`wzAnalysis.py`) on CMS Connect using Condor with file transfer.

## Overview

The WZ analysis processes 3-lepton events (skimType="3l") and requires:
- Input files from skimming (3l skim type)
- Configuration files (config/, jsns/)
- Scale factors and weights (data/)
- MVA weights (weights_mva/)

## Quick Start

### Step 1: Setup Analysis Folder (if not done)

```bash
cd /home/stqian/MitAnalysisRunIII/rdf/macros
./make_analysis_folder.sh
cd /home/scratch/stqian/analysis
```

### Step 2: Verify Job Configuration

The job configuration file should already exist: `wzAnalysis_input_condor_jobs.cfg`

Check its contents:
```bash
head -20 wzAnalysis_input_condor_jobs.cfg
```

Format: `<switchSample> <year> [no]`

Example:
```
179 20220
183 20220
279 20221
283 20221
```

### Step 3: Verify File Paths

Make sure `utilsAna.py` points to your 3l skim files. Check the `SwitchSample()` function:

```bash
# Check what path wzAnalysis will use for a sample
python3 -c "from utilsAna import SwitchSample; print(SwitchSample(179, '3l', 20220)[0])"
```

This should point to where your 3l skim files are located (e.g., `/home/scratch/stqian/wz_guillermo/skims_2022a/3l/`).

### Step 4: Test File Collection

Before submitting many jobs, test that files can be found:

```bash
# Test file collection for sample 179, year 20220, job 0
python3 collect_files_for_job.py 179 20220 0 3l 2
```

This should output a list of ROOT file paths. If it's empty or shows errors, check your paths in `utilsAna.py`.

### Step 5: Submit Jobs

```bash
# Make scripts executable
chmod +x submit_wzAnalysis_condor.sh
chmod +x analysis_*.sh

# Submit jobs (default: condorJob=1001, group=1)
./submit_wzAnalysis_condor.sh

# Or specify parameters
./submit_wzAnalysis_condor.sh 1001 1
```

**Parameters**:
- `condorJob`: Job ID prefix for output naming (default: 1001)
- `group`: Number of job groups 0-N (default: 1, wzAnalysis typically uses group=1)

### Step 6: Monitor Jobs

```bash
# Check job status
condor_q -submitter $USER

# Watch queue
watch -n 5 'condor_q -submitter $USER'

# Check specific job
condor_q <job_id>
```

### Step 7: Check Logs

```bash
# List log files
ls -lh logs/

# Check output of a specific job
tail -f logs/wzAnalysis_1001_179_20220_0.out

# Check for errors
grep -i error logs/*.error | head -20

# Count successful jobs
grep -c "DONE" logs/*.out

# Count failed jobs
grep -c "FAILED" logs/*.out
```

### Step 8: Check Output Files

```bash
# List output files
ls -lh fillhisto_wzAnalysis*.root

# Count completed jobs
ls fillhisto_wzAnalysis*.root | wc -l

# Check file sizes (should be > 0)
find . -name "fillhisto_wzAnalysis*.root" -size +0
```

## WZ Analysis Specifics

### Skim Type

WZ analysis uses **skimType="3l"** (3-lepton events). Make sure you have:
1. Run skimming with 3l skim type
2. Files are located at the path specified in `utilsAna.py` for 3l skims

### Command Line Arguments

WZ analysis uses:
- `--process=<sample_id>` (instead of `--switchSample`)
- `--year=<year>`
- `--whichJob=<job_id>`

The wrapper script `analysis_slurm_wzAnalysis.sh` handles the conversion from `switchSample` to `process`.

### Group Size

WZ analysis typically uses `group=1` (2 jobs total: jobs 0 and 1). This is set as the default in `submit_wzAnalysis_condor.sh`.

### Output Files

Output files are named:
```
fillhisto_wzAnalysis<condorJob>_sample<sample>_year<year>_job<job>.root
```

Example:
```
fillhisto_wzAnalysis1001_sample179_year20220_job0.root
```

## Directory Structure

After running, you'll have:

```
/home/scratch/stqian/analysis/
├── wzAnalysis_input_condor_jobs.cfg  # Job configuration
├── file_lists/                       # File lists (created automatically)
│   ├── wzAnalysis_1001_179_20220_0.txt
│   ├── wzAnalysis_1001_179_20220_1.txt
│   └── ...
├── logs/                             # Job logs (created automatically)
│   ├── wzAnalysis_1001_179_20220_0.log
│   ├── wzAnalysis_1001_179_20220_0.out
│   ├── wzAnalysis_1001_179_20220_0.error
│   └── ...
└── fillhisto_wzAnalysis*.root        # Output files (transferred back)
```

## Troubleshooting

### No Files Found

**Error**: "No files found for sample=X, year=Y, job=Z"

**Solutions**:
1. Check that 3l skim files exist:
   ```bash
   ls /home/scratch/stqian/wz_guillermo/skims_2022a/3l/
   ```

2. Verify path in `utilsAna.py`:
   ```bash
   python3 -c "from utilsAna import SwitchSample; print(SwitchSample(179, '3l', 20220)[0])"
   ```

3. Test file collection:
   ```bash
   python3 collect_files_for_job.py 179 20220 0 3l 2
   ```

### Job Fails

**Check logs**:
```bash
# Look at error log
cat logs/wzAnalysis_1001_179_20220_0.error

# Look at output log
cat logs/wzAnalysis_1001_179_20220_0.out

# Common issues:
# - Missing VOMS proxy
# - Files not accessible
# - Missing data files (data/VV_NLO_LO_CMS_mjj.root, etc.)
# - Disk space issues
```

### Missing Data Files

WZ analysis requires several data files:
- `data/VV_NLO_LO_CMS_mjj.root` - EWK correction weights
- `data/histoWSSF_<year>.root` - W* scale factors
- `data/puWeights_UL_<year>.root` - Pileup weights
- `data/histoFakeEtaPt_<year>.root` - Fake rates
- And others...

Make sure these are included in the tarball (they should be copied automatically).

## Running Interactively (for testing)

To test wzAnalysis locally before submitting to Condor:

```bash
# Test with a single sample
python3 wzAnalysis.py --process=179 --year=20220 --whichJob=-1
```

This will process all files for sample 179, year 20220 (whichJob=-1 means all files).

## Integration with Other Analyses

The WZ analysis follows the same pattern as other analyses:
- Uses `SwitchSample()` to get sample paths
- Uses `getMClist()` or `getDATAlist()` to get file lists
- Uses the file transfer system for CMS Connect

The main difference is:
- Uses `--process` instead of `--switchSample`
- Uses `skimType="3l"` by default
- Uses `group=1` typically

## See Also

- `CMS_CONNECT_EXECUTION_GUIDE.md` - General execution guide
- `CMS_CONNECT_FILE_TRANSFER.md` - File transfer documentation
- `ANALYSIS_FOLDER_SETUP.md` - Analysis folder setup guide
- `wzAnalysis.py` - The main analysis script

