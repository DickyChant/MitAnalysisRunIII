#!/bin/bash

# Script to check if skim output from skim_condor_wz_guillermo.sh is complete
# Usage: ./check_wz_guillermo_skim_complete.sh <year> [--skims-dir <path>] [--work-dir <path>]

YEAR=""
SKIMS_DIR=""
WORK_DIR="/home/scratch/stqian/wz_guillermo"
CONDORJOBS=""

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
        --condor-jobs-cfg|-c)
            CONDORJOBS="$2"
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
            echo "  --condor-jobs-cfg, -c FILE  Condor jobs config file"
            echo "                        (default: skim_input_condor_jobs_fromDAS.cfg)"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 2022a"
            echo "  $0 2022a --skims-dir /path/to/skims"
            echo "  $0 2022a --skims-dir /path/to/skims --work-dir /path/to/work"
            echo "  $0 2022a --condor-jobs-cfg custom_jobs.cfg"
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

# Set default condor jobs config file if not provided
CONDORJOBS=${CONDORJOBS:-"skim_input_condor_jobs_fromDAS.cfg"}

# Check for condor jobs config file
if [ ! -f "$CONDORJOBS" ]; then
    echo "Error: Condor jobs config not found: $CONDORJOBS"
    echo "Please specify with --condor-jobs-cfg if using a custom file"
    exit 1
fi

# Skim types to check
SKIM_TYPES=("1l" "2l" "3l" "met" "pho")

# Counters
TOTAL_JOBS=0
COMPLETE_JOBS=0
MISSING_JOBS=0
MISSING_FILES=0

# Arrays to track missing files and detailed file information
declare -a MISSING_JOB_LIST=()
declare -a MISSING_FILE_LIST=()
declare -a DETAILED_FILE_INFO=()
declare -A INSPECTED_DIRS  # Associative array to track unique inspected directories

# Generate report filename
REPORT_FILE="${WORK_DIR}/skim_completeness_report_${YEAR}_$(date +%Y%m%d_%H%M%S).md"

# Initialize report file
{
    echo "# Skim Output Completeness Report"
    echo ""
    echo "**Generated:** $(date)"
    echo "**Year:** $YEAR"
    echo "**Work Directory:** $WORK_DIR"
    if [ -n "$SKIMS_DIR" ]; then
        echo "**Skims Directory:** $SKIMS_DIR"
    else
        echo "**Skims Directory:** (default locations)"
    fi
    echo ""
    echo "---"
    echo ""
    echo "## Missing Files Details"
    echo ""
    echo "| Sample | Job | Sample Name | Skim Type | Filename | Status | Expected Location |"
    echo "|--------|-----|-------------|-----------|----------|--------|-------------------|"
} > "$REPORT_FILE"

# Check each job
echo "Checking jobs from $CONDORJOBS..."
echo "Generating detailed report: $REPORT_FILE"
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
        file_size=0
        status="MISSING"
        
        # Build list of possible file paths to check
        declare -a check_paths=()
        declare -a checked_dirs=()
        
        if [ -n "$SKIMS_DIR" ]; then
            # If skims-dir is specified, use it directly (no YEAR subdirectory)
            check_paths+=("${SKIMS_DIR}/${skimtype}/${sampleName}/${filename}")
            checked_dirs+=("${SKIMS_DIR}/${skimtype}/${sampleName}")
        else
            # Default locations: work directory with YEAR, or work_dir/skims
            check_paths+=("${WORK_DIR}/${YEAR}/${skimtype}/${sampleName}/${filename}")
            check_paths+=("${WORK_DIR}/skims/${skimtype}/${sampleName}/${filename}")
            checked_dirs+=("${WORK_DIR}/${YEAR}/${skimtype}/${sampleName}")
            checked_dirs+=("${WORK_DIR}/skims/${skimtype}/${sampleName}")
        fi
        
        # Track directories we're checking (all of them, whether they exist or not)
        for dir_path in "${checked_dirs[@]}"; do
            INSPECTED_DIRS["$dir_path"]=1
        done
        
        # Check each possible path
        for filepath in "${check_paths[@]}"; do
            if [ -f "$filepath" ]; then
                # Check file size (should be > 1000 bytes to avoid empty/corrupted files)
                file_size=$(stat -f%z "$filepath" 2>/dev/null || stat -c%s "$filepath" 2>/dev/null || echo "0")
                if [ "$file_size" -gt 1000 ]; then
                    file_exists=true
                    file_path="$filepath"
                    status="FOUND"
                    break
                else
                    # File exists but too small (possibly corrupted)
                    file_path="$filepath"
                    status="TOO_SMALL"
                    file_size=$(stat -f%z "$filepath" 2>/dev/null || stat -c%s "$filepath" 2>/dev/null || echo "0")
                fi
            fi
        done
        
        # Add to detailed file info for report (only missing or problematic files)
        if [ "$status" = "TOO_SMALL" ]; then
            # Include files that exist but are too small (possibly corrupted)
            echo "| ${whichSample} | ${whichJob} | ${sampleName} | ${skimtype} | ${filename} | ${status} | ${file_path} (size: ${file_size} bytes) |" >> "$REPORT_FILE"
        elif [ "$file_exists" = false ]; then
            # Missing files - determine which directory was checked
            checked_dir=""
            if [ -n "$SKIMS_DIR" ]; then
                checked_dir="${SKIMS_DIR}/${skimtype}/${sampleName}/"
            else
                checked_dir="${WORK_DIR}/skims/${skimtype}/${sampleName}/ (or ${WORK_DIR}/${YEAR}/${skimtype}/${sampleName}/)"
            fi
            echo "| ${whichSample} | ${whichJob} | ${sampleName} | ${skimtype} | ${filename} | ${status} | ${checked_dir} |" >> "$REPORT_FILE"
        fi
        
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

