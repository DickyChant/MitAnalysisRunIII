#!/usr/bin/env python3
"""
Generate XRootD file lists for direct NanoAOD analysis (no skim files needed).

For each sample, queries CMS DAS to get the list of raw NanoAOD files, then
writes XRootD URLs to filelists/<sample_id>.txt (MC) or
filelists/data_<type>_<year>.txt (data).

Usage:
    # Resolve a single MC sample (derives DAS name from SwitchSample automatically)
    python3 resolve_sample_files.py --sample=179

    # Resolve all MC samples in a condor jobs config
    python3 resolve_sample_files.py --config=../wzAnalysis_input_condor_jobs.cfg

    # Resolve a data sample with explicit DAS dataset name
    python3 resolve_sample_files.py --data --type=1022 --year=2024 \
        --das="/MuonEG/Run2024C-MINIv6NANOv15-v1/NANOAOD"

    # Resolve a DAS dataset to a custom output file
    python3 resolve_sample_files.py --das="/WZto3LNu_.../NANOAODSIM" --output=filelists/custom.txt

    # Use a specific XRootD redirector (default: cms-xrd-global.cern.ch)
    python3 resolve_sample_files.py --sample=179 --redirector=xrootd-cms.infn.it

Prerequisites:
    - dasgoclient must be available (source CMS environment first)
    - Valid VOMS proxy (voms-proxy-init --voms cms)
"""

import os
import sys
import getopt
from subprocess import check_output, CalledProcessError

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.join(SCRIPT_DIR, "..")
FILELIST_DIR = os.path.join(SCRIPT_DIR, "filelists")

# Add parent for utilsAna imports
sys.path.insert(0, PARENT_DIR)
os.chdir(PARENT_DIR)

XRD_REDIRECTOR = "cms-xrd-global.cern.ch"


def das_query_files(das_dataset, redirector=None):
    """Query DAS for file list and return XRootD URLs."""
    if redirector is None:
        redirector = XRD_REDIRECTOR

    cmd = "dasgoclient -query 'file dataset={0}'".format(das_dataset)
    print("  DAS query: {0}".format(cmd))

    try:
        output = check_output(cmd, shell=True).decode().strip()
    except CalledProcessError as e:
        print("  ERROR: DAS query failed: {0}".format(e))
        return []

    if not output:
        print("  WARNING: DAS returned no files for {0}".format(das_dataset))
        return []

    files = []
    for line in output.split('\n'):
        line = line.strip()
        if line and line.startswith('/store/'):
            url = "root://{0}/{1}".format(redirector, line)
            files.append(url)

    print("  Found {0} files".format(len(files)))
    return files


def dataset_name_from_switch_sample(sample_id, skim_type="3l"):
    """Derive DAS dataset name from SwitchSample directory path."""
    from utilsAna import SwitchSample

    try:
        info = SwitchSample(sample_id, skim_type)
    except (KeyError, Exception) as e:
        print("  ERROR: SwitchSample({0}) failed: {1}".format(sample_id, e))
        return None

    dir_path = info[0]
    # Extract dataset directory name (last path component)
    dataset_dir = os.path.basename(dir_path)
    # Convert skim format (A+B+C) to DAS format (/A/B/C)
    das_name = "/" + dataset_dir.replace("+", "/")
    return das_name


def resolve_mc_sample(sample_id, skim_type="3l", redirector=None):
    """Resolve an MC sample to XRootD file list."""
    print("Resolving MC sample {0}...".format(sample_id))

    das_name = dataset_name_from_switch_sample(sample_id, skim_type)
    if not das_name:
        return False

    print("  DAS dataset: {0}".format(das_name))
    files = das_query_files(das_name, redirector)

    if not files:
        return False

    outpath = os.path.join(FILELIST_DIR, "{0}.txt".format(sample_id))
    os.makedirs(os.path.dirname(outpath), exist_ok=True)

    with open(outpath, 'w') as f:
        f.write("# MC sample {0}\n".format(sample_id))
        f.write("# DAS: {0}\n".format(das_name))
        f.write("# {0} files\n".format(len(files)))
        for url in sorted(files):
            f.write(url + "\n")

    print("  Written to {0}".format(outpath))
    return True


def resolve_data_sample(sample_type, year, das_name, redirector=None):
    """Resolve a data sample to XRootD file list."""
    print("Resolving data type={0} year={1}...".format(sample_type, year))
    print("  DAS dataset: {0}".format(das_name))

    files = das_query_files(das_name, redirector)

    if not files:
        return False

    outpath = os.path.join(FILELIST_DIR, "data_{0}_{1}.txt".format(sample_type, year))
    os.makedirs(os.path.dirname(outpath), exist_ok=True)

    # Append if file exists (data samples often span multiple DAS datasets)
    mode = 'a' if os.path.exists(outpath) else 'w'
    with open(outpath, mode) as f:
        if mode == 'w':
            f.write("# Data type={0} year={1}\n".format(sample_type, year))
        f.write("# DAS: {0}\n".format(das_name))
        f.write("# {0} files\n".format(len(files)))
        for url in sorted(files):
            f.write(url + "\n")

    print("  Written to {0} (mode={1})".format(outpath, mode))
    return True


