#!/bin/bash

# Script to resubmit missing skim jobs for wz_guillermo
# Usage: ./resubmit_missing_wz_guillermo.sh <year> [--missing-jobs-file <path>] [--output-base-dir <path>]

YEAR=""
MISSING_JOBS_FILE=""
OUTPUT_BASE_DIR=""
WORK_DIR="/home/scratch/stqian/wz_guillermo"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --missing-jobs-file|-m)
            MISSING_JOBS_FILE="$2"
            shift 2
            ;;
        --output-base-dir|-o)
            OUTPUT_BASE_DIR="$2"
            shift 2
            ;;
        --work-dir|-w)
            WORK_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 <year> [OPTIONS]"
            echo ""
            echo "Required:"
            echo "  year                  Data year (e.g., 2022a, 2023b, etc.)"
            echo ""
            echo "Options:"
            echo "  --missing-jobs-file, -m PATH  Path to missing jobs config file"
            echo "                                 (default: WORK_DIR/skim_input_condor_missing_jobs_<year>.cfg)"
            echo "  --output-base-dir, -o PATH    Base directory for output (default: /home/scratch/stqian/wz_guillermo/skims)"
            echo "  --work-dir, -w PATH           Work directory (default: /home/scratch/stqian/wz_guillermo)"
            echo "  --help, -h                    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 2022a"
            echo "  $0 2022a --missing-jobs-file /path/to/missing_jobs.cfg"
            echo "  $0 2022a --output-base-dir /path/to/skims"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            if [ -z "$YEAR" ]; then
                YEAR="$1"
            else
                echo "Error: Multiple year arguments specified"
                echo "Use --help for usage information"
                exit 1
            fi
            shift
            ;;
    esac
done

# Check if year is provided
if [ -z "$YEAR" ]; then
    echo "Error: Year is required"
    echo "Usage: $0 <year> [--missing-jobs-file <path>] [--output-base-dir <path>]"
    echo "Use --help for more information"
    exit 1
fi

# Set default missing jobs file if not provided
if [ -z "$MISSING_JOBS_FILE" ]; then
    MISSING_JOBS_FILE="${WORK_DIR}/skim_input_condor_missing_jobs_${YEAR}.cfg"
fi

# Set default output base directory
if [ -z "$OUTPUT_BASE_DIR" ]; then
    OUTPUT_BASE_DIR="/home/scratch/stqian/wz_guillermo/skims"
fi

echo "=== Resubmitting Missing Skim Jobs ==="
echo "Year: $YEAR"
echo "Work directory: $WORK_DIR"
echo "Output base directory: $OUTPUT_BASE_DIR"
echo "Missing jobs file: $MISSING_JOBS_FILE"
echo ""

# Check if work directory exists
if [ ! -d "$WORK_DIR" ]; then
    echo "Error: Work directory does not exist: $WORK_DIR"
    exit 1
fi

# Change to work directory
cd "$WORK_DIR" || {
    echo "Error: Cannot change to work directory: $WORK_DIR"
    exit 1
}

# Check if missing jobs file exists
if [ ! -f "$MISSING_JOBS_FILE" ]; then
    echo "Error: Missing jobs file not found: $MISSING_JOBS_FILE"
    echo "Please run check_wz_guillermo_skim_complete.sh first to generate this file"
    exit 1
fi

# Check that missing jobs file is not empty
if [ ! -s "$MISSING_JOBS_FILE" ]; then
    echo "Error: Missing jobs file is empty: $MISSING_JOBS_FILE"
    echo "No jobs to resubmit"
    exit 1
fi

# Check for required files
INPUTSAMPLESCFG="skim_input_samples_${YEAR}_fromDAS.cfg"
INPUTFILESCFG="skim_input_files_fromDAS.cfg"

if [ ! -f "$INPUTSAMPLESCFG" ]; then
    echo "Error: Input samples config not found: $INPUTSAMPLESCFG"
    exit 1
fi

if [ ! -f "$INPUTFILESCFG" ]; then
    echo "Error: Input files config not found: $INPUTFILESCFG"
    exit 1
fi

# Setup VOMS proxy
USERPROXY=`id -u`
echo "User proxy ID: ${USERPROXY}"

if [ -f "$HOME/.grid-cert-passphrase" ]; then
    voms-proxy-init --voms cms --valid 168:00 -pwstdin < $HOME/.grid-cert-passphrase
else
    echo "Warning: $HOME/.grid-cert-passphrase not found"
    echo "Attempting voms-proxy-init without password file..."
    voms-proxy-init --voms cms --valid 168:00 || {
        echo "Error: Failed to initialize VOMS proxy"
        exit 1
    }
fi

# Copy proxy to a location accessible by condor
PROXY_LOCATION="/tmp/x509up_u${USERPROXY}"
if [ -f "$PROXY_LOCATION" ]; then
    echo "VOMS proxy found at: $PROXY_LOCATION"
else
    echo "Warning: VOMS proxy not found at expected location"