# Calculate completion rate
if [ $TOTAL_JOBS -gt 0 ]; then
    COMPLETION_RATE=$(awk "BEGIN {printf \"%.2f\", ($COMPLETE_JOBS / $TOTAL_JOBS) * 100}")
else
    COMPLETION_RATE="0.00"
fi

# Add summary section to report
{
    echo ""
    echo "---"
    echo ""
    echo "## Summary"
    echo ""
    echo "| Metric | Count |"
    echo "|--------|-------|"
    echo "| Total jobs checked | $TOTAL_JOBS |"
    echo "| Complete jobs | $COMPLETE_JOBS |"
    echo "| Jobs with missing files | $MISSING_JOBS |"
    echo "| Total missing files | $MISSING_FILES |"
    echo "| **Completion rate** | **${COMPLETION_RATE}%** |"
    echo ""
} >> "$REPORT_FILE"

# Print summary
echo "=========================================="
echo "=== Summary ==="
echo "=========================================="
echo "Total jobs checked: $TOTAL_JOBS"
echo "Completion rate: ${COMPLETION_RATE}%"
echo ""
echo "Jobs with missing files: $MISSING_JOBS"
echo "Total missing files: $MISSING_FILES"
echo ""

if [ $MISSING_JOBS -eq 0 ]; then
    {
        echo "## Status"
        echo ""
        echo "✓ **All skim output files are complete!**"
        echo ""
        echo "All $COMPLETE_JOBS jobs have all required output files."
        echo "Completion rate: ${COMPLETION_RATE}%"
        echo ""
    } >> "$REPORT_FILE"
    
    echo "✓ All skim output files are complete! (${COMPLETION_RATE}%)"
    echo ""
else
    {
        echo "## Status"
        echo ""
        echo "✗ **Some skim output files are missing**"
        echo ""
        echo "### Jobs with Missing Files"
        echo ""
        for job_info in "${MISSING_JOB_LIST[@]}"; do
            echo "- ${job_info}"
        done
        echo ""
        echo "### Missing Files Details"
        echo ""
        for file_info in "${MISSING_FILE_LIST[@]}"; do
            echo "${file_info}"
        done
        echo ""
        echo "### Next Steps"
        echo ""
        echo "1. Check condor job logs: \`$WORK_DIR/logs/\`"
        echo "2. Check for failed jobs: \`condor_q | grep FAILED\`"
        echo "3. Check job status: \`condor_q\`"
        echo "4. Resubmit failed jobs if needed"
        echo ""
    } >> "$REPORT_FILE"
    
    echo "✗ Some skim output files are missing (${COMPLETION_RATE}% complete)"
    echo ""
    echo "Missing: $MISSING_JOBS jobs, $MISSING_FILES files"
    echo ""
    echo "See detailed report for complete missing file information: $REPORT_FILE"
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
    
    {
        echo "### Missing Jobs Config File"
        echo ""
        echo "Missing jobs saved to: \`$MISSING_JOBS_FILE\`"
        echo ""
        echo "You can use this file to resubmit only the missing jobs."
        echo ""
    } >> "$REPORT_FILE"
    
    echo "Missing jobs saved to: $MISSING_JOBS_FILE"
    echo "You can use this file to resubmit only the missing jobs."
    echo ""
