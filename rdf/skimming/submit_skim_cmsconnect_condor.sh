#!/bin/bash
# Script to generate and submit condor JDL jobs for CMS Connect
# Usage: ./submit_skim_cmsconnect_condor.sh <year> [outputDir]

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <year> [outputDir]"
    echo "  year: Data year (e.g., 2022a, 2023b, etc.)"
    echo "  outputDir: (optional) Output directory for skimmed files"
    echo ""
    echo "Example:"
    echo "  ./submit_skim_cmsconnect_condor.sh 2022a"
    echo "  ./submit_skim_cmsconnect_condor.sh 2023b ./output"
    exit 1
fi

YEAR=$1
OUTPUTDIR=${2:-"./output"}

echo "=== Preparing CMS Connect Condor JDL Jobs ==="
echo "Year: $YEAR"
echo "Output directory: $OUTPUTDIR"
echo ""

# Check for required files
INPUTSAMPLESCFG="skim_input_samples_${YEAR}_fromDAS.cfg"
INPUTFILESCFG="skim_input_files_fromDAS.cfg"
CONDORJOBS="skim_input_condor_jobs_fromDAS.cfg"
JDL_TEMPLATE="skim_cmsconnect.jdl"

if [ ! -f "$INPUTSAMPLESCFG" ]; then
    echo "Error: Input samples config not found: $INPUTSAMPLESCFG"
    echo "Please run make_skim_input_files_fromDAS.py first"
    exit 1
fi

if [ ! -f "$INPUTFILESCFG" ]; then
    echo "Error: Input files config not found: $INPUTFILESCFG"
    echo "Please run make_skim_input_files_fromDAS.py first"
    exit 1
fi

if [ ! -f "$CONDORJOBS" ]; then
    echo "Error: Condor jobs config not found: $CONDORJOBS"
    echo "Please run make_skim_input_files_fromDAS.py first"
    exit 1
fi

if [ ! -f "$JDL_TEMPLATE" ]; then
    echo "Error: JDL template not found: $JDL_TEMPLATE"
    exit 1
fi

# Create tarball
echo "=== Creating tarball ==="
TARBALL="skim.tgz"

# Remove old tarball if it exists
rm -f "$TARBALL"

echo "Including files in tarball:"
echo "  - skim.py"
echo "  - skim_cmsconnect.sh"
echo "  - functions_skim.h"
echo "  - haddnanoaod.py"
echo "  - $INPUTSAMPLESCFG"
echo "  - $INPUTFILESCFG"
echo "  - skim_*.cfg (all other config files)"
echo "  - jsns/ (JSON files)"
echo "  - config/ (config directory)"

# Create tarball with all necessary files
tar czf "$TARBALL" --exclude='*.csv' \
    skim.py \
    skim_cmsconnect.sh \
    functions_skim.h \
    haddnanoaod.py \
    "$INPUTSAMPLESCFG" \
    "$INPUTFILESCFG" \
    skim_*.cfg \
    config/ \
    jsns/ \
    2>&1 | head -30

if [ ! -f "$TARBALL" ]; then
    echo "Error: Failed to create tarball"
    exit 1
fi

TARBALL_SIZE=$(du -h "$TARBALL" | cut -f1)
echo "Created tarball: $TARBALL ($TARBALL_SIZE)"
echo ""

# Make sure skim_cmsconnect.sh is executable
chmod +x skim_cmsconnect.sh

# Create logs directory
mkdir -p logs

# Generate job list file for queue statement
echo "=== Generating job list ==="
JOBLIST="job_list_${YEAR}.txt"
> "$JOBLIST"  # Clear/create file

JOB_COUNT=0
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    
    set -- $line
    WHICHSAMPLE=$1
    WHICHJOB=$2
    GROUP=$3
    SAMPLENAME=$4
    
    # Write job parameters to job list
    echo "$WHICHSAMPLE $WHICHJOB $GROUP $INPUTSAMPLESCFG $INPUTFILESCFG $OUTPUTDIR" >> "$JOBLIST"
    JOB_COUNT=$((JOB_COUNT + 1))
done < "$CONDORJOBS"

