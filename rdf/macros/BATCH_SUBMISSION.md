# Batch Submission Guide

This guide explains how to submit analysis jobs to batch systems (SLURM or Condor).

## Overview

The batch submission workflow consists of:
1. **Job Configuration File**: Lists samples and years to process
2. **Submission Script**: Creates and submits batch jobs
3. **Execution Script**: Runs the actual analysis (called by batch system)
4. **Monitoring**: Check job status and logs

---

## Step 1: Create Job Configuration File

Create a configuration file listing all samples and years to process.

**Format**: `<analysis>_input_condor_jobs.cfg`
```
<switchSample> <year> [passSel]
<switchSample> <year> [passSel]
...
```

**Example**: `analysis_with_switchSample_input_condor_jobs.cfg`
```
101 20220
101 20221
102 20220
102 20221
100 20230
100 20231
```

- **switchSample**: Sample ID (from `utilsAna.py` or use 0 for custom paths)
- **year**: Year (2016, 2017, 2018, 20220, 20221, 20230, 20231, 20240, 20250)
- **passSel**: Optional "no" to skip this line

**For custom paths**, you can use a placeholder sample ID (e.g., 0) and handle it in the submission script.

---

## Step 2: Create Execution Script

The execution script is what actually runs on the worker node.

### For SLURM: `analysis_slurm_with_switchSample.sh`

```bash
#!/bin/bash

echo "hostname"
hostname
whoami

# Setup CMSSW environment (if needed)
# cd ~/releases/CMSSW_14_1_4/src/
# eval `scramv1 runtime -sh`
# cd -

echo "Parameters: " $1 $2 $3 $4 $5

# $1 = switchSample
# $2 = year
# $3 = whichJob
# $4 = condorJob (job ID for output naming)
# $5 = analysisName

time python3 $5.py --switchSample=$1 --year=$2 --whichJob=$3
status=$?

if [ -f "fillhisto_$5_sample$1_year$2_job$3.root" ]; then
  mv fillhisto_$5_sample$1_year$2_job$3.root fillhisto_$5$4_sample$1_year$2_job$3.root
  echo "DONE"

elif [ $status -eq 0 ]; then
  echo "DONE NO FILES"

else
  echo "FAILED"

fi
```

**Make it executable:**
```bash
chmod +x analysis_slurm_with_switchSample.sh
```

### For Condor: `analysis_condor_with_switchSample.sh`

```bash
#!/bin/sh

source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc7_amd64_gcc12
scramv1 project CMSSW CMSSW_13_3_1
cd CMSSW_13_3_1/src/
eval `scramv1 runtime -sh`
cd ../..

voms-proxy-info

tar xzf $5.tgz

echo $PWD

./analysis_slurm_with_switchSample.sh $1 $2 $3 $4 $5

rm -rf functions* *.pyc $5.tgz \
*Analysis.py analysis_slurm.sh functions.h utils*.py \
data weights_mva tmva_helper_xml.* \
mysf.* \
jsns config jsonpog-integration 

ls -l
```

---

## Step 3: Create Submission Script

### For SLURM: `analysis_submit_slurm_with_switchSample.sh`

```bash
#!/bin/sh

if [ $# -lt 1 ]; then
   echo "Usage: $0 <analysis_number> [condorJob]"
   echo "  analysis_number: 0=zAnalysis, 1=wzAnalysis, etc."
   echo "  condorJob: Job ID for output naming (default: 1001)"
   exit
fi

theAna=$1
whichAna="analysis_with_switchSample"  # Your analysis script name
group=9  # Number of job groups (0 to group)

condorJob=1001
if [ $# -gt 1 ]; then
  condorJob=$2
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Read job configuration file
while IFS= read -r line; do

  set -- $line
  whichSample=$1
  whichYear=$2
  passSel=$3

  if [ "${passSel}" != "no" ]; then

    # Loop over job groups
    for whichJob in $(seq 0 $group); do

      # Create SLURM submission script
      cat << EOF > submit
#!/bin/bash
#SBATCH --job-name=${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}
#SBATCH --output=logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}_%j.out
#SBATCH --error=logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}_%j.error
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=3000M
#SBATCH --time=04:00:00
srun ./analysis_slurm_with_switchSample.sh ${whichSample} ${whichYear} ${whichJob} ${condorJob} ${whichAna}
EOF

      sbatch submit
      sleep 0.1

    done

  fi

done < ${whichAna}_input_condor_jobs.cfg

rm -f submit
echo "All jobs submitted!"
```

