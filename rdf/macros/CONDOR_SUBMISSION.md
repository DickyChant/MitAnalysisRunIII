# Condor Batch Submission Guide

This guide explains how to submit analysis jobs to Condor batch system.

## Overview

Condor submission involves:
1. **Packaging files**: Create a tarball with all necessary analysis files
2. **Job configuration**: List samples/years to process
3. **Submission**: Create Condor submit files and submit jobs
4. **File transfer**: Condor automatically transfers files to worker nodes
5. **Execution**: Worker nodes extract files, set up environment, run analysis

---

## File Structure

```
rdf/macros/
├── analysis_with_switchSample.py                    # Your analysis script
├── analysis_slurm_with_switchSample.sh              # Analysis runner (called on worker)
├── analysis_condor_with_switchSample.sh             # Environment setup + extraction (runs on worker)
├── analysis_singularity_condor_with_switchSample.sh # Condor executable (wrapper)
├── analysis_submit_condor_with_switchSample.sh      # Submission script (runs on submit node)
├── analysis_with_switchSample_input_condor_jobs.cfg # Job list
└── logs/                                            # Job logs (created automatically)
```

---

## Step-by-Step Process

### Step 1: Create Job Configuration File

Create `analysis_with_switchSample_input_condor_jobs.cfg`:

```
101 20220
101 20221
102 20220
102 20221
```

**Format**: `<switchSample> <year> [no]`
- `switchSample`: Sample ID from `utilsAna.py` (or 0 for custom paths)
- `year`: Year (2016, 2017, 2018, 20220, 20221, 20230, 20231, 20240, 20250)
- `no`: Optional, skip this line if present

### Step 2: Prepare Files

The submission script automatically:
- Creates a tarball (`.tgz`) with all necessary files
- Includes: Python scripts, utilities, data files, configs, weights, etc.

**Files included in tarball:**
- `*Analysis.py` - All analysis scripts
- `analysis_slurm_with_switchSample.sh` - Execution script
- `functions.h` - C++ functions
- `utils*.py` - Utility modules
- `data/*` - Scale factors, weights, etc.
- `weights_mva/*` - MVA weights
- `tmva_helper_xml.*` - TMVA helpers
- `mysf.h` - Scale factor headers
- `jsns/*` - JSON files
- `config/*` - Configuration files
- `jsonpog-integration/*` - JSONPOG integration

### Step 3: Initialize VOMS Proxy

The submission script will prompt for your grid certificate passphrase:

```bash
# This happens automatically in the submission script
voms-proxy-init --voms cms --valid 168:00
```

**Note**: You need `$HOME/.grid-cert-passphrase` file with your passphrase.

### Step 4: Submit Jobs

```bash
# Submit with default settings (condorJob=1001, group=9)
./analysis_submit_condor_with_switchSample.sh

# Or specify job ID and group size
./analysis_submit_condor_with_switchSample.sh 1001 9
```

**What happens:**
1. Creates tarball with all files
2. Reads job configuration file
3. For each sample/year/job combination:
   - Creates Condor submit file
   - Submits job to Condor
4. Jobs are queued and run on available worker nodes

### Step 5: Monitor Jobs

```bash
# Check job queue
condor_q

# Check your jobs only
condor_q -submitter $USER

# Check specific job
condor_q <job_id>

# Check job details
condor_q -long <job_id>

# Watch queue (updates every 5 seconds)
watch -n 5 'condor_q -submitter $USER'
```

### Step 6: Check Logs

```bash
# List log files
ls -lh logs/

# Check output
tail -f logs/analysis_with_switchSample_1001_101_20220_0.out

# Check for errors
grep -i error logs/*.error | head -20

# Count successful jobs
grep -c "DONE" logs/*.out

# Count failed jobs
grep -c "FAILED" logs/*.out
```

### Step 7: Check Output Files

```bash
# List output files
ls -lh fillhisto_analysis_with_switchSample*.root

# Count completed jobs
ls fillhisto_analysis_with_switchSample*.root | wc -l

# Check file sizes (should be > 0)
find . -name "fillhisto_analysis_with_switchSample*.root" -size +0
```

---

## How Condor File Transfer Works

### Automatic File Transfer

Condor uses `transfer_input_files` in the submit file to automatically:
1. **Transfer files TO worker node**: Tarball and execution script
2. **Extract on worker**: Script extracts tarball
3. **Run analysis**: Execute analysis script
4. **Transfer output BACK**: Output files are automatically transferred back

### Transfer Configuration

In the submit file:
```bash
should_transfer_files = YES          # Enable file transfer
when_to_transfer_output = ON_EXIT    # Transfer output when job completes
transfer_input_files = analysis_condor_with_switchSample.sh,${whichAna}.tgz
```

### What Gets Transferred

**Input (to worker):**
- `analysis_condor_with_switchSample.sh` - Setup script
- `${whichAna}.tgz` - Tarball with all analysis files

**Output (from worker):**
- `fillhisto_*.root` - Analysis output files
- Log files (`.out`, `.error`, `.log`)

---

## Complete Example Workflow

