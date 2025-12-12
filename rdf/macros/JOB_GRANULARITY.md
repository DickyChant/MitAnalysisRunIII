# Job Granularity Explanation

## Overview

Jobs are **NOT** one big job per sample/year. Instead, each sample/year is **split into multiple smaller jobs** that process subsets of files.

## Job Structure

### Granularity: One Job Per `<switchSample> <year> <whichJob>` Combination

For each entry in your config file:
```
101 20220
```

The submission script creates **multiple Condor jobs** (default: 10 jobs, numbered 0-9).

### Example Breakdown

**Config file:**
```
101 20220
102 20220
```

**With `group=9` (default), this creates:**

| switchSample | year  | whichJob | Job Name | Files Processed |
|--------------|-------|----------|----------|-----------------|
| 101          | 20220 | 0        | Job 0    | Files: 0, 10, 20, 30, ... |
| 101          | 20220 | 1        | Job 1    | Files: 1, 11, 21, 31, ... |
| 101          | 20220 | 2        | Job 2    | Files: 2, 12, 22, 32, ... |
| ...          | ...   | ...      | ...      | ... |
| 101          | 20220 | 9        | Job 9    | Files: 9, 19, 29, 39, ... |
| 102          | 20220 | 0        | Job 0    | Files: 0, 10, 20, 30, ... |
| 102          | 20220 | 1        | Job 1    | Files: 1, 11, 21, 31, ... |
| ...          | ...   | ...      | ...      | ... |
| 102          | 20220 | 9        | Job 9    | Files: 9, 19, 29, 39, ... |

**Total: 20 Condor jobs** (2 samples × 10 jobs each)

## How File Splitting Works

The `groupFiles()` function splits files using Python slicing:

```python
def groupFiles(fIns, group):
    # Creates 'group' number of groups
    # Job 0: files[0], files[group], files[2*group], ...
    # Job 1: files[1], files[group+1], files[2*group+1], ...
    # Job 2: files[2], files[group+2], files[2*group+2], ...
    # ...
    ret = [fIns[i::group] for i in range(group)]
    return ret
```

**Example with 100 files and group=9:**
- Job 0: files[0], files[9], files[18], files[27], ... → ~11 files
- Job 1: files[1], files[10], files[19], files[28], ... → ~11 files
- Job 2: files[2], files[11], files[20], files[29], ... → ~11 files
- ...
- Job 9: files[9], files[18], files[27], files[36], ... → ~11 files

**Note**: With `group=9`, you get 10 jobs (0-9), each processing roughly 1/10th of the files.

## Why Split Into Multiple Jobs?

### Advantages:
1. **Faster completion**: Multiple jobs run in parallel
2. **Better resource utilization**: Jobs can run on different worker nodes
3. **Fault tolerance**: If one job fails, others continue
4. **Memory management**: Each job processes fewer files, reducing memory usage
5. **Checkpointing**: Can resubmit failed jobs individually

### Trade-offs:
- More job management overhead
- More output files to merge later
- More Condor queue entries

## Controlling Granularity

### Option 1: Change Group Size

In `analysis_submit_condor_with_switchSample.sh`:

```bash
group=9  # Default: creates 10 jobs (0-9)

# For fewer, larger jobs:
group=4  # Creates 5 jobs (0-4), each processes ~20% of files

# For more, smaller jobs:
group=19  # Creates 20 jobs (0-19), each processes ~5% of files
```

Or pass as argument:
```bash
./analysis_submit_condor_with_switchSample.sh 1001 4  # group=4
```

### Option 2: Process All Files in One Job

To process all files in a single job (not recommended for large samples):

```bash
# In the submission script, change:
for whichJob in $(seq 0 $group)  # Multiple jobs

# To:
for whichJob in -1  # Single job (processes all files)
```

**Note**: Your analysis script uses `whichJob=-1` to mean "process all files".

### Option 3: Process Specific Jobs Only

Edit the loop in submission script:
```bash
# Process only jobs 0-4 (instead of 0-9)
for whichJob in $(seq 0 4)
```

## Real-World Example

**Config file (`wzAnalysis_input_condor_jobs.cfg`):**
```
101 20220
101 20221
102 20220
102 20221
```

**With `group=9` (default):**
- 4 samples/years × 10 jobs each = **40 Condor jobs**

**Each job:**
- Processes ~10% of files for that sample/year
- Runs independently on a worker node
- Produces one output file: `fillhisto_wzAnalysis1001_sample101_year20220_job0.root`

**After completion:**
- You have 40 output files to merge
- Use `mergeHistograms.py` or similar to combine by sample/year

## Output File Naming

Each job produces:
```
fillhisto_<analysis><condorJob>_sample<switchSample>_year<year>_job<whichJob>.root
```

**Example:**
```
fillhisto_wzAnalysis1001_sample101_year20220_job0.root
fillhisto_wzAnalysis1001_sample101_year20220_job1.root
...
fillhisto_wzAnalysis1001_sample101_year20220_job9.root
```

## Summary

**Granularity:**
- ✅ **Multiple small jobs** per sample/year (default: 10 jobs)
- ❌ **NOT** one big job per sample/year
- Each job processes a subset of files (roughly 1/10th with default settings)

**Benefits:**
- Parallel processing
- Better fault tolerance
- Lower memory usage per job
- Faster overall completion

**To change:**
- Adjust `group` parameter in submission script
- Smaller `group` = fewer, larger jobs
- Larger `group` = more, smaller jobs