def resolve_from_config(config_path, skim_type="3l", redirector=None):
    """Resolve all MC samples in a condor jobs config file."""
    if not os.path.exists(config_path):
        print("ERROR: Config file not found: {0}".format(config_path))
        return False

    print("Reading config: {0}".format(config_path))
    n_ok = 0
    n_fail = 0
    n_skip = 0
    n_data = 0

    with open(config_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            sample_id = int(parts[0])
            skip = parts[2] if len(parts) > 2 else ""

            if skip == "no":
                n_skip += 1
                continue

            if sample_id >= 1000:
                # Data sample - cannot auto-resolve, skip
                n_data += 1
                print("Skipping data sample {0} (use --data --type=... --das=... to resolve manually)".format(
                    sample_id))
                continue

            # Check if file list already exists
            outpath = os.path.join(FILELIST_DIR, "{0}.txt".format(sample_id))
            if os.path.exists(outpath):
                print("Skipping MC sample {0} (file list already exists)".format(sample_id))
                n_ok += 1
                continue

            if resolve_mc_sample(sample_id, skim_type, redirector):
                n_ok += 1
            else:
                n_fail += 1

    print("\n" + "="*60)
    print("Summary: {0} resolved, {1} failed, {2} skipped, {3} data (manual)".format(
        n_ok, n_fail, n_skip, n_data))
    return n_fail == 0


def resolve_das_to_file(das_name, output_path, redirector=None):
    """Resolve a DAS dataset to a specific output file."""
    print("Resolving DAS dataset: {0}".format(das_name))

    files = das_query_files(das_name, redirector)

    if not files:
        return False

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("# DAS: {0}\n".format(das_name))
        f.write("# {0} files\n".format(len(files)))
        for url in sorted(files):
            f.write(url + "\n")

    print("Written {0} files to {1}".format(len(files), output_path))
    return True


def main():
    valid = ['sample=', 'config=', 'data', 'type=', 'year=', 'das=',
             'output=', 'redirector=', 'skim=', 'force', 'help']

    usage = """Usage:
  resolve_sample_files.py --sample=<id>                  # Single MC sample
  resolve_sample_files.py --config=<path>                # All MC in config
  resolve_sample_files.py --data --type=<id> --year=<y> --das=<name>  # Data
  resolve_sample_files.py --das=<name> --output=<path>   # Custom DAS query

Options:
  --sample=ID      MC sample ID (from SwitchSample)
  --config=PATH    Condor jobs config file
  --data           Data mode (requires --type, --year, --das)
  --type=ID        Data sample type (e.g. 1022 for MuonEG)
  --year=YEAR      Data year (e.g. 2024)
  --das=NAME       DAS dataset name (e.g. /MuonEG/Run2024C-.../NANOAOD)
  --output=PATH    Custom output file path
  --redirector=HOST  XRootD redirector (default: cms-xrd-global.cern.ch)
  --skim=TYPE      Skim type for SwitchSample lookup (default: 3l)
  --force          Overwrite existing file lists
"""

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", valid)
    except getopt.GetoptError as ex:
        print(usage)
        print(str(ex))
        sys.exit(1)

    sample = None
    config = None
    is_data = False
    sample_type = None
    year = None
    das_name = None
    output = None
    redirector = None
    skim_type = "3l"

    for opt, arg in opts:
        if opt == "--help":
            print(usage)
            sys.exit(0)
        if opt == "--sample":
            sample = int(arg)
        if opt == "--config":
            config = arg
        if opt == "--data":
            is_data = True
        if opt == "--type":
            sample_type = int(arg)
        if opt == "--year":
            year = int(arg)
        if opt == "--das":
            das_name = arg
        if opt == "--output":
            output = arg
        if opt == "--redirector":
            redirector = arg
        if opt == "--skim":
            skim_type = arg

    # Mode 1: Custom DAS query to output file
    if das_name and output:
        ok = resolve_das_to_file(das_name, output, redirector)
        sys.exit(0 if ok else 1)

    # Mode 2: Data sample
    if is_data:
        if not (sample_type and year and das_name):
            print("Data mode requires --type, --year, and --das")
            print(usage)
            sys.exit(1)
        ok = resolve_data_sample(sample_type, year, das_name, redirector)
        sys.exit(0 if ok else 1)

    # Mode 3: Single MC sample
    if sample is not None:
        ok = resolve_mc_sample(sample, skim_type, redirector)
        sys.exit(0 if ok else 1)

    # Mode 4: Config file (all MC)
    if config:
        ok = resolve_from_config(config, skim_type, redirector)
        sys.exit(0 if ok else 1)

    print(usage)
    sys.exit(1)


if __name__ == "__main__":
    main()
