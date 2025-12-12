# Year-Dependent Skim Paths

## Overview

Both `SwitchSample()` and `getDATAlist()` now accept a `year` parameter, allowing you to configure year-dependent skim locations. This aligns the two functions and enables better organization of skim files by year.

## Function Signatures

### SwitchSample (MC Samples)

```python
def SwitchSample(argument, skimType, year=None):
    # argument: sample ID
    # skimType: "1l", "2l", "3l", "met", etc.
    # year: year (optional, for backward compatibility)
```

### getDATAlist (Data Samples)

```python
def getDATAlist(type, year, skimType):
    # type: data sample type (1000-1059)
    # year: year (required)
    # skimType: "1l", "2l", "3l", "met", etc.
```

### getMClist (MC Samples - Helper)

```python
def getMClist(sampleNOW, skimType, year=None):
    # sampleNOW: sample ID
    # skimType: "1l", "2l", "3l", "met", etc.
    # year: year (optional, passed to SwitchSample)
```

## Setting Year-Dependent Paths

### In `utilsAna.py` - `SwitchSample()` Function

**Location**: Line ~799

```python
def SwitchSample(argument, skimType, year=None):
    # Normalize year format (handle era format like 20220, 20221, etc.)
    if year is not None and year > 10000:
        year = year // 10
    
    # Year-dependent base directory
    if year is not None:
        # Example: year-specific paths
        if year == 2022:
            dirT2 = "/path/to/2022/skims/" + skimType
        elif year == 2023:
            dirT2 = "/path/to/2023/skims/" + skimType
        elif year == 2024:
            dirT2 = "/path/to/2024/skims/" + skimType
        elif year == 2025:
            dirT2 = "/path/to/2025/skims/" + skimType
        else:
            # Default path
            dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
    else:
        # Default when year not specified (backward compatibility)
        dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
```

### In `utilsAna.py` - `getDATAlist()` Function

**Location**: Line ~185

```python
def getDATAlist(type, year, skimType):
    if(year > 10000): year = year // 10
    
    # Year-dependent base directory (same structure as SwitchSample)
    if year == 2022:
        dirT2 = "/path/to/2022/skims/" + skimType
    elif year == 2023:
        dirT2 = "/path/to/2023/skims/" + skimType
    elif year == 2024:
        dirT2 = "/path/to/2024/skims/" + skimType
    elif year == 2025:
        dirT2 = "/path/to/2025/skims/" + skimType
    else:
        dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
```

## Example: Complete Year-Dependent Setup

### Scenario: Different skim locations per year

```python
# In SwitchSample() and getDATAlist()

if year == 2022:
    dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_2022/" + skimType
elif year == 2023:
    dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_2023/" + skimType
elif year == 2024:
    dirT2 = "/home/scratch/stqian/wz_guillermo/skims_2024/" + skimType
elif year == 2025:
    dirT2 = "/home/scratch/stqian/wz_guillermo/skims_2025/" + skimType
else:
    dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
```

### Directory Structure

```
/path/to/2022/skims/
├── 2l/
│   └── <sampleName>/
│       └── *.root
└── 3l/
    └── <sampleName>/
        └── *.root

/path/to/2023/skims/
├── 2l/
│   └── <sampleName>/
│       └── *.root
└── 3l/
    └── <sampleName>/
        └── *.root
```

## Usage

### In Analysis Scripts

The year is automatically passed when using `getMClist()`:

```python
# In your analysis script
files = getMClist(switchSample, skimType, year)  # year is passed through
```

### In `analysis_with_switchSample.py`

The year is automatically passed:

```python
# Year is already available in the script
sample_info = SwitchSample(switchSample, skimType, year)
files = getMClist(switchSample, skimType, year)
```

### Backward Compatibility

If `year=None` is passed (or not passed), the function uses the default path:

```python
# Old code still works (uses default path)
SwitchSample(101, "2l")  # year=None, uses default

# New code with year
SwitchSample(101, "2l", 2022)  # uses year-specific path
```

## Year Format Handling

The function automatically handles different year formats:

- **Standard format**: `2022`, `2023`, `2024` → used as-is
- **Era format**: `20220`, `20221`, `20230`, `20231` → converted to `2022`, `2023` by dividing by 10

```python
# Both work the same:
SwitchSample(101, "2l", 2022)   # Standard format
SwitchSample(101, "2l", 20220)  # Era format (converted to 2022)
```

## Benefits

1. **Consistency**: MC and data samples use the same path structure
2. **Organization**: Skims can be organized by year
3. **Flexibility**: Different years can use different storage locations
4. **Backward Compatible**: Old code without year parameter still works

## Migration Guide

### Existing Code

**Before:**
```python
files = getMClist(switchSample, skimType)
sample_info = SwitchSample(switchSample, skimType)
```

**After (with year):**
```python
files = getMClist(switchSample, skimType, year)  # Add year
sample_info = SwitchSample(switchSample, skimType, year)  # Add year
```

**Note**: Old code without `year` still works (uses default path).

### Updating Existing Analysis Scripts

If you want to use year-dependent paths in existing analysis scripts:

1. **Find calls to `SwitchSample()`**:
   ```python
   # Old
   SwitchSample(sampleNOW, skimType)
   
   # New
   SwitchSample(sampleNOW, skimType, year)
   ```

2. **Find calls to `getMClist()`**:
   ```python
   # Old
   getMClist(sampleNOW, skimType)
   
   # New
   getMClist(sampleNOW, skimType, year)
   ```

3. **Update function signatures** if you're calling these in custom functions.

## Example: Custom Year-Dependent Paths

```python
def SwitchSample(argument, skimType, year=None):
    if year is not None and year > 10000:
        year = year // 10
    
    if year is not None:
        # Custom paths per year
        if year == 2022:
            # 2022 skims in one location
            dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_2022/" + skimType
        elif year == 2023:
            # 2023 skims in another location
            dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_2023/" + skimType
        elif year == 2024:
            # 2024 skims in custom location
            dirT2 = "/home/scratch/stqian/wz_guillermo/skims_2024/" + skimType
        else:
            # Default for other years
            dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
    else:
        # Default when year not specified
        dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
```

## Summary

- ✅ `SwitchSample()` now accepts `year` parameter (optional, backward compatible)
- ✅ `getMClist()` passes `year` to `SwitchSample()`
- ✅ `getDATAlist()` already had `year` parameter
- ✅ Both functions can use the same year-dependent path logic
- ✅ Old code without `year` still works (uses default path)

**To enable year-dependent paths**: Uncomment and customize the year-specific path logic in both `SwitchSample()` and `getDATAlist()` functions in `utilsAna.py`.