echo "Generated job list: $JOBLIST with $JOB_COUNT jobs"
echo ""

# Generate individual JDL files (optional - for debugging)
echo "=== Generating individual JDL files (optional) ==="
mkdir -p jdl_files
JDL_COUNT=0

while IFS= read -r line || [ -n "$line" ]; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    
    set -- $line
    WHICHSAMPLE=$1
    WHICHJOB=$2
    GROUP=$3
    
    JDL_FILE="jdl_files/skim_${WHICHSAMPLE}_${WHICHJOB}.jdl"
    
    # Create JDL file from template with substituted values
    sed -e "s|\$(whichSample)|$WHICHSAMPLE|g" \
        -e "s|\$(whichJob)|$WHICHJOB|g" \
        -e "s|\$(group)|$GROUP|g" \
        -e "s|\$(inputSamplesCfg)|$INPUTSAMPLESCFG|g" \
        -e "s|\$(inputFilesCfg)|$INPUTFILESCFG|g" \
        -e "s|\$(outputDir)|$OUTPUTDIR|g" \
        -e "s|\$(uid)|$(id -u)|g" \
        -e "s|\$(user)|$(whoami)|g" \
        "$JDL_TEMPLATE" > "$JDL_FILE"
    
    # Remove the Queue line comment and add actual queue
    echo "Queue" >> "$JDL_FILE"
    
    JDL_COUNT=$((JDL_COUNT + 1))
done < "$CONDORJOBS"

echo "Generated $JDL_COUNT individual JDL files in jdl_files/"
echo ""

# Generate master JDL file with queue from job list
echo "=== Generating master JDL file ==="
MASTER_JDL="skim_cmsconnect_${YEAR}.jdl"

# Create master JDL with queue statement
sed -e "s|\$(uid)|$(id -u)|g" \
    -e "s|\$(user)|$(whoami)|g" \
    "$JDL_TEMPLATE" > "$MASTER_JDL"

# Add queue statement with job list
echo "" >> "$MASTER_JDL"
echo "# Queue jobs from job list" >> "$MASTER_JDL"
echo "Queue whichSample whichJob group inputSamplesCfg inputFilesCfg outputDir from $JOBLIST" >> "$MASTER_JDL"

echo "Generated master JDL: $MASTER_JDL"
echo ""

# Check if condor_submit is available
if ! command -v condor_submit &> /dev/null; then
    echo "Warning: condor_submit not found in PATH"
    echo "You may need to set up HTCondor environment"
    echo ""
    echo "To submit jobs later, run:"
    echo "  condor_submit $MASTER_JDL"
    echo ""
    echo "Or submit individual jobs:"
    echo "  for jdl in jdl_files/*.jdl; do condor_submit \$jdl; done"
else
    echo "=== Submitting jobs to condor ==="
    echo "Submitting master JDL: $MASTER_JDL"
    
    # Ask for confirmation
    read -p "Submit $JOB_COUNT jobs to condor? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        condor_submit "$MASTER_JDL"
        SUBMIT_STATUS=$?
        
        if [ $SUBMIT_STATUS -eq 0 ]; then
            echo ""
            echo "Jobs submitted successfully!"
            echo "Check status with: condor_q"
        else
            echo "Warning: Job submission may have failed (exit code: $SUBMIT_STATUS)"
        fi
    else
        echo "Submission cancelled. You can submit later with:"
        echo "  condor_submit $MASTER_JDL"
    fi
fi

echo ""
echo "=== Summary ==="
echo "Tarball: $TARBALL"
echo "Master JDL: $MASTER_JDL"
echo "Job list: $JOBLIST"
echo "Individual JDL files: jdl_files/ (${JDL_COUNT} files)"
echo "Total jobs: $JOB_COUNT"
echo ""
echo "Files ready for CMS Connect:"
echo "1. $TARBALL - Job input files"
echo "2. $MASTER_JDL - Master condor JDL file"
echo "3. $JOBLIST - Job parameter list"
echo "4. skim_cmsconnect.sh - Executable script"
echo ""
echo "To submit on CMS Connect:"
echo "  condor_submit $MASTER_JDL"

