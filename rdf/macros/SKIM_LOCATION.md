# Setting Skim Locations

This guide explains where and how to configure the location of your skimmed files.

## Option 1: Modify `utilsAna.py` (Recommended for Global Change)

The main location where skim paths are set is in **`utilsAna.py`**.

### For MC Samples: `SwitchSample()` Function

**Location**: Line ~802 in `utilsAna.py`

```python
def SwitchSample(argument, skimType):
    # Current default:
    dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
    
    # Change to your location:
    dirT2 = "/home/scratch/stqian/wz_guillermo/skims/" + skimType
    # OR
    dirT2 = "/path/to/your/skims/" + skimType
    
    dirLocal = "/work/submit/mariadlf/Hrare/D01"
    # ... rest of function
```

**What it does:**
- Sets the base directory for MC sample lookups
- `skimType` is appended (e.g., "2l", "3l", "1l", "met")
- Used by `getMClist()` function

**Example:**
- If `skimType = "2l"` and `dirT2 = "/home/scratch/stqian/wz_guillermo/skims/"`
- Final path: `/home/scratch/stqian/wz_guillermo/skims/2l/`

### For Data Samples: `getDATAlist()` Function

**Location**: Line ~191 in `utilsAna.py`

```python
def getDATAlist(type, year, skimType):
    if(year > 10000): year = year // 10
    
    # Current default:
    dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
    
    # Change to your location:
    dirT2 = "/home/scratch/stqian/wz_guillermo/skims/" + skimType
    
    # ... rest of function
```

**What it does:**
- Sets the base directory for data sample lookups
- Used when processing data samples (switchSample >= 1000)

---

## Option 2: Use `--samplePath` in `analysis_with_switchSample.py` (Per-Job Override)

If you want to specify a custom path for individual jobs without modifying `utilsAna.py`:

```bash
python3 analysis_with_switchSample.py \
    --samplePath=/home/scratch/stqian/wz_guillermo/skims/2l/DYto2L-2Jets_MLL-50 \
    --year=2022 \
    --customXsec=6345.99 \
    --customCategory=kPlotDY
```

**Advantages:**
- No need to modify `utilsAna.py`
- Can use different paths for different jobs
- Works with custom skimming output

**Limitations:**
- Requires specifying cross section and category manually
- Not compatible with standard batch submission (would need to modify submission script)

---

## Option 3: Environment Variable (Advanced)

You can modify `utilsAna.py` to check for an environment variable:

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

Then set before running:
```bash
export CUSTOM_SKIM_DIR="/home/scratch/stqian/wz_guillermo/skims"
python3 analysis_with_switchSample.py --switchSample=101 --year=2022
```

---

## Option 4: Modify Submission Script (For Batch Jobs)

If you want to use custom paths in batch submission, you can modify the execution script:

**Edit `analysis_slurm_with_switchSample.sh`:**

```bash
# Add path mapping or use samplePath for specific samples
if [ $1 -eq 0 ]; then
  # Custom path for sample ID 0
  time python3 $5.py --samplePath=/custom/path --year=$2 --whichJob=$3 --customXsec=1000
else
  # Normal switchSample lookup
  time python3 $5.py --switchSample=$1 --year=$2 --whichJob=$3
fi
```

---

## Recommended Approach

### For Most Users: Modify `utilsAna.py`

**Step 1**: Edit `utilsAna.py`

```python
# Line ~802 in SwitchSample()
def SwitchSample(argument, skimType):
    # Change this line:
    dirT2 = "/home/scratch/stqian/wz_guillermo/skims/" + skimType
    # ... rest unchanged
```

**Step 2**: Also update `getDATAlist()` if processing data:

```python
# Line ~191 in getDATAlist()
def getDATAlist(type, year, skimType):
    # Change this line:
    dirT2 = "/home/scratch/stqian/wz_guillermo/skims/" + skimType
    # ... rest unchanged
```

**Step 3**: Verify sample names match

Make sure your skim directory structure matches what `SwitchSample()` expects:

```
/home/scratch/stqian/wz_guillermo/skims/
├── 2l/
│   └── DYto2L-2Jets_MLL-50_TuneCP5_.../
│       └── *.root files
├── 3l/
│   └── ...
└── 1l/
    └── ...
```

The sample directory name should match (or be mappable to) the dataset path in `SwitchSample()`.

---

## Quick Reference

| Method | Location | Use Case |
|--------|----------|----------|
| **Option 1** | `utilsAna.py` line 802 | Global change for all jobs |
| **Option 1** | `utilsAna.py` line 191 | Global change for data samples |
| **Option 2** | `--samplePath` flag | Per-job custom paths |
| **Option 3** | Environment variable | Temporary/testing |
| **Option 4** | Submission script | Batch jobs with custom paths |

---

## Example: Complete Setup

**1. Check your current skim location:**
```bash
ls /home/scratch/stqian/wz_guillermo/skims/2l/
```

**2. Check what analysis expects:**
```bash
cd /home/stqian/MitAnalysisRunIII/rdf/macros
python3 -c "from utilsAna import SwitchSample; print(SwitchSample(101, '2l')[0])"
```

**3. If paths don't match, edit `utilsAna.py`:**
```python
# In SwitchSample() function
dirT2 = "/home/scratch/stqian/wz_guillermo/skims/" + skimType
```

**4. Test:**
```bash
python3 analysis_with_switchSample.py --switchSample=101 --year=20220 --whichJob=-1
```

**5. Verify files are found:**
- Check output for "Total files found: X"
- Should be > 0 if path is correct

---

## Troubleshooting

### "No files found" error

**Check:**
1. Path is correct in `utilsAna.py`
2. Sample directory name matches expected name
3. Files actually exist: `ls /your/path/skims/2l/<sampleName>/`
4. Files are `.root` files

### Sample name mismatch

**Solution:**
- Create symlinks from expected name to your actual name
- Or modify `SwitchSample()` to use your naming convention
- Or use `--samplePath` for individual samples

### Path not accessible from worker nodes

**For Condor:**
- Ensure path is accessible from worker nodes
- May need to use shared filesystem (e.g., `/ceph/submit/`)
- Or ensure files are transferred (not typical for large skim files)

---

## Summary

**Easiest method**: Edit `dirT2` in `utilsAna.py` at:
- Line ~802 in `SwitchSample()` (for MC)
- Line ~191 in `getDATAlist()` (for data)

This changes the skim location globally for all analyses.

