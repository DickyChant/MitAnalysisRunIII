# WZ Guillermo Skimming Guide

This guide explains how to set up and run skimming jobs for the wz_guillermo analysis using condor.

## Setup

### Step 1: Create the skimming folder

From the repository root:

```bash
cd rdf/skimming
./make_wz_guillermo_folder.sh
```

This will create a complete skimming setup at `/home/scratch/stqian/wz_guillermo` with:
- All necessary skimming scripts
- Configuration files (config/, jsns/)
- CMSSW environment setup
- Condor submission script

### Step 2: Generate input file lists

Navigate to the new folder and generate input file lists from DAS:

```bash
cd /home/scratch/stqian/wz_guillermo

# Generate input files for a specific year
python make_skim_input_files_fromDAS.py \
    --inputCfg=skim_input_samples_2022a_fromDAS.cfg \
    --outputCfg=skim_input_files_fromDAS.cfg \
    --outputForCondorCfg=skim_input_condor_jobs_fromDAS.cfg \
    --group=5
```

This creates:
- `skim_input_files_fromDAS.cfg` - List of all input files
- `skim_input_condor_jobs_fromDAS.cfg` - Job configuration for condor

## Running Condor Jobs

### Basic Usage

```bash
cd /home/scratch/stqian/wz_guillermo
./skim_condor_wz_guillermo.sh <YEAR> [outputDir]
```

**Arguments:**
- `YEAR`: Data year (e.g., `2022a`, `2023b`, `2024a`)
- `outputDir`: (optional) Output directory for skimmed files
  - Default: `/home/scratch/stqian/wz_guillermo/skims`

**Example:**
```bash
# Use default output directory
./skim_condor_wz_guillermo.sh 2022a

# Specify custom output directory
./skim_condor_wz_guillermo.sh 2022a /home/scratch/stqian/wz_guillermo/skims_2022a
```

### What the Script Does

1. **Validates setup**: Checks that all required files exist
2. **Sets up VOMS proxy**: Initializes CMS VOMS proxy for xrootd access
3. **Creates tarball**: Packages all necessary files (`skim.tgz`)
4. **Creates output directories**: Sets up directory structure for each sample
5. **Submits jobs**: Submits one condor job per sample/job combination

### Output Structure

The skimmed files will be organized as:

```
<outputDir>/
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

## Monitoring Jobs

### Check Job Status

```bash
# List all your condor jobs
condor_q

# List jobs with details
condor_q -better-analyze

# Check specific job
condor_q <job_id>
```

### View Logs

Logs are stored in the `logs/` directory:

```bash
cd /home/scratch/stqian/wz_guillermo

# View output log
tail -f logs/simple_skim_<sample>_<job>.out

# View error log
tail -f logs/simple_skim_<sample>_<job>.error

# View condor log
tail -f logs/simple_skim_<sample>_<job>.log
```

### Check for Failed Jobs

```bash
# List failed jobs
condor_q | grep FAILED

# Get details on failed jobs
condor_q -better-analyze <job_id>
```

## Troubleshooting

### VOMS Proxy Issues

If you get proxy errors:

```bash
# Initialize proxy (if you have a passphrase file)
voms-proxy-init --voms cms --valid 168:00 -pwstdin < $HOME/.grid-cert-passphrase

# Or interactively
voms-proxy-init --voms cms --valid 168:00

# Check proxy status
voms-proxy-info -all
```

### Missing Input Files

If condor jobs fail because input files are missing:

1. Check that `skim_input_files_fromDAS.cfg` was generated correctly
2. Verify files are accessible:
   ```bash
   xrdfs root://xrootd-cms.infn.it/ ls <file_path>
   ```

### Output Directory Issues

If jobs complete but output files are missing:

1. Check the job logs for errors
2. Verify output directory permissions:
   ```bash
   ls -ld /home/scratch/stqian/wz_guillermo/skims
   ```
3. Check disk space:
   ```bash
   df -h /home/scratch/stqian/wz_guillermo
   ```

### Resubmitting Failed Jobs

To resubmit specific failed jobs, you can either:

1. **Manual resubmission**: Edit the condor submit file and resubmit
2. **Re-run the script**: The script will skip existing output directories, but you may want to remove failed job outputs first

## Advanced Usage

### Running Specific Samples Only

Edit `skim_input_condor_jobs_fromDAS.cfg` to include only the samples you want, then run the submission script.

### Adjusting Resources

Edit `skim_condor_wz_guillermo.sh` to modify:
- `RequestMemory`: Memory per job (default: 6000 MB)
- `RequestCpus`: CPUs per job (default: 1)
- `RequestDisk`: Disk space (default: DiskUsage)

### Custom Site Requirements

Modify the `+DESIRED_Sites` line in the condor submit file to specify preferred sites.

## Integration with Analysis

After skimming is complete:

1. **Verify outputs**: Check that all expected files were created
2. **Update analysis configs**: Point your analysis scripts to the skimmed files
3. **Run analysis**: Use the analysis scripts in `rdf/macros/` with the skimmed files

Example analysis command:
```bash
cd /home/stqian/MitAnalysisRunIII/rdf/macros
python wzAnalysis.py --process=0 --year=20220 --whichJob=-1
```

## Notes

- The default output directory uses local paths. If you need to write to a remote storage (e.g., EOS), modify the `outputDir` parameter in `skim.py` or pass a root:// URL as the output directory.
- Jobs are submitted with accounting group `analysis.stqian`. Make sure this matches your condor setup.
- The script creates output directories automatically, but ensure you have write permissions.

## Support

For issues:
1. Check condor logs in `logs/` directory
2. Review this README for common issues
3. Check the main repository README.md
4. Contact the MIT CMS group

