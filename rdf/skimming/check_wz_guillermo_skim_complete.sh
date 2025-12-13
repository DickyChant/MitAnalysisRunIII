#!/bin/bash

# Script to check if skim output from skim_condor_wz_guillermo.sh is complete
# Usage: ./check_wz_guillermo_skim_complete.sh <year> [--skims-dir <path>] [--work-dir <path>]

YEAR=""
SKIMS_DIR=""
WORK_DIR="/home/scratch/stqian/wz_guillermo"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skims-dir|-s)
            SKIMS_DIR="$2"
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
            echo "  --skims-dir, -s PATH  Directory containing skim output files"
            echo "                        If not specified, checks WORK_DIR/YEAR/ and WORK_DIR/skims/"
            echo "  --work-dir, -w PATH   Work directory containing config files (default: /home/scratch/stqian/wz_guillermo)"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 2022a"
            echo "  $0 2022a --skims-dir /path/to/skims"
            echo "  $0 2022a --skims-dir /path/to/skims --work-dir /path/to/work"
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
    echo "Usage: $0 <year> [--skims-dir <path>] [--work-dir <path>]"
    echo "Use --help for more information"
    exit 1
fi

echo "=== Checking Skim Output Completeness ==="
echo "Year: $YEAR"
echo "Work directory: $WORK_DIR"
if [ -n "$SKIMS_DIR" ]; then
    echo "Skims directory: $SKIMS_DIR"
else
    echo "Skims directory: (checking default locations)"
fi
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

# Check for condor jobs config file
CONDORJOBS="skim_input_condor_jobs_fromDAS.cfg"
if [ ! -f "$CONDORJOBS" ]; then
    echo "Error: Condor jobs config not found: $CONDORJOBS"
    echo "This file should exist in the work directory"
    exit 1
fi

# Skim types to check
SKIM_TYPES=("1l" "2l" "3l" "met" "pho")

# Counters
TOTAL_JOBS=0
COMPLETE_JOBS=0
MISSING_JOBS=0
MISSING_FILES=0

# Arrays to track missing files
declare -a MISSING_JOB_LIST=()
declare -a MISSING_FILE_LIST=()

# Check each job
echo "Checking jobs from $CONDORJOBS..."
echo ""

while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    
    set -- $line
    whichSample=$1
    whichJob=$2
    group=$3
    sampleName=$4
    
    TOTAL_JOBS=$((TOTAL_JOBS + 1))
    
    # Check if all output files exist for this job
    job_complete=true
    job_missing_files=()
    
    for skimtype in "${SKIM_TYPES[@]}"; do
        # Expected filename: output_<skimtype>_<whichSample>_<whichJob>.root
        filename="output_${skimtype}_${whichSample}_${whichJob}.root"
        
        file_exists=false
        file_path=""
        
        # Build list of possible file paths to check
        declare -a check_paths=()
        
        if [ -n "$SKIMS_DIR" ]; then
            # If skims-dir is specified, check there first
            # Try both with and without YEAR subdirectory
            check_paths+=("${SKIMS_DIR}/${skimtype}/${sampleName}/${filename}")
            check_paths+=("${SKIMS_DIR}/${YEAR}/${skimtype}/${sampleName}/${filename}")
        else
            # Default locations: work directory with YEAR, or work_dir/skims
            check_paths+=("${WORK_DIR}/${YEAR}/${skimtype}/${sampleName}/${filename}")
            check_paths+=("${WORK_DIR}/skims/${skimtype}/${sampleName}/${filename}")
        fi
        
        # Check each possible path
        for filepath in "${check_paths[@]}"; do
            if [ -f "$filepath" ]; then
                # Check file size (should be > 1000 bytes to avoid empty/corrupted files)
                file_size=$(stat -f%z "$filepath" 2>/dev/null || stat -c%s "$filepath" 2>/dev/null || echo "0")
                if [ "$file_size" -gt 1000 ]; then
                    file_exists=true
                    file_path="$filepath"
                    break
                fi
            fi
        done
        
        if [ "$file_exists" = false ]; then
            job_complete=false
            job_missing_files+=("${skimtype}:${filename}")
            MISSING_FILES=$((MISSING_FILES + 1))
        fi
    done
    
    # Update counters
    if [ "$job_complete" = true ]; then
        COMPLETE_JOBS=$((COMPLETE_JOBS + 1))
    else
        MISSING_JOBS=$((MISSING_JOBS + 1))
        MISSING_JOB_LIST+=("Sample ${whichSample}, Job ${whichJob} (${sampleName})")
        for missing in "${job_missing_files[@]}"; do
            MISSING_FILE_LIST+=("  - ${missing}")
        done
    fi
    
