# Connecting Skimming Output to Analysis

This guide explains how to connect your custom skimming output (from `make_wz_guillermo_folder.sh`) to the analysis framework.

## Understanding the Structure

### Skimming Output Structure

Your skimming produces files in:
```
/home/scratch/stqian/wz_guillermo/skims/
├── 1l/
│   └── <sampleName>/
│       └── output_1l_<sample>_<job>.root
├── 2l/
│   └── <sampleName>/
│       └── output_2l_<sample>_<job>.root
├── 3l/
│   └── <sampleName>/
│       └── output_3l_<sample>_<job>.root
└── met/
    └── <sampleName>/
        └── output_met_<sample>_<job>.root
```

Where `<sampleName>` is the dataset name from your `skim_input_samples_*_fromDAS.cfg` file.

### Analysis Expected Structure

The analysis framework expects files in:
```
/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/<skimType>/
└── <dataset_path>/
    └── *.root files
```

Where `<dataset_path>` is the full dataset name like:
`DYto2L-2Jets_MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM`

## Solution Options

### Option 1: Modify SwitchSample() Function (Recommended)

Modify `utilsAna.py` to point to your skimming output directory.

**Step 1: Edit `utilsAna.py`**

Find the `SwitchSample()` function (around line 799) and modify the `dirT2` variable:

```python
def SwitchSample(argument, skimType):
    # Original line:
    # dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
    
    # Change to your skimming output location:
    dirT2 = "/home/scratch/stqian/wz_guillermo/skims/" + skimType
    dirLocal = "/work/submit/mariadlf/Hrare/D01"
    
    # ... rest of the function stays the same
```

**Step 2: Update Sample Paths**

The `SwitchSample()` function maps sample IDs to dataset paths. You need to ensure the `<sampleName>` in your skimming output matches the dataset path expected by the analysis.

**Option A: If your sample names match exactly**

If your `skim_input_samples_*_fromDAS.cfg` uses the same dataset names as in `SwitchSample()`, you're done!

**Option B: If sample names differ**

You may need to create a mapping. For example, if your skimming uses shorter names, you could:

1. Create a mapping dictionary in `utilsAna.py`
2. Or create symlinks from the expected names to your actual names
3. Or modify `SwitchSample()` to use your sample naming convention

### Option 2: Create Symlinks

Create symlinks from the expected location to your actual skimming output:

```bash
# Create the expected directory structure
mkdir -p /ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/2l

# For each sample, create a symlink
# Example: if your sample is named "DYto2L-2Jets_MLL-10to50_2022"
# and the analysis expects "DYto2L-2Jets_MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM"

SKIM_OUTPUT="/home/scratch/stqian/wz_guillermo/skims"
ANALYSIS_EXPECTED="/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit"

# Create symlink for 2l skim
ln -s "${SKIM_OUTPUT}/2l/YourSampleName" "${ANALYSIS_EXPECTED}/2l/ExpectedDatasetName"

# Repeat for other skim types (1l, 3l, met, pho)
```

### Option 3: Copy Files to Expected Location

Copy your skimming output to the expected location:

```bash
SKIM_OUTPUT="/home/scratch/stqian/wz_guillermo/skims"
ANALYSIS_EXPECTED="/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit"

# Copy 2l files
cp -r "${SKIM_OUTPUT}/2l/"* "${ANALYSIS_EXPECTED}/2l/"

# Repeat for other skim types
```

**Note:** This uses more disk space but ensures compatibility.

### Option 4: Environment Variable Override (Advanced)

Modify `utilsAna.py` to check for an environment variable:

```python
def SwitchSample(argument, skimType):
    # Check for custom skimming directory
    custom_skim_dir = os.environ.get('CUSTOM_SKIM_DIR', None)
    if custom_skim_dir:
        dirT2 = custom_skim_dir + "/" + skimType
    else:
        dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
    
    # ... rest of function
```

Then set the environment variable before running:
```bash
export CUSTOM_SKIM_DIR="/home/scratch/stqian/wz_guillermo/skims"
./analysis_submit_slurm.sh 1  # for wzAnalysis
```

## Matching Sample Names

The key challenge is matching your skimming sample names to the dataset paths expected by the analysis.

### Check Your Sample Names

```bash
# Check what sample names your skimming uses
cd /home/scratch/stqian/wz_guillermo
cat skim_input_samples_2022a_fromDAS.cfg | head -5

# Check what the analysis expects
cd /home/stqian/MitAnalysisRunIII/rdf/macros
grep -A 1 "^100:" utilsAna.py | head -3
```

### Create a Mapping Script

If names don't match, create a Python script to map them:

```python
# map_samples.py
sample_mapping = {
    # Your skimming name: Analysis expected name
    "DYto2L-2Jets_MLL-10to50_2022": "DYto2L-2Jets_MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",
    # Add more mappings...
}
```

Then modify `SwitchSample()` to use this mapping.

## Recommended Workflow

1. **First, check sample name compatibility:**
   ```bash
   # List your skimming output samples
   ls /home/scratch/stqian/wz_guillermo/skims/2l/
   
   # Check what analysis expects (for sample ID 100, 2l skim)
   cd /home/stqian/MitAnalysisRunIII/rdf/macros
   python3 -c "from utilsAna import SwitchSample; print(SwitchSample(100, '2l')[0])"
   ```

2. **If names match or are close:**
   - Use **Option 1** (modify `dirT2` in `SwitchSample()`)
   - This is the cleanest solution

3. **If names are very different:**
   - Use **Option 2** (symlinks) or **Option 3** (copy files)
   - Or create a mapping function

4. **Test with a single sample:**
   ```bash
   # Run analysis on one sample to verify
   ./analysis_slurm.sh 100 20230 0 1001 wzAnalysis
   ```

## Example: Complete Setup for wz_guillermo

Assuming your skimming output is at `/home/scratch/stqian/wz_guillermo/skims/`:

1. **Edit `utilsAna.py`:**
   ```python
   def SwitchSample(argument, skimType):
       # Use your custom skimming directory
       dirT2 = "/home/scratch/stqian/wz_guillermo/skims/" + skimType
       # ... rest unchanged
   ```

2. **Verify the sample paths match:**
   - Check that sample names in your `skim_input_samples_*_fromDAS.cfg` 
   - Match (or can be mapped to) the dataset paths in `SwitchSample()`

3. **Run the analysis:**
   ```bash
   cd /home/stqian/MitAnalysisRunIII/rdf/macros
   ./analysis_submit_slurm.sh 1 1001  # wzAnalysis
   ```

## Troubleshooting

### Issue: "No files found" error

**Solution:** Check that:
1. The directory path is correct
2. Sample names match between skimming and analysis
3. Files actually exist: `ls /home/scratch/stqian/wz_guillermo/skims/2l/<sampleName>/`

### Issue: Sample ID not found

**Solution:** 
- Check that your `*_input_condor_jobs.cfg` uses sample IDs that exist in `SwitchSample()`
- Or add new sample IDs to `SwitchSample()` for your custom samples

### Issue: Wrong skim type

**Solution:**
- Make sure you're using the correct `skimType` parameter
- For WZ analysis, it's typically `"2l"` or `"3l"`
- Check what `skimType` your analysis uses in the `readMCSample()` function

## Additional Notes

- The analysis framework uses `findDIR()` to recursively search for `.root` files in the specified directory
- File names don't need to match exactly, as long as they're `.root` files in the right directory
- The `findDIR()` function will find all `.root` files recursively, so the exact file naming (`output_2l_*_*.root`) should work fine

