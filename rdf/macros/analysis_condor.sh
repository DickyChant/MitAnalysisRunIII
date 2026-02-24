#!/bin/sh

# This script runs on the Condor worker node (CMS Connect)
# It sets up the environment, extracts the tarball, and runs the analysis

source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc7_amd64_gcc12
scramv1 project CMSSW CMSSW_13_3_1 # cmsrel is an alias not on the workers
cd CMSSW_13_3_1/src/
eval `scramv1 runtime -sh` # cmsenv is an alias not on the workers
cd ../..

voms-proxy-info

# Enable CMS Connect mode - files are transferred, not accessed remotely
export CMS_CONNECT_MODE=1
export CMS_CONNECT_FILES_TRANSFERRED=1

# Extract the tarball containing all analysis files
tar xzf $5.tgz

# Check for file list and set up transferred files
fileListName="${5}_${4}_${1}_${2}_${3}.txt"

if [ -f "${fileListName}" ]; then
  echo "Setting up transferred files from file list: ${fileListName}"

  # Files are transferred directly (not in a tarball)
  # They will be in the current working directory with their original paths
  # We need to create a mapping from original paths to transferred file locations

  # Create a mapping file that tells the analysis where to find files
  echo "Creating file path mapping..."
  python3 << 'PYEOF'
import os
import sys

fileListName = sys.argv[1]
cwd = os.getcwd()

# Read original file paths
originalPaths = []
if os.path.exists(fileListName):
    with open(fileListName, 'r') as f:
        originalPaths = [line.strip() for line in f if line.strip()]

# Create mapping: original path -> transferred path
# Condor transfers files to the working directory
# Files may be flattened (just basename) or preserve some path structure
mapping = {}
for origPath in originalPaths:
    filename = os.path.basename(origPath)
    foundPath = None

    # Try 1: Look for file by basename in current directory (most common case)
    if os.path.exists(filename):
        foundPath = os.path.abspath(filename)

    # Try 2: Look for file with relative path structure (if Condor preserved it)
    elif not foundPath:
        # Remove leading / and try
        relPath = origPath.lstrip('/')
        if os.path.exists(relPath):
            foundPath = os.path.abspath(relPath)

    # Try 3: Search in current directory recursively (in case files are in subdirectories)
    elif not foundPath:
        for root, dirs, files in os.walk(cwd):
            if filename in files:
                foundPath = os.path.abspath(os.path.join(root, filename))
                break

    if foundPath:
        mapping[origPath] = foundPath
        # Also create mapping for directory -> any file in that directory
        # This helps when findDIR is called with a directory path
        origDir = os.path.dirname(origPath)
        if origDir and origDir not in mapping:
            # Store first file found in this directory as a reference
            mapping[origDir] = os.path.dirname(foundPath)

# Write mapping to file
with open('file_path_mapping.txt', 'w') as f:
    for orig, trans in mapping.items():
        f.write(f"{orig}\t{trans}\n")

print(f"Created mapping for {len(mapping)} files")
if len(mapping) < len(originalPaths):
    print(f"Warning: Only mapped {len(mapping)} of {len(originalPaths)} files")
PYEOF
  "${fileListName}"

  if [ -f "file_path_mapping.txt" ]; then
    export CMS_CONNECT_FILE_MAPPING="file_path_mapping.txt"
    echo "File mapping created with $(wc -l < file_path_mapping.txt) entries"
  fi
fi

echo $PWD
echo "Files in current directory:"
ls -lh | head -20
echo "Looking for transferred ROOT files..."
find . -name "*.root" -type f | head -10

# Run the analysis script
# $1 = switchSample/process
# $2 = year
# $3 = whichJob
# $4 = condorJob
# $5 = analysisName
./analysis_runner.sh $1 $2 $3 $4 $5

# Clean up
rm -rf functions* *.pyc $5.tgz \
*Analysis.py analysis_runner.sh functions.h utils*.py \
data weights_mva tmva_helper_xml.* \
mysf.* \
jsns config jsonpog-integration

ls -l
