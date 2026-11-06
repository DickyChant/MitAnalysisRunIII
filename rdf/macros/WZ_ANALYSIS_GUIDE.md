# Analysis Guide

This guide explains how to run analyses on CMS Connect using Condor with file transfer.

## Overview

All analyses use the same submission infrastructure. Each analysis has its own skim type:
- **wzAnalysis** (code 1): skimType="3l", default group=1
- **fakeAnalysis** (code 5): skimType="1l", default group=9
- **triggerAnalysis** (code 6): skimType="2l", default group=9
- **metAnalysis** (code 7): skimType="met", default group=9
- **puAnalysis** (code 9): skimType="2l", default group=9

## Submission Workflow

There are two rounds of submission. Round 1 produces supporting inputs (fake rates, trigger SFs, pileup weights, MET corrections) that the WZ analysis depends on. Round 2 runs the WZ analysis itself.

### Round 1: Supporting Analyses

```bash
# Submit supporting analyses (in any order, they are independent)
./submit_condor.sh 5 1001    # fakeAnalysis
./submit_condor.sh 6 1001    # triggerAnalysis
./submit_condor.sh 7 1001    # metAnalysis
./submit_condor.sh 9 1001    # puAnalysis
```

After all Round 1 jobs finish, merge and compute the supporting results:
```bash
python3 mergeHistograms.py --path=fillhisto_fakeAnalysis --year=20220 --output=anaFake
python3 mergeHistograms.py --path=fillhisto_triggerAnalysis --year=20220 --output=anaTrigger
# etc. for each year
```

### Round 2: WZ Analysis

```bash
./submit_condor.sh 1 1001    # wzAnalysis
```

## Quick Start

### Step 1: Setup Analysis Folder (if not done)

```bash
cd /home/stqian/MitAnalysisRunIII/rdf/macros
./makeAnalysisFolders.sh
cd /home/scratch/stqian/analysis
```

### Step 2: Verify Job Configuration

Each analysis has a config file: `<analysis>_input_condor_jobs.cfg`

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

Make sure `utilsAna.py` points to your skim files:

```bash
python3 -c "from utilsAna import SwitchSample; print(SwitchSample(179, '3l', 20220)[0])"
```

### Step 4: Test File Collection

```bash
python3 collect_files_for_job.py 179 20220 0 3l 2
```

This should output ROOT file paths. If empty, check paths in `utilsAna.py`.

### Step 5: Submit Jobs

```bash
chmod +x submit_condor.sh analysis_*.sh

# Submit with analysis code
./submit_condor.sh <anaCode> [condorJob] [group]

# Examples:
./submit_condor.sh 1          # WZ with defaults (condorJob=1001, group=1)
./submit_condor.sh 1 1001 1   # WZ with explicit params
./submit_condor.sh 5 1001     # fake with defaults (group=9)
./submit_condor.sh 5 1001 9   # fake with explicit group
```

**Parameters**:
- `anaCode`: 1=wz, 5=fake, 6=trigger, 7=met, 9=pu
- `condorJob`: Job ID prefix for output naming (default: 1001)
- `group`: Number of job groups 0-N (default depends on analysis)

### Step 6: Monitor Jobs

```bash
condor_q -submitter $USER
watch -n 5 'condor_q -submitter $USER'
```

### Step 7: Check Logs

```bash
ls -lh logs/
tail -f logs/wzAnalysis_1001_179_20220_0.out
grep -i error logs/*.error | head -20
grep -c "DONE" logs/*.out
grep -c "FAILED" logs/*.out
```

### Step 8: Check Output Files

```bash
ls -lh fillhisto_wzAnalysis*.root
ls fillhisto_wzAnalysis*.root | wc -l
```

## Command Line Arguments

All analyses use:
- `--process=<sample_id>`
- `--year=<year>`
- `--whichJob=<job_id>` (-1 for all files)

## Output Files

Output files are named:
```
fillhisto_<analysis><condorJob>_sample<sample>_year<year>_job<job>.root
```

Example:
```
fillhisto_wzAnalysis1001_sample179_year20220_job0.root
```

## Running Interactively (for testing)

```bash
python3 wzAnalysis.py --process=179 --year=20220 --whichJob=-1
```

## Troubleshooting

### No Files Found

1. Check that skim files exist at the expected path
2. Verify path in `utilsAna.py`:
   ```bash
   python3 -c "from utilsAna import SwitchSample; print(SwitchSample(179, '3l', 20220)[0])"
   ```
3. Test file collection:
   ```bash
   python3 collect_files_for_job.py 179 20220 0 3l 2
   ```

### Job Fails

```bash
cat logs/wzAnalysis_1001_179_20220_0.error
cat logs/wzAnalysis_1001_179_20220_0.out
```

Common issues: missing VOMS proxy, files not accessible, missing data files, disk space.

## See Also

- `submit_condor.sh` — CMS Connect submission script (all analyses)
- `collect_files_for_job.py` — File collection utility
- `analysis_condor.sh` — Worker node script
- `analysis_runner.sh` — Analysis execution script