**Make it executable:**
```bash
chmod +x analysis_submit_slurm_with_switchSample.sh
```

### For Condor: `analysis_submit_condor_with_switchSample.sh`

```bash
#!/bin/sh

if [ $# -lt 1 ]; then
   echo "Usage: $0 <analysis_number> [condorJob]"
   exit
fi

theAna=$1
whichAna="analysis_with_switchSample"
group=9

condorJob=1001
if [ $# -ge 2 ]; then
  condorJob=$2
fi

USERPROXY=`id -u`
echo ${USERPROXY}

# Initialize VOMS proxy
voms-proxy-init --voms cms --valid 168:00 -pwstdin < $HOME/.grid-cert-passphrase

# Create tarball with all necessary files
tar cvzf ${whichAna}.tgz \
*Analysis.py analysis_slurm_with_switchSample.sh functions.h utils*.py \
data/* weights_mva/* tmva_helper_xml.* \
mysf.h \
jsns/* config/* jsonpog-integration/*

# Create logs directory
mkdir -p logs

# Read job configuration file
while IFS= read -r line; do

  set -- $line
  whichSample=$1
  whichYear=$2
  passSel=$3

  if [ "${passSel}" != "no" ]; then

    for whichJob in $(seq 0 $group); do

      # Create Condor submission file
      cat << EOF > submit
Universe   = vanilla
Executable = analysis_condor_with_switchSample.sh
Arguments  = ${whichSample} ${whichYear} ${whichJob} ${condorJob} ${whichAna}
RequestMemory = 4000
RequestCpus = 1
RequestDisk = DiskUsage
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
Log    = logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.log
Output = logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.out
Error  = logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.error
transfer_input_files = analysis_condor_with_switchSample.sh,${whichAna}.tgz
use_x509userproxy = True
x509userproxy = /tmp/x509up_u${USERPROXY}
Requirements = ( BOSCOCluster =!= "t3serv008.mit.edu" && BOSCOCluster =!= "ce03.cmsaf.mit.edu" && BOSCOCluster =!= "eofe8.mit.edu") && (Machine != "t3btch003.mit.edu")
+DESIRED_Sites = "mit_tier2,mit_tier3"
Queue
EOF

      condor_submit submit

    done

  fi

done < ${whichAna}_input_condor_jobs.cfg

rm -f submit
echo "All jobs submitted!"
```

**Make it executable:**
```bash
chmod +x analysis_submit_condor_with_switchSample.sh
```

---

## Step 4: Using Custom Paths in Batch Submission

If you want to use custom paths instead of switchSample IDs, you can modify the submission script:

### Option A: Modify the execution script to handle custom paths

```bash
# In analysis_slurm_with_switchSample.sh
if [ $1 -eq 0 ]; then
  # Use custom path mode
  # You'll need to pass path, xsec, category as additional arguments
  time python3 $5.py --samplePath=$6 --year=$2 --whichJob=$3 --customXsec=$7 --customCategory=$8
else
  # Use switchSample mode
  time python3 $5.py --switchSample=$1 --year=$2 --whichJob=$3
fi
```

### Option B: Create a mapping file

Create a file mapping sample IDs to custom paths:

```bash
# custom_paths.cfg
# Format: switchSample path xsec category
0 /path/to/sample1 6345.99 kPlotDY
1 /path/to/sample2 19982.5 kPlotDY
```

Then modify the submission script to read this mapping.

---

## Step 5: Submit Jobs

### SLURM Submission

```bash
# Submit all jobs
./analysis_submit_slurm_with_switchSample.sh 0 1001

# Check job status
squeue -u $USER

# Check specific job
scontrol show job <job_id>

# Cancel a job
scancel <job_id>

# Cancel all your jobs
scancel -u $USER
```

### Condor Submission

```bash
# Submit all jobs
./analysis_submit_condor_with_switchSample.sh 0 1001

# Check job status
condor_q

# Check specific job
condor_q <job_id>

# Cancel a job
condor_rm <job_id>

# Cancel all your jobs
condor_rm -all
```

---

## Step 6: Monitor Jobs

### Check Log Files

```bash
# List all log files
ls -lh logs/

# Check a specific job's output
tail -f logs/analysis_with_switchSample_1001_101_20220_0_*.out

# Check for errors
grep -i error logs/*.error

# Check for "DONE" messages
grep "DONE" logs/*.out

# Check for "FAILED" messages
grep "FAILED" logs/*.out
```