done < "$CONDORJOBS"

# Print summary
echo "=========================================="
echo "=== Summary ==="
echo "=========================================="
echo "Total jobs checked: $TOTAL_JOBS"
echo "Complete jobs: $COMPLETE_JOBS"
echo "Jobs with missing files: $MISSING_JOBS"
echo "Total missing files: $MISSING_FILES"
echo ""

if [ $MISSING_JOBS -eq 0 ]; then
    echo "✓ All skim output files are complete!"
    echo ""
    echo "All $COMPLETE_JOBS jobs have all required output files."
    exit 0
else
    echo "✗ Some skim output files are missing"
    echo ""
    echo "=== Jobs with Missing Files ==="
    for job_info in "${MISSING_JOB_LIST[@]}"; do
        echo "$job_info"
    done
    echo ""
    echo "=== Missing Files Details ==="
    for file_info in "${MISSING_FILE_LIST[@]}"; do
        echo "$file_info"
    done
    echo ""
    echo "=== Next Steps ==="
    echo "1. Check condor job logs: $WORK_DIR/logs/"
    echo "2. Check for failed jobs: condor_q | grep FAILED"
    echo "3. Check job status: condor_q"
    echo "4. Resubmit failed jobs if needed"
    echo ""
    
    # Generate a list of missing jobs for resubmission
    MISSING_JOBS_FILE="${WORK_DIR}/skim_input_condor_missing_jobs_${YEAR}.cfg"
    echo "Generating missing jobs file: $MISSING_JOBS_FILE"
    > "$MISSING_JOBS_FILE"
    
    while IFS= read -r line || [ -n "$line" ]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        set -- $line
        whichSample=$1
        whichJob=$2
        group=$3
        sampleName=$4
        
        # Check if this job is missing files (using same logic as above)
        job_missing=false
        for skimtype in "${SKIM_TYPES[@]}"; do
            filename="output_${skimtype}_${whichSample}_${whichJob}.root"
            
            # Build list of possible file paths to check
            declare -a check_paths=()
            
            if [ -n "$SKIMS_DIR" ]; then
                check_paths+=("${SKIMS_DIR}/${skimtype}/${sampleName}/${filename}")
                check_paths+=("${SKIMS_DIR}/${YEAR}/${skimtype}/${sampleName}/${filename}")
            else
                check_paths+=("${WORK_DIR}/${YEAR}/${skimtype}/${sampleName}/${filename}")
                check_paths+=("${WORK_DIR}/skims/${skimtype}/${sampleName}/${filename}")
            fi
            
            file_found=false
            for filepath in "${check_paths[@]}"; do
                if [ -f "$filepath" ]; then
                    file_size=$(stat -f%z "$filepath" 2>/dev/null || stat -c%s "$filepath" 2>/dev/null || echo "0")
                    if [ "$file_size" -gt 1000 ]; then
                        file_found=true
                        break
                    fi
                fi
            done
            
            if [ "$file_found" = false ]; then
                job_missing=true
                break
            fi
        done
        
        if [ "$job_missing" = true ]; then
            echo "$line" >> "$MISSING_JOBS_FILE"
        fi
    done < "$CONDORJOBS"
    
    echo "Missing jobs saved to: $MISSING_JOBS_FILE"
    echo "You can use this file to resubmit only the missing jobs."
    echo ""
    
    exit 1
fi