fi

# Check if tarball exists and is recent (less than 7 days old)
NEED_TARBALL=true
if [ -f "skim.tgz" ]; then
    # Check if tarball is less than 7 days old
    if [ $(find skim.tgz -mtime -7 | wc -l) -gt 0 ]; then
        echo "Using existing tarball: skim.tgz"
        NEED_TARBALL=false
    else
        echo "Tarball exists but is older than 7 days, recreating..."
    fi
fi

# Create tarball if needed
if [ "$NEED_TARBALL" = true ]; then
    echo "Creating tarball..."
    echo "Including files in tarball:"
    echo "  - skim.py"
    echo "  - skim_*.cfg (all config files)"
    echo "  - functions_skim.h"
    echo "  - haddnanoaod.py"
    echo "  - jsns/* (JSON files)"
    echo "  - config/* (config directory)"
    
    # Remove old tarball if it exists
    rm -f skim.tgz
    
    # Create tarball with all necessary files
    tar cvzf skim.tgz --exclude='*.csv' \
        skim.py \
        skim_*.cfg \
        functions_skim.h \
        haddnanoaod.py \
        jsns/ \
        config/ 2>&1 | head -20
    
    if [ ! -f "skim.tgz" ]; then
        echo "Error: Failed to create tarball"
        exit 1
    fi
    
    TARBALL_SIZE=$(du -h skim.tgz | cut -f1)
    echo "Tarball created successfully: skim.tgz ($TARBALL_SIZE)"
fi
echo ""

# Create logs directory
mkdir -p logs

# Create YEAR directory if it doesn't exist
mkdir -p ${YEAR}

# Count jobs to resubmit
JOB_COUNT_IN_FILE=$(grep -v '^[[:space:]]*#' "$MISSING_JOBS_FILE" | grep -v '^[[:space:]]*$' | wc -l)
echo "Number of jobs to resubmit: $JOB_COUNT_IN_FILE"
echo ""

# Create output directories structure
echo "Creating output directory structure..."

# Submit condor jobs
echo "Resubmitting condor jobs..."
JOB_COUNT=0

while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    
    set -- $line
    whichSample=$1
    whichJob=$2
    group=$3
    sampleName=$4
    
    # Create output directories for this sample
    for skimtype in 1l 2l 3l met pho; do
        SAMPLE_OUTPUT_DIR="${OUTPUT_BASE_DIR}/${skimtype}/${sampleName}"
        if [ ! -d "$SAMPLE_OUTPUT_DIR" ]; then
            mkdir -p "$SAMPLE_OUTPUT_DIR"
        fi
    done

    echo "Resubmitting sample $whichSample, job $whichJob, group $group, sampleName $sampleName"
    
    # Create condor submit file
    cat << EOF > submit_${whichSample}_${whichJob}
Universe   = vanilla
Executable = skim_within_singularity.sh
Arguments  = ${whichSample} ${whichJob} ${group} ${INPUTSAMPLESCFG} ${INPUTFILESCFG}
RequestMemory = 6000
RequestCpus = 1
RequestDisk = DiskUsage
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_output_files = 1l, 2l, 3l, met, pho
transfer_output_remaps = 1l=${YEAR}/1l; 2l=${YEAR}/2l; 3l=${YEAR}/3l; met=${YEAR}/met; pho=${YEAR}/pho
Log    = logs/simple_skim_${whichSample}_${whichJob}.log
Output = logs/simple_skim_${whichSample}_${whichJob}.out
Error  = logs/simple_skim_${whichSample}_${whichJob}.error
transfer_input_files = skim.tgz, skim_within_singularity.sh
Requirements = HAS_SINGULARITY == True
+SingularityImage = "/cvmfs/singularity.opensciencegrid.org/cmssw/cms:rhel9"
Queue
EOF
    
    # Submit the job
    condor_submit submit_${whichSample}_${whichJob}
    SUBMIT_STATUS=$?
    
    if [ $SUBMIT_STATUS -eq 0 ]; then
        JOB_COUNT=$((JOB_COUNT + 1))
        echo "  ✓ Submitted job for sample $whichSample, job $whichJob (sample: $sampleName)"
    else
        echo "  ✗ Warning: Failed to submit job for sample $whichSample, job $whichJob"
    fi
    
    # Clean up submit file
    rm -f submit_${whichSample}_${whichJob}
    
done < "$MISSING_JOBS_FILE"

echo ""
echo "=== Resubmission Complete ==="
echo "Total jobs resubmitted: $JOB_COUNT"
echo "Output directory: $OUTPUT_BASE_DIR"
echo "Logs directory: $WORK_DIR/logs"
echo ""
echo "To check job status:"
echo "  condor_q"
echo ""
echo "To check specific job logs:"
echo "  tail -f $WORK_DIR/logs/simple_skim_<sample>_<job>.log"
echo ""
echo "After jobs complete, run check_wz_guillermo_skim_complete.sh again to verify completion."