### Check Output Files

```bash
# List output files
ls -lh fillhisto_analysis_with_switchSample*.root

# Check file sizes (should be > 0)
find . -name "fillhisto_analysis_with_switchSample*.root" -size +0

# Count completed jobs
ls fillhisto_analysis_with_switchSample*.root | wc -l
```

---

## Step 7: Resubmit Failed Jobs

### Manual Resubmission

```bash
# Find failed jobs
grep -l "FAILED" logs/*.out | while read logfile; do
  # Extract job parameters from log filename
  # Format: logs/analysis_with_switchSample_1001_101_20220_0_12345.out
  basename $logfile | sed 's/.*_\([0-9]*\)_\([0-9]*\)_\([0-9]*\)_\([0-9]*\)_.*/.\/analysis_slurm_with_switchSample.sh \2 \3 \4 1001 analysis_with_switchSample/'
done
```

### Automated Resubmission Script

```bash
#!/bin/bash
# resubmit_failed_jobs.sh

condorJob=1001
whichAna="analysis_with_switchSample"

# Find failed jobs
grep -l "FAILED" logs/*.out | while read logfile; do
  # Parse filename: logs/analysis_with_switchSample_1001_101_20220_0_12345.out
  filename=$(basename $logfile)
  parts=($(echo $filename | tr '_' ' '))
  
  whichSample=${parts[3]}
  whichYear=${parts[4]}
  whichJob=${parts[5]}
  
  echo "Resubmitting: sample=$whichSample year=$whichYear job=$whichJob"
  
  # Create and submit job
  cat << EOF > submit
#!/bin/bash
#SBATCH --job-name=${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}
#SBATCH --output=logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}_%j.out
#SBATCH --error=logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}_%j.error
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=3000M
srun ./analysis_slurm_with_switchSample.sh ${whichSample} ${whichYear} ${whichJob} ${condorJob} ${whichAna}
EOF
  
  sbatch submit
  sleep 0.1
done

rm -f submit
```

---

## Complete Example Workflow

### 1. Create job configuration file

```bash
cat > analysis_with_switchSample_input_condor_jobs.cfg << EOF
101 20220
101 20221
102 20220
102 20221
EOF
```

### 2. Create execution script

```bash
# Copy and modify analysis_slurm.sh
cp analysis_slurm.sh analysis_slurm_with_switchSample.sh
# Edit to use --switchSample instead of --process
```

### 3. Create submission script

```bash
# Copy and modify analysis_submit_slurm.sh
cp analysis_submit_slurm.sh analysis_submit_slurm_with_switchSample.sh
# Edit to use your analysis name and execution script
```

### 4. Make scripts executable

```bash
chmod +x analysis_slurm_with_switchSample.sh
chmod +x analysis_submit_slurm_with_switchSample.sh
```

### 5. Submit jobs

```bash
./analysis_submit_slurm_with_switchSample.sh 0 1001
```

### 6. Monitor

```bash
# Watch job queue
watch -n 5 'squeue -u $USER'

# Check logs
tail -f logs/analysis_with_switchSample_1001_101_20220_0_*.out
```

### 7. Check results

```bash
# List output files
ls -lh fillhisto_analysis_with_switchSample*.root

# Check for failures
grep -c "FAILED" logs/*.out
```

---

## Tips and Best Practices

1. **Start Small**: Test with 1-2 samples before submitting all jobs
2. **Check Resources**: Ensure you have enough disk space and quota
3. **Monitor Regularly**: Check job status and logs frequently
4. **Use Job Groups**: Split large samples into multiple jobs (whichJob)
5. **Keep Logs**: Don't delete log files until jobs complete successfully
6. **Resubmit Promptly**: Fix and resubmit failed jobs quickly
7. **Check Outputs**: Verify output files are created and have reasonable sizes

---

## Troubleshooting

### Jobs stuck in queue
- Check if cluster is busy: `squeue` or `condor_q`
- Check resource requirements (memory, CPU, time)
- Try reducing memory/CPU requests

### Jobs failing immediately
- Check execution script is executable
- Check Python script path is correct
- Check all required files are present

### "No files found" errors
- Verify file paths are correct
- Check files actually exist
- Verify sample names match

### Memory errors
- Increase `--mem-per-cpu` in SLURM script
- Increase `RequestMemory` in Condor script
- Reduce number of files per job (increase group size)

### Timeout errors
- Increase `--time` in SLURM script
- Split jobs into smaller groups

