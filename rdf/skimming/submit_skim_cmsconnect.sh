#!/bin/bash
# Script to prepare and submit skimming jobs to CMS Connect
# Usage: ./submit_skim_cmsconnect.sh <year> [outputDir]

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <year> [outputDir]"
    echo "  year: Data year (e.g., 2022a, 2023b, etc.)"
    echo "  outputDir: (optional) Output directory for skimmed files"
    echo ""
    echo "Example:"
    echo "  ./submit_skim_cmsconnect.sh 2022a"
    echo "  ./submit_skim_cmsconnect.sh 2023b /store/user/yourusername/skims"
    exit 1
fi

YEAR=$1
OUTPUTDIR=${2:-"./output"}

echo "=== Preparing CMS Connect Skimming Jobs ==="
echo "Year: $YEAR"
echo "Output directory: $OUTPUTDIR"
echo ""

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
    echo "Please run make_skim_input_files_fromDAS.py first"
    exit 1
fi

if [ ! -f "$CONDORJOBS" ]; then
    echo "Error: Condor jobs config not found: $CONDORJOBS"
    echo "Please run make_skim_input_files_fromDAS.py first"
    exit 1
fi

# Create tarball with all necessary files
echo "=== Creating tarball ==="
TARBALL="skim_cmsconnect_${YEAR}.tgz"

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

# Create logs directory
mkdir -p logs

# Generate job submission script
echo "=== Generating job submission commands ==="
JOBSCRIPT="submit_cmsconnect_${YEAR}.sh"

cat > "$JOBSCRIPT" << EOF
#!/bin/bash
# Auto-generated CMS Connect submission script for year $YEAR
# Generated on: $(date)

# Instructions for CMS Connect:
# 1. Upload the tarball: $TARBALL
# 2. Upload this script: $JOBSCRIPT
# 3. For each job, run on CMS Connect:
#    ./skim_cmsconnect.sh <whichSample> <whichJob> <group> <inputSamplesCfg> <inputFilesCfg> [outputDir]

# Or use the commands below for individual jobs:

EOF

# Read the condor jobs config and generate commands
JOB_COUNT=0
while IFS= read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    
    set -- $line
    WHICHSAMPLE=$1
    WHICHJOB=$2
    GROUP=$3
    SAMPLENAME=$4
    
    echo "# Sample: $SAMPLENAME (index $WHICHSAMPLE, job $WHICHJOB, group $GROUP)" >> "$JOBSCRIPT"
    echo "./skim_cmsconnect.sh $WHICHSAMPLE $WHICHJOB $GROUP $INPUTSAMPLESCFG $INPUTFILESCFG $OUTPUTDIR" >> "$JOBSCRIPT"
    echo "" >> "$JOBSCRIPT"
    
    JOB_COUNT=$((JOB_COUNT + 1))
done < "$CONDORJOBS"

chmod +x "$JOBSCRIPT"

echo "Generated job script: $JOBSCRIPT"
echo "Total jobs: $JOB_COUNT"
echo ""

# Create a simple README for CMS Connect
README="README_CMSConnect_${YEAR}.txt"
cat > "$README" << EOF
CMS Connect Skimming Setup for $YEAR
=====================================

Files to upload to CMS Connect:
1. $TARBALL - Contains all necessary scripts and configs
2. $JOBSCRIPT - Job submission script (or use commands below)

Setup on CMS Connect:
---------------------
1. Extract the tarball:
   tar xzf $TARBALL

2. Make scripts executable:
   chmod +x skim_cmsconnect.sh
   chmod +x $JOBSCRIPT

3. Run individual jobs:
   ./skim_cmsconnect.sh <whichSample> <whichJob> <group> <inputSamplesCfg> <inputFilesCfg> [outputDir]

   Or use the generated script:
   ./$JOBSCRIPT

Example for a single job:
-------------------------
./skim_cmsconnect.sh 0 0 5 $INPUTSAMPLESCFG $INPUTFILESCFG ./output

Job Configuration:
------------------
- Input samples: $INPUTSAMPLESCFG
- Input files: $INPUTFILESCFG
- Total jobs: $JOB_COUNT
- Output directory: $OUTPUTDIR

Notes:
------
- Ensure you have a valid VOMS proxy: voms-proxy-init --voms cms
- The script will automatically set up CMSSW if needed
- Output files will be saved to the specified output directory
- Check logs for job status

For more information, see the main README.md
EOF

echo "Created README: $README"
echo ""
echo "=== Summary ==="
echo "Tarball: $TARBALL"
echo "Job script: $JOBSCRIPT"
echo "README: $README"
echo "Total jobs: $JOB_COUNT"
echo ""
echo "Next steps:"
echo "1. Upload $TARBALL and $JOBSCRIPT to CMS Connect"
echo "2. Extract the tarball on CMS Connect"
echo "3. Run the jobs using $JOBSCRIPT or individual commands"
echo "4. See $README for detailed instructions"