fi

# Add inspected directories section to report
{
    echo "---"
    echo ""
    echo "## Inspected Directories"
    echo ""
    echo "The following directories were inspected for root files:"
    echo ""
} >> "$REPORT_FILE"

# Collect and sort inspected directories
INSPECTED_DIRS_SORTED=()
for dir in "${!INSPECTED_DIRS[@]}"; do
    INSPECTED_DIRS_SORTED+=("$dir")
done

# Sort directories
IFS=$'\n' INSPECTED_DIRS_SORTED=($(sort <<<"${INSPECTED_DIRS_SORTED[*]}"))
unset IFS

# Add directories to report and print them
if [ ${#INSPECTED_DIRS_SORTED[@]} -gt 0 ]; then
    for dir in "${INSPECTED_DIRS_SORTED[@]}"; do
        if [ -d "$dir" ]; then
            echo "- \`$dir\` ✓ (exists)" >> "$REPORT_FILE"
        else
            echo "- \`$dir\` ✗ (does not exist)" >> "$REPORT_FILE"
        fi
    done
else
    echo "- *No directories were inspected (no matching directory structure found)*" >> "$REPORT_FILE"
fi

{
    echo ""
    echo "---"
    echo ""
    echo "*Report generated by: check_wz_guillermo_skim_complete.sh*"
} >> "$REPORT_FILE"

# Print inspected directories to console with diagnostic info
echo "=========================================="
echo "=== Inspected Directories ==="
echo "=========================================="
if [ ${#INSPECTED_DIRS_SORTED[@]} -gt 0 ]; then
    # Show first few directories with file counts
    SHOWN=0
    MAX_SHOW=10
    for dir in "${INSPECTED_DIRS_SORTED[@]}"; do
        if [ -d "$dir" ]; then
            root_count=$(find "$dir" -maxdepth 1 -name "*.root" -type f 2>/dev/null | wc -l)
            if [ $SHOWN -lt $MAX_SHOW ]; then
                echo "✓ $dir (exists, $root_count .root files)"
                # Show example files if any exist
                if [ "$root_count" -gt 0 ] && [ $SHOWN -eq 0 ]; then
                    echo "  Example files found:"
                    find "$dir" -maxdepth 1 -name "*.root" -type f 2>/dev/null | head -3 | sed 's/^/    - /'
                fi
                SHOWN=$((SHOWN + 1))
            fi
        else
            if [ $SHOWN -lt $MAX_SHOW ]; then
                echo "✗ $dir (does not exist)"
                SHOWN=$((SHOWN + 1))
            fi
        fi
    done
    
    # Show summary
    total_dirs=${#INSPECTED_DIRS_SORTED[@]}
    if [ $total_dirs -gt $MAX_SHOW ]; then
        echo "... ($((total_dirs - MAX_SHOW)) more directories, showing first $MAX_SHOW)"
    fi
    
    # Check a sample directory to show what we're looking for
    if [ ${#INSPECTED_DIRS_SORTED[@]} -gt 0 ]; then
        sample_dir="${INSPECTED_DIRS_SORTED[0]}"
        if [ -d "$sample_dir" ]; then
            echo ""
            echo "=== Diagnostic: Expected vs Actual Files ==="
            echo "Sample directory: $sample_dir"
            echo ""
            echo "Expected file pattern: output_<skimtype>_<sample>_<job>.root"
            echo ""
            echo "Actual .root files in this directory:"
            find "$sample_dir" -maxdepth 1 -name "*.root" -type f 2>/dev/null | head -5 | sed 's/^/  /'
            if [ $(find "$sample_dir" -maxdepth 1 -name "*.root" -type f 2>/dev/null | wc -l) -eq 0 ]; then
                echo "  (none found)"
            fi
            echo ""
        fi
    fi
else
    echo "No directories were inspected (no matching directory structure found)"
fi
echo ""
echo "=========================================="
echo "Detailed report saved to: $REPORT_FILE"
echo "=========================================="

if [ $MISSING_JOBS -eq 0 ]; then
    exit 0
else
    exit 1
fi

