# Direct NanoAOD Analysis (No Skim Files)

This subfolder provides an alternative analysis workflow that **reads raw NanoAOD
directly from the CMS grid via XRootD**, completely eliminating the need for
pre-produced skim files.

## Why?

The standard workflow requires:
1. **Skimming**: Copy raw NanoAOD from CMS grid → apply loose preselection → store locally (~TB scale)
2. **Analysis**: Read skim files → apply full selection → produce histograms

For **CMS Connect**, skims are problematic because:
- Require TB-scale local storage
- Condor must transfer skim files to each worker node (slow, disk-heavy)
- Must keep skims in sync with analysis changes

The **direct mode** fuses steps 1 and 2:
- Worker nodes read raw NanoAOD directly from XRootD (the CMS grid)
- RDataFrame's lazy evaluation only reads branches needed for each Filter
- The analysis selections naturally subsume the skim preselection
- No local storage or data transfer needed

## Trade-offs

| | Standard (skim) | Direct (XRootD) |
|---|---|---|
| Storage needed | ~TB (local skims) | ~GB (code only) |
| Condor transfer | Heavy (skim files) | Light (code tarball) |
| Per-job speed | Fast (local I/O) | Slower (network I/O) |
| Setup effort | Skim + validate | Generate file lists |
| Submission speed | Slow (collect files) | Fast (no file collection) |

**Bottom line**: Direct mode is ideal for CMS Connect where local storage is
limited and network access to the grid is available.

## Quick Start

### 1. Generate XRootD file lists

You need a valid VOMS proxy and `dasgoclient` available (CMS environment).

```bash
# Generate file lists for all MC samples in the WZ config
python3 resolve_sample_files.py --config=../wzAnalysis_input_condor_jobs.cfg

# Generate a single MC sample
python3 resolve_sample_files.py --sample=179

# Generate a data sample (need to specify DAS name explicitly)
python3 resolve_sample_files.py --data --type=1022 --year=2024 \
    --das="/MuonEG/Run2024C-MINIv6NANOv15-v1/NANOAOD"
```

File lists are written to `filelists/`:
- MC: `filelists/<sample_id>.txt` (e.g., `filelists/179.txt`)
- Data: `filelists/data_<type>_<year>.txt` (e.g., `filelists/data_1022_2024.txt`)

### 2. Submit Condor jobs

```bash
# Submit WZ analysis
./submit_condor.sh 1 1001

# Submit with more job groups (more parallelism)
./submit_condor.sh 1 1001 4
```

### 3. Run interactively (from rdf/macros/ directory)

```bash
cd ..  # go to rdf/macros/
USE_DIRECT_NANOAOD=1 FILELIST_DIR=direct/filelists \
    python3 wzAnalysis.py --process=179 --year=20220 --whichJob=0
```

## How It Works

1. `resolve_sample_files.py` derives DAS dataset names from the existing
   `SwitchSample()` mapping in `utilsAna.py`, then queries DAS for file paths
   and writes XRootD URLs to `filelists/`.

2. When `USE_DIRECT_NANOAOD=1` is set, `utilsAna.py`'s `getMClist()` and
   `getDATAlist()` read from `FILELIST_DIR` instead of walking local skim
   directories. Everything else (selections, weights, histograms) is identical.

3. Worker nodes set up CMS environment (for ROOT/XRootD), extract the code
   tarball, enable direct mode, and run the analysis. Data streams from the
   CMS grid in real-time via XRootD.

## File List Format

Each file list is a text file with one XRootD URL per line:

```
# MC sample 179
# DAS: /WZto3LNu-2Jets_QCD_TuneCP5_.../NANOAODSIM
# 42 files
root://cms-xrd-global.cern.ch//store/mc/Run3Summer22NanoAODv12/.../file_0.root
root://cms-xrd-global.cern.ch//store/mc/Run3Summer22NanoAODv12/.../file_1.root
...
```

Lines starting with `#` are comments and are ignored.

## Data Samples

For data, DAS dataset names cannot be auto-derived from `SwitchSample` (they are
hardcoded in `getDATAlist()`). You must specify them explicitly:

```bash
# Example: MuonEG Run2024C
python3 resolve_sample_files.py --data --type=1022 --year=2024 \
    --das="/MuonEG/Run2024C-MINIv6NANOv15-v1/NANOAOD"

# Multiple runs: just run again (appends to same file)
python3 resolve_sample_files.py --data --type=1022 --year=2024 \
    --das="/MuonEG/Run2024D-MINIv6NANOv15-v1/NANOAOD"
```

The data DAS names follow the pattern visible in `utilsAna.py`'s `getDATAlist()`:
- Skim directory: `Muon0+Run2024C-MINIv6NANOv15-v1+NANOAOD`
- DAS name: `/Muon0/Run2024C-MINIv6NANOv15-v1/NANOAOD`

## Troubleshooting

### XRootD connection issues
If jobs fail with XRootD errors, try a different redirector:
```bash
python3 resolve_sample_files.py --sample=179 --redirector=xrootd-cms.infn.it
```

Or set XRootD environment variables in `analysis_condor.sh`:
```bash
export XRD_NETWORKSTACK=IPv4
export XRD_REQUESTTIMEOUT=600
```

### Slow jobs
Direct mode jobs are inherently slower than skim-based jobs because they read
more data over the network. To compensate:
- Increase `group` (more jobs per sample, fewer files per job)
- Use a geographically closer XRootD redirector

### Missing file lists
```
FileNotFoundError: File list not found: direct/filelists/179.txt
```
Generate it: `python3 resolve_sample_files.py --sample=179`

### DAS query fails
Ensure:
- VOMS proxy is valid: `voms-proxy-info`
- CMS environment is set up: `cmsenv`
- `dasgoclient` is available: `which dasgoclient`
