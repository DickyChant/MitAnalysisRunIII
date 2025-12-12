# Batch Submission Quick Start

## Quick Setup (5 minutes)

### 1. Create Job Configuration File

```bash
cat > analysis_with_switchSample_input_condor_jobs.cfg << EOF
101 20220
101 20221
102 20220
102 20221
EOF
```

Format: `<switchSample> <year> [no]`

### 2. Submit Jobs (SLURM)

```bash
# Submit with default settings (group=9, condorJob=1001)
./analysis_submit_slurm_with_switchSample.sh

# Or specify job ID and group size
./analysis_submit_slurm_with_switchSample.sh 1001 9
```

### 3. Monitor Jobs

```bash
# Check job queue
squeue -u $USER

# Watch queue (updates every 5 seconds)
watch -n 5 'squeue -u $USER'

# Check logs
tail -f logs/analysis_with_switchSample_1001_101_20220_0_*.out
```

### 4. Check Results

```bash
# List output files
ls -lh fillhisto_analysis_with_switchSample*.root

# Count completed jobs
ls fillhisto_analysis_with_switchSample*.root | wc -l

# Check for failures
grep -c "FAILED" logs/*.out
```

---

## File Structure

```
rdf/macros/
├── analysis_with_switchSample.py          # Your analysis script
├── analysis_slurm_with_switchSample.sh    # Execution script (runs on worker)
├── analysis_submit_slurm_with_switchSample.sh  # Submission script
├── analysis_with_switchSample_input_condor_jobs.cfg  # Job list
└── logs/                                   # Job logs (created automatically)
```

---

## Common Commands

### SLURM

```bash
# Submit jobs
./analysis_submit_slurm_with_switchSample.sh [jobID] [group]

# Check status
squeue -u $USER

# Cancel job
scancel <job_id>

# Cancel all your jobs
scancel -u $USER

# Check job details
scontrol show job <job_id>
```

### Check Logs

```bash
# View latest log
ls -t logs/*.out | head -1 | xargs tail -f

# Check for errors
grep -i error logs/*.error | head -20

# Count successful jobs
grep -c "DONE" logs/*.out

# Count failed jobs
grep -c "FAILED" logs/*.out
```

---

## Example: Complete Workflow

```bash
# 1. Create job list
cat > analysis_with_switchSample_input_condor_jobs.cfg << EOF
101 20220
102 20220
EOF

# 2. Submit jobs
./analysis_submit_slurm_with_switchSample.sh 1001 9

# 3. Monitor (in another terminal)
watch -n 10 'squeue -u $USER | head -20'

# 4. Check progress
while true; do
  completed=$(ls fillhisto_analysis_with_switchSample*.root 2>/dev/null | wc -l)
  total=$(grep -v "^#" analysis_with_switchSample_input_condor_jobs.cfg | grep -v "no" | wc -l)
  echo "Completed: $completed / $((total * 10)) jobs"
  sleep 60
done

# 5. Check for failures
grep -l "FAILED" logs/*.out
```

---

## Troubleshooting

### Jobs not starting
- Check cluster status: `sinfo`
- Check resource limits: `squeue -u $USER -o "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"`

### Jobs failing
- Check error logs: `cat logs/*.error | head -50`
- Check if Python script exists: `ls analysis_with_switchSample.py`
- Check if files are accessible

### No output files
- Check if analysis completed: `grep "DONE" logs/*.out`
- Check output filename pattern matches in execution script
- Verify analysis script creates output files

---

## For More Details

See `BATCH_SUBMISSION.md` for:
- Detailed explanation of each step
- Condor submission (instead of SLURM)
- Custom path handling
- Advanced monitoring and resubmission

