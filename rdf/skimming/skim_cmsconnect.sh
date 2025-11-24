#!/bin/bash
# CMS Connect compatible skimming script
# Usage: ./skim_cmsconnect.sh <whichSample> <whichJob> <group> <inputSamplesCfg> <inputFilesCfg> [outputDir]

set -e  # Exit on error

# Print environment info
echo "=== CMS Connect Skimming Job ==="
echo "Hostname: $(hostname)"
echo "User: $(whoami)"
echo "Date: $(date)"
echo "Working directory: $PWD"
echo "Arguments: $@"
echo ""

# Parse arguments
if [ $# -lt 5 ]; then
    echo "Usage: $0 <whichSample> <whichJob> <group> <inputSamplesCfg> <inputFilesCfg> [outputDir]"
    echo "  whichSample: Sample index in inputSamplesCfg (0-based)"
    echo "  whichJob: Job index (-1 for all jobs, or specific job number)"
    echo "  group: Number of files per job"
    echo "  inputSamplesCfg: Configuration file with sample names"
    echo "  inputFilesCfg: Configuration file with input file paths"
    echo "  outputDir: (optional) Output directory (default: ./output)"
    exit 1
fi

WHICHSAMPLE=$1
WHICHJOB=$2
GROUP=$3
INPUTSAMPLESCFG=$4
INPUTFILESCFG=$5
OUTPUTDIR=${6:-"./output"}

echo "Configuration:"
echo "  Sample index: $WHICHSAMPLE"
echo "  Job index: $WHICHJOB"
echo "  Files per job: $GROUP"
echo "  Input samples cfg: $INPUTSAMPLESCFG"
echo "  Input files cfg: $INPUTFILESCFG"
echo "  Output directory: $OUTPUTDIR"
echo ""

# Setup CMS environment
echo "=== Setting up CMS environment ==="
if [ -f /cvmfs/cms.cern.ch/cmsset_default.sh ]; then
    source /cvmfs/cms.cern.ch/cmsset_default.sh
    export SCRAM_ARCH=el9_amd64_gcc12
    
    # Check if CMSSW is already set up
    if [ -z "$CMSSW_BASE" ]; then
        echo "Setting up CMSSW_14_1_4..."
        scramv1 project CMSSW CMSSW_14_1_4
        cd CMSSW_14_1_4/src
        eval `scramv1 runtime -sh`
        cd ../..
    else
        echo "CMSSW already set up: $CMSSW_BASE"
        cd $CMSSW_BASE/src
        eval `scramv1 runtime -sh`
        cd -
    fi
else
    echo "Warning: /cvmfs/cms.cern.ch/cmsset_default.sh not found"
    echo "Assuming CMS environment is already set up"
fi

# Check for ROOT
echo "=== Checking ROOT ==="
if command -v root &> /dev/null; then
    ROOT_VERSION=$(root-config --version)
    echo "ROOT version: $ROOT_VERSION"
else
    echo "Error: ROOT not found in PATH"
    exit 1
fi

# Check for Python
echo "=== Checking Python ==="
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "Python version: $PYTHON_VERSION"
else
    echo "Error: python3 not found in PATH"
    exit 1
fi

# Check for required files
echo "=== Checking required files ==="
REQUIRED_FILES=("skim.py" "functions_skim.h" "haddnanoaod.py" "$INPUTSAMPLESCFG" "$INPUTFILESCFG")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "Error: Required file not found: $file"
        exit 1
    else
        echo "  Found: $file"
    fi
done

# Check for config and jsns directories
if [ ! -d "config" ]; then
    echo "Warning: config directory not found"
fi
if [ ! -d "jsns" ]; then
    echo "Warning: jsns directory not found"
fi

# Create output directory
mkdir -p "$OUTPUTDIR"

# Setup proxy if needed (for xrootd access)
echo "=== Checking VOMS proxy ==="
if command -v voms-proxy-info &> /dev/null; then
    if voms-proxy-info -exists -valid 1:00 2>/dev/null; then
        echo "Valid VOMS proxy found"
        voms-proxy-info -all
    else
        echo "Warning: No valid VOMS proxy found"
        echo "You may need to run: voms-proxy-init --voms cms"
    fi
else
    echo "Warning: voms-proxy-info not found"
fi

echo ""
echo "=== Starting skimming ==="
echo ""

# Run the skimming script
python3 skim.py \
    --outputDir="$OUTPUTDIR" \
    --inputSamplesCfg="$INPUTSAMPLESCFG" \
    --inputFilesCfg="$INPUTFILESCFG" \
    --whichSample="$WHICHSAMPLE" \
    --whichJob="$WHICHJOB" \
    --group="$GROUP"

STATUS=$?

echo ""
echo "=== Skimming completed ==="
if [ $STATUS -eq 0 ]; then
    echo "Status: SUCCESS"
    echo "Output files in: $OUTPUTDIR"
    ls -lh "$OUTPUTDIR" || true
else
    echo "Status: FAILURE (exit code: $STATUS)"
fi

exit $STATUS