```bash
# 1. Create job configuration
cat > analysis_with_switchSample_input_condor_jobs.cfg << EOF
101 20220
102 20220
EOF

# 2. Make sure you have grid certificate passphrase file
# (If you don't have it, create it or modify the script to prompt interactively)

# 3. Submit jobs
./analysis_submit_condor_with_switchSample.sh 1001 9

# 4. Monitor (in another terminal)
watch -n 10 'condor_q -submitter $USER | head -20'

# 5. Check progress
while true; do
  completed=$(ls fillhisto_analysis_with_switchSample*.root 2>/dev/null | wc -l)
  running=$(condor_q -submitter $USER | grep -c " R ")
  idle=$(condor_q -submitter $USER | grep -c " I ")
  echo "Completed: $completed | Running: $running | Idle: $idle"
  sleep 60
done

# 6. Check for failures
grep -l "FAILED" logs/*.out
```

---

## Condor Job States

- **I** (Idle): Job is waiting in queue
- **R** (Running): Job is currently running
- **H** (Held): Job is held (check why with `condor_q -hold`)
- **C** (Completed): Job finished successfully
- **X** (Removed): Job was removed/cancelled

---

## Common Commands

### Job Management

```bash
# Submit jobs
./analysis_submit_condor_with_switchSample.sh [jobID] [group]

# Check status
condor_q -submitter $USER

# Check specific job
condor_q <job_id>

# Hold a job (pause)
condor_hold <job_id>

# Release a held job
condor_release <job_id>

# Remove/cancel a job
condor_rm <job_id>

# Remove all your jobs
condor_rm -all

# Check why job is held
condor_q -hold -long <job_id>
```

### Log Management

```bash
# View latest output
ls -t logs/*.out | head -1 | xargs tail -f

# View latest error
ls -t logs/*.error | head -1 | xargs tail -f

# Search for errors
grep -i error logs/*.error | head -20

# Count jobs by status
grep -c "DONE" logs/*.out
grep -c "FAILED" logs/*.out
grep -c "DONE NO FILES" logs/*.out
```

---

## Troubleshooting

### Issue: "VOMS proxy initialization failed"

**Solution:**
- Check you have grid certificate: `ls ~/.globus/`
- Check passphrase file exists: `ls ~/.grid-cert-passphrase`
- Or modify script to prompt interactively:
  ```bash
  voms-proxy-init --voms cms --valid 168:00
  ```

### Issue: "Tarball creation failed"

**Solution:**
- Check all required files exist
- Check you have write permissions
- Some files might not exist (2>/dev/null suppresses errors for missing files)

### Issue: "Job stuck in Idle (I) state"

**Solution:**
- Check job requirements: `condor_q -long <job_id> | grep Requirements`
- Check if resources are available
- Check if job is held: `condor_q -hold <job_id>`

### Issue: "Job failed immediately"

**Solution:**
- Check error log: `cat logs/*.error | head -50`
- Check if executable exists and is executable
- Check if tarball was transferred correctly
- Check CMSSW environment setup

### Issue: "No output files"

**Solution:**
- Check if analysis completed: `grep "DONE" logs/*.out`
- Check output filename pattern matches
- Check if analysis script creates output files
- Verify `when_to_transfer_output = ON_EXIT` is set

### Issue: "Memory errors"

**Solution:**
- Increase `RequestMemory` in submit file (currently 4000 MB)
- Reduce number of files per job (increase group size)

### Issue: "Disk space errors"

**Solution:**
- Check `RequestDisk = DiskUsage` is set
- Reduce tarball size (exclude unnecessary files)
- Clean up old output files

---

## Customizing File Transfer

### Adding More Files to Tarball

Edit `analysis_submit_condor_with_switchSample.sh`:

```bash
tar cvzf ${whichAna}.tgz \
*Analysis.py analysis_slurm_with_switchSample.sh functions.h utils*.py \
data/* weights_mva/* tmva_helper_xml.* \
mysf.h \
jsns/* config/* jsonpog-integration/* \
your_additional_files/*  # Add here
```

### Excluding Files from Tarball

```bash
tar cvzf ${whichAna}.tgz \
--exclude="*.root" \  # Exclude ROOT files
--exclude="logs/*" \  # Exclude logs
*Analysis.py ...
```

### Transferring Additional Input Files

Edit the submit file generation in the script:

```bash
transfer_input_files = analysis_condor_with_switchSample.sh,${whichAna}.tgz,your_file.txt
```

---

## Advanced: Using Custom Paths

If you want to use custom sample paths instead of switchSample IDs:

### Option 1: Modify execution script

Edit `analysis_slurm_with_switchSample.sh` to handle custom paths:

```bash
if [ $1 -eq 0 ]; then
  # Custom path mode - pass additional arguments
  time python3 $5.py --samplePath=$6 --year=$2 --whichJob=$3 --customXsec=$7 --customCategory=$8
else
  # Normal switchSample mode
  time python3 $5.py --switchSample=$1 --year=$2 --whichJob=$3
fi
```

### Option 2: Create path mapping file

Create a file mapping sample IDs to paths and include it in the tarball.

---

## Best Practices

1. **Test First**: Submit 1-2 jobs to test before submitting all
2. **Monitor Regularly**: Check job status and logs frequently
3. **Keep Logs**: Don't delete logs until jobs complete
4. **Resubmit Promptly**: Fix and resubmit failed jobs
5. **Check Resources**: Ensure enough disk space and quota
6. **Use Job Groups**: Split large samples into multiple jobs
7. **Verify Outputs**: Check output files are created and have reasonable sizes

---

## Quick Reference

```bash
# Submit
./analysis_submit_condor_with_switchSample.sh [jobID] [group]

# Monitor
condor_q -submitter $USER

# Check logs
tail -f logs/*.out

# Cancel all
condor_rm -all

# Check output
ls fillhisto_*.root
```

