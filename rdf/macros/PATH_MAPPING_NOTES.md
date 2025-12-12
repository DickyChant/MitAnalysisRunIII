# Path Mapping for Transferred Files

## Overview

When files are transferred from CMS Connect storage to remote Condor worker nodes, they end up in different locations than their original paths. This document explains how the path mapping system works.

## The Problem

1. **Original paths**: Files are at paths like `/home/scratch/stqian/wz_guillermo/skims_2022a/3l/SampleName/file.root`
2. **Transferred paths**: Files end up in the worker node's working directory, possibly as just `file.root` or with some preserved structure
3. **Analysis code**: Calls `getMClist()` or `getDATAlist()` which call `findDIR()` with directory paths
4. **Issue**: `findDIR()` tries to walk the original directory path, which doesn't exist on the worker node

## The Solution

### Step 1: File List Creation (Submission Time)

At submission time, `collect_files_for_job.py` creates a file list with original paths:
```
/home/scratch/stqian/wz_guillermo/skims_2022a/3l/SampleName/file1.root
/home/scratch/stqian/wz_guillermo/skims_2022a/3l/SampleName/file2.root
...
```

### Step 2: File Transfer

Condor transfers these files to the worker node. They may be:
- Flattened to just the filename: `file1.root`, `file2.root`
- Preserved with some path structure: `skims_2022a/3l/SampleName/file1.root`
- In the working directory or subdirectories

### Step 3: Mapping Creation (Worker Node)

On the worker node, `analysis_condor_wzAnalysis.sh` creates a mapping file:
```
/home/scratch/.../file1.root    /path/to/worker/dir/file1.root
/home/scratch/.../file2.root    /path/to/worker/dir/file2.root
```

### Step 4: Path Resolution (Analysis Time)

When the analysis calls `getMClist()` or `getDATAlist()`:

1. These functions call `findDIR()` with a directory path
2. `findDIR()` checks if files were transferred (`CMS_CONNECT_FILES_TRANSFERRED`)
3. If yes, it uses the mapping to find files whose original paths match the directory
4. Returns the transferred file paths instead of trying to walk the original directory

## How It Works

### In `findDIR()`:

```python
# If files were transferred and directory doesn't exist locally
if CMS_CONNECT_FILES_TRANSFERRED and not os.path.exists(accessDir):
    mapping = loadFileMapping()
    if mapping:
        # Find files whose original path matches the directory
        for origPath, transPath in mapping.items():
            if origPath.startswith(directory):
                # Use the transferred path
                rootFiles.push_back(transPath)
```

### In `resolvePathForRemote()`:

```python
# First check if files were transferred and use mapping
if CMS_CONNECT_FILES_TRANSFERRED:
    mapping = loadFileMapping()
    if localPath in mapping:
        # Return the transferred path
        return mapping[localPath]
```

## File Mapping Format

The mapping file (`file_path_mapping.txt`) has the format:
```
<original_path>    <transferred_path>
```

Example:
```
/home/scratch/stqian/wz_guillermo/skims_2022a/3l/SampleName/file1.root    /tmp/condor_work/file1.root
/home/scratch/stqian/wz_guillermo/skims_2022a/3l/SampleName/file2.root    /tmp/condor_work/file2.root
```

## Testing

To verify the mapping works:

1. **Check mapping file exists**:
   ```bash
   cat file_path_mapping.txt
   ```

2. **Check files exist at transferred paths**:
   ```bash
   while read orig trans; do
     if [ -f "$trans" ]; then
       echo "OK: $trans"
     else
       echo "MISSING: $trans"
     fi
   done < file_path_mapping.txt
   ```

3. **Test path resolution**:
   ```python
   from utilsAna import resolvePathForRemote, loadFileMapping
   import os
   os.environ['CMS_CONNECT_FILES_TRANSFERRED'] = '1'
   mapping = loadFileMapping()
   print(f"Loaded {len(mapping)} mappings")
   # Test with an original path
   testPath = "/home/scratch/stqian/wz_guillermo/skims_2022a/3l/SampleName/file1.root"
   resolved = resolvePathForRemote(testPath)
   print(f"Original: {testPath}")
   print(f"Resolved: {resolved}")
   ```

## Troubleshooting

### Files Not Found

If `findDIR()` can't find files:

1. **Check mapping file exists and has entries**:
   ```bash
   wc -l file_path_mapping.txt
   ```

2. **Check directory matching**:
   - The directory path must match the beginning of original file paths
   - Example: Directory `/home/scratch/.../3l/SampleName/` should match files like `/home/scratch/.../3l/SampleName/file.root`

3. **Check transferred files exist**:
   ```bash
   find . -name "*.root" -type f
   ```

### Mapping Not Working

If the mapping isn't being used:

1. **Check environment variable**:
   ```bash
   echo $CMS_CONNECT_FILES_TRANSFERRED
   # Should be "1"
   ```

2. **Check mapping file location**:
   ```bash
   echo $CMS_CONNECT_FILE_MAPPING
   # Should point to file_path_mapping.txt
   ```

3. **Verify mapping is loaded**:
   - Look for "Loaded X file path mappings" in the output

## Notes

- The mapping is created once per job and cached
- Directory paths are normalized (trailing slashes removed) for matching
- If a file isn't found in the mapping, the system falls back to searching the current directory
- The mapping handles both individual file paths and directory-based lookups

