# Analysis Folder Setup Guide

This guide explains how to create the analysis directory structure in your scratch folder, similar to how the skimming folder is set up.

## Quick Start

### Step 1: Create Analysis Folder

From the macros directory:

```bash
cd /home/stqian/MitAnalysisRunIII/rdf/macros
./make_analysis_folder.sh
```

This will create a complete analysis setup at `/home/scratch/stqian/analysis` with:
- All necessary analysis scripts
- Directory structure for outputs
- Configuration files
- Helper scripts

### Step 2: Check Setup

Navigate to the new folder and verify everything is set up correctly:

```bash
cd /home/scratch/stqian/analysis
./check_setup.sh
```

This will verify that all required files and directories are present.

### Step 3: Configure Jobs

Edit the job configuration file:

```bash
# Edit the job configuration
nano analysis_with_switchSample_input_condor_jobs.cfg
```

Format: `<switchSample> <year> [no]` (one per line)

Example:
```
101 20220
102 20220
101 20221
```

### Step 4: Verify File Paths

Make sure `utilsAna.py` points to your skim files. Check the paths in:
- `SwitchSample()` function (for MC samples)
- `getDATAlist()` function (for data samples)

These should point to where your skimming output files are located (e.g., `/home/scratch/stqian/wz_guillermo/skims/`).

### Step 5: Submit Jobs

```bash
./analysis_submit_condor_with_switchSample.sh 1001 9
```

## Directory Structure

The script creates the following structure:

```
/home/scratch/stqian/analysis/
├── outputs/          # Analysis output files (organized by skim type)
│   ├── 1l/
│   ├── 2l/
│   ├── 3l/
│   ├── met/
│   └── pho/
├── histograms/       # Histogram output files
├── logs/            # Condor job logs (created automatically)
├── file_lists/       # File lists for job submission (created automatically)
├── configs/          # Configuration files
├── config/           # Analysis configuration (copied from macros)
├── jsns/             # JSON files (copied from macros)
├── data/              # Scale factors, weights, etc. (copied from macros)
├── weights_mva/      # MVA weights (copied from macros)
├── *.py              # Analysis scripts
├── *.sh              # Submission scripts
├── *.h               # Header files
├── analysis_with_switchSample_input_condor_jobs.cfg  # Job configuration
├── check_setup.sh    # Setup verification script
└── README.md          # This guide
```

## What Gets Copied

The script copies:

**Analysis Scripts:**
- `*Analysis.py` - All analysis scripts (wzAnalysis.py, zzAnalysis.py, etc.)
- `analysis_with_switchSample.py` - Generic analysis script
- `utils*.py` - Utility modules
- `collect_files_for_job.py` - File collection script

**Submission Scripts:**
- `analysis_*.sh` - All submission scripts

**Supporting Files:**
- `*.h` - Header files (functions.h, mysf.h, etc.)
- `config/` - Configuration directory
- `jsns/` - JSON files directory
- `data/` - Scale factors and weights
- `weights_mva/` - MVA weights
- `jsonpog-integration/` - JSONPOG integration

## Customization

### Change Target Directory

Edit `make_analysis_folder.sh` and change:
```bash
TARGET_DIR="/home/scratch/stqian/analysis"
```
to your desired location.

### Keep Existing Directory

By default, the script will create a new directory. If you want to keep an existing directory, comment out the removal section in the script:
```bash
# if [ -d "$TARGET_DIR" ]; then
#     echo "Removing existing directory: $TARGET_DIR"
#     rm -rf "$TARGET_DIR"
# fi
```

## Integration with Skimming

If you've run skimming and have output files at `/home/scratch/stqian/wz_guillermo/skims/`, make sure your `utilsAna.py` points to these files:

```python
# In SwitchSample() function
if year == 20220:
    dirT2 = "/home/scratch/stqian/wz_guillermo/skims_2022a/" + skimType
elif year == 20221:
    dirT2 = "/home/scratch/stqian/wz_guillermo/skims_2022b/" + skimType
# etc.
```

## Running Analysis

After setup, you can run analysis jobs:

```bash
cd /home/scratch/stqian/analysis

# 1. Create/edit job configuration
nano analysis_with_switchSample_input_condor_jobs.cfg

# 2. Submit jobs
./analysis_submit_condor_with_switchSample.sh 1001 9

# 3. Monitor jobs
condor_q -submitter $USER

# 4. Check outputs
ls -lh fillhisto_*.root
```

## Troubleshooting

### Setup Check Fails

If `check_setup.sh` reports errors:

1. **Missing files**: Re-run `make_analysis_folder.sh` or manually copy missing files
2. **Missing directories**: Create them manually:
   ```bash
   mkdir -p outputs/{1l,2l,3l,met,pho} histograms logs file_lists configs
   ```

### Files Not Found

If analysis can't find input files:

1. Check paths in `utilsAna.py` (SwitchSample and getDATAlist functions)
2. Verify skim files exist:
   ```bash
   ls /home/scratch/stqian/wz_guillermo/skims/2l/
   ```
3. Test file collection:
   ```bash
   python3 collect_files_for_job.py 101 20220 0 2l 10
   ```

### Permission Issues

If you get permission errors:

```bash
# Make scripts executable
chmod +x *.sh
chmod +x collect_files_for_job.py

# Check directory permissions
ls -ld /home/scratch/stqian/analysis
```

## Comparison with Skimming Setup

This script follows the same pattern as `make_wz_guillermo_folder.sh`:

| Feature | Skimming | Analysis |
|---------|----------|----------|
| Target Directory | `/home/scratch/stqian/wz_guillermo` | `/home/scratch/stqian/analysis` |
| Output Structure | `skims/{1l,2l,3l,met,pho}/<sample>/` | `outputs/{1l,2l,3l,met,pho}/` |
| Main Script | `skim.py` | `*Analysis.py` |
| Submission | `skim_condor_wz_guillermo.sh` | `analysis_submit_condor_with_switchSample.sh` |
| Setup Script | `make_wz_guillermo_folder.sh` | `make_analysis_folder.sh` |

## Next Steps

After setting up the analysis folder:

1. **Verify skim files exist** and are accessible
2. **Update paths in utilsAna.py** to point to your skim files
3. **Create job configuration** with samples you want to process
4. **Test file collection** for a sample before submitting many jobs
5. **Submit jobs** and monitor progress
6. **Check outputs** and verify results

## See Also

- `CMS_CONNECT_EXECUTION_GUIDE.md` - Detailed execution guide
- `CMS_CONNECT_FILE_TRANSFER.md` - File transfer documentation
- `CONDOR_SUBMISSION.md` - General Condor submission guide
- `WZ_GUILLERMO_README.md` (in skimming folder) - Skimming setup guide

