#!/bin/sh

# Condor submission script for wz_guillermo skimming
# Usage: ./skim_condor_wz_guillermo.sh <year> [outputBaseDir]

if [ $# -lt 1 ]; then
    echo "TOO FEW PARAMETERS"
    echo "Usage: $0 <year> [outputBaseDir]"
    echo "  year: Data year (e.g., 2022a, 2023b, etc.)"
    echo "  outputBaseDir: (optional) Base directory for output (default: /home/scratch/stqian/wz_guillermo/skims)"
    exit 1
fi

YEAR=$1
OUTPUT_BASE_DIR=${2:-"/home/scratch/stqian/wz_guillermo/skims"}
WORK_DIR="/home/scratch/stqian/wz_guillermo"

echo "=== Condor Submission for wz_guillermo Skimming ==="
echo "Year: $YEAR"
echo "Work directory: $WORK_DIR"
echo "Output base directory: $OUTPUT_BASE_DIR"
echo ""

# Check if work directory exists
if [ ! -d "$WORK_DIR" ]; then
    echo "Error: Work directory does not exist: $WORK_DIR"
    echo "Please run make_wz_guillermo_folder.sh first"
    exit 1
fi

# Change to work directory
cd "$WORK_DIR" || {
    echo "Error: Cannot change to work directory: $WORK_DIR"
    exit 1
}

# Check for required files
INPUTSAMPLESCFG="skim_input_samples_${YEAR}_fromDAS.cfg"
INPUTFILESCFG="skim_input_files_fromDAS.cfg"
CONDORJOBS="skim_input_condor_jobs_fromDAS.cfg"

if [ ! -f "$INPUTSAMPLESCFG" ]; then
    echo "Error: Input samples config not found: $INPUTSAMPLESCFG"
    echo "Please run make_skim_input_files_fromDAS.py first"
    exit 1
fi

if [ ! -f "$INPUTFILESCFG" ]; then
    echo "Error: Input files config not found: $INPUTFILESCFG"
    echo "Please run make_skim_input_files_fromDAS.cfg first"
    exit 1
fi

if [ ! -f "$CONDORJOBS" ]; then
    echo "Error: Condor jobs config not found: $CONDORJOBS"
    echo "Please run make_skim_input_files_fromDAS.py first"
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

# Create tarball with necessary files
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
echo ""

# Create logs directory
mkdir -p logs

# Create output directories structure
echo "Creating output directory structure..."
mkdir -p "${OUTPUT_BASE_DIR}"

# Submit condor jobs
echo "Submitting condor jobs..."
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

    echo "Working on sample $whichSample, job $whichJob, group $group, sampleName $sampleName"
    
    # Create condor submit file
    # Output files: skim.py writes to current dir, then copies to ./1l/<sample>/ etc., then removes originals
    # So files end up in subdirectories. We'll use transfer_output_remaps to move them to final location
    cat << EOF > submit_${whichSample}_${whichJob}
Universe   = vanilla
Executable = skim_within_singularity.sh
Arguments  = ${whichSample} ${whichJob} ${group} ${INPUTSAMPLESCFG} ${INPUTFILESCFG}
RequestMemory = 6000
RequestCpus = 1
RequestDisk = DiskUsage
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
# transfer_output_files = 1l/${sampleName}/output_1l_${whichSample}_${whichJob}.root, 2l/${sampleName}/output_2l_${whichSample}_${whichJob}.root, 3l/${sampleName}/output_3l_${whichSample}_${whichJob}.root, met/${sampleName}/output_met_${whichSample}_${whichJob}.root
transfer_output_files = 1l, 2l, 3l, met, pho
Log    = logs/simple_skim_${whichSample}_${whichJob}.log
Output = logs/simple_skim_${whichSample}_${whichJob}.out
Error  = logs/simple_skim_${whichSample}_${whichJob}.error
transfer_input_files = skim.tgz, skim_within_singularity.sh
Requirements = HAS_SINGULARITY == True
+SingularityImage = "/cvmfs/singularity.opensciencegrid.org/cmssw/cms:rhel9"
Queue
EOF
    
    cat submit_${whichSample}_${whichJob}
    echo "Submitting job for sample $whichSample, job $whichJob (sample: $sampleName)"
    echo "--------------------------------"
    echo ""
    echo ""
    echo ""
    echo ""
    echo ""
    echo ""
    # Submit the job
    condor_submit submit_${whichSample}_${whichJob}
    SUBMIT_STATUS=$?
    
    if [ $SUBMIT_STATUS -eq 0 ]; then
        JOB_COUNT=$((JOB_COUNT + 1))
        echo "  Submitted job for sample $whichSample, job $whichJob (sample: $sampleName)"
    else
        echo "  Warning: Failed to submit job for sample $whichSample, job $whichJob"
    fi
    
    # Clean up submit file
    rm -f submit_${whichSample}_${whichJob}
    
done < "$CONDORJOBS"

echo ""
echo "=== Submission Complete ==="
echo "Total jobs submitted: $JOB_COUNT"
echo "Output directory: $OUTPUT_BASE_DIR"
echo "Logs directory: $WORK_DIR/logs"
echo ""
echo "=== Output Files Location ==="
echo "Output ROOT files will be written to:"
echo "  $OUTPUT_BASE_DIR/"
echo "  ├── 1l/<sampleName>/output_1l_<sample>_<job>.root"
echo "  ├── 2l/<sampleName>/output_2l_<sample>_<job>.root"
echo "  ├── 3l/<sampleName>/output_3l_<sample>_<job>.root"
echo "  ├── met/<sampleName>/output_met_<sample>_<job>.root"
echo "  └── pho/<sampleName>/output_pho_<sample>_<job>.root"
echo ""
echo "Example for sample 0, job 0:"
echo "  $OUTPUT_BASE_DIR/1l/<sampleName>/output_1l_0_0.root"
echo "  $OUTPUT_BASE_DIR/2l/<sampleName>/output_2l_0_0.root"
echo "  etc."
echo ""
echo "Note: If worker nodes cannot access $OUTPUT_BASE_DIR, files will be"
echo "written to the job's working directory. Check job logs for details."
echo ""
echo "To check job status:"
echo "  condor_q"
echo ""
echo "To check specific job logs:"
echo "  tail -f $WORK_DIR/logs/simple_skim_<sample>_<job>.log"
echo ""
echo "To list output files after jobs complete:"
echo "  find $OUTPUT_BASE_DIR -name '*.root' -type f"

