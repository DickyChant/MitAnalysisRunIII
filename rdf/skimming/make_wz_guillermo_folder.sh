#!/bin/sh

# Script to create a new skimming folder for wz_guillermo analysis
# Based on make_newskimfolder.sh

TARGET_DIR="/home/scratch/stqian/wz_guillermo"
SOURCE_DIR="/home/stqian/MitAnalysisRunIII/rdf/skimming"
MACROS_DIR="/home/stqian/MitAnalysisRunIII/rdf/macros"

echo "=== Creating wz_guillermo skimming folder ==="
echo "Target directory: $TARGET_DIR"
echo "Source directory: $SOURCE_DIR"
echo ""

# Remove old directory if it exists
if [ -d "$TARGET_DIR" ]; then
    echo "Removing existing directory: $TARGET_DIR"
    rm -rf "$TARGET_DIR"
fi

# Create target directory
echo "Creating target directory..."
mkdir -p "$TARGET_DIR" || {
    echo "Error: Failed to create target directory: $TARGET_DIR"
    exit 1
}

# Copy skimming directory
echo "Copying skimming files from $SOURCE_DIR to $TARGET_DIR..."

# Check source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory does not exist: $SOURCE_DIR"
    exit 1
fi

# Use simple cp command that's more reliable
cd "$SOURCE_DIR" || {
    echo "Error: Cannot change to source directory: $SOURCE_DIR"
    exit 1
}

# Copy all files except config, jsns, and logs
echo "  Copying files (this may take a moment)..."
COPIED_COUNT=0
for item in * .[!.]*; do
    # Skip if item doesn't exist (happens when no hidden files)
    [ ! -e "$item" ] && continue
    # Skip directories we'll copy from macros
    [ "$item" = "config" ] && continue
    [ "$item" = "jsns" ] && continue
    [ "$item" = "logs" ] && continue
    [ "$item" = "." ] && continue
    [ "$item" = ".." ] && continue
    
    echo "    Copying: $item"
    if cp -r "$item" "$TARGET_DIR/" 2>&1; then
        COPIED_COUNT=$((COPIED_COUNT + 1))
    else
        echo "    Warning: Failed to copy $item"
    fi
done
cd - > /dev/null

echo "  Copied $COPIED_COUNT items"

# Verify some key files were copied
echo "Verifying copied files..."
MISSING_FILES=0
for keyfile in skim.py skim_within_singularity.sh skim.sh functions_skim.h haddnanoaod.py; do
    if [ ! -f "$TARGET_DIR/$keyfile" ] && [ ! -d "$TARGET_DIR/$keyfile" ]; then
        echo "  ERROR: $keyfile was not copied!"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo "  ERROR: $MISSING_FILES critical files are missing!"
    echo "  Files in target directory:"
    ls -la "$TARGET_DIR" | head -20
    exit 1
fi

echo "  ✓ Verified key files copied successfully"

# Change to target directory
cd "$TARGET_DIR"

# Remove config and jsns if they exist (they might be symlinks)
echo "Removing old config and jsns..."
rm -rf config jsns

# Copy config and jsns from macros directory
echo "Copying config and jsns from $MACROS_DIR..."
if [ -d "$MACROS_DIR/config" ]; then
    cp -r "$MACROS_DIR/config" .
    echo "  Copied config directory"
else
    echo "  Warning: $MACROS_DIR/config not found"
fi

if [ -d "$MACROS_DIR/jsns" ]; then
    cp -r "$MACROS_DIR/jsns" .
    echo "  Copied jsns directory"
else
    echo "  Warning: $MACROS_DIR/jsns not found"
fi

# Remove logs directory if it exists
echo "Removing logs directory..."
rm -rf logs

# Modify skim_within_singularity.sh to remove cleanup rm commands (but keep tar extraction)
echo "Modifying skim_within_singularity.sh..."
if [ -f "skim_within_singularity.sh" ]; then
    # Remove only the cleanup rm command line, but keep tar xvzf for extraction
    # We want to keep: tar xvzf skim.tgz (line 17)
    # We want to remove: rm -rf skim.tgz skim.py ... (cleanup line before SUCCESS/FAILURE)
    # Use sed to remove only the rm cleanup line
    sed '/^rm -rf skim\.tgz/d' skim_within_singularity.sh > skim_new.sh
    
    # Verify tar extraction line is still present
    if ! grep -q "tar xvzf skim.tgz" skim_new.sh; then
        echo "  Error: tar extraction line was removed! This should not happen."
        echo "  Restoring original and only removing rm cleanup line"
        cp skim_within_singularity.sh skim_new.sh
        sed -i '/^rm -rf skim\.tgz/d' skim_new.sh
    fi
    
    # Verify the script still has the essential parts
    if ! grep -q "python3 skim.py" skim_new.sh; then
        echo "  Error: python3 skim.py line missing! Restoring original."
        cp skim_within_singularity.sh skim_new.sh
        sed -i '/^rm -rf skim\.tgz/d' skim_new.sh
    fi
    
    diff skim_new.sh skim_within_singularity.sh || true
    mv skim_new.sh skim_within_singularity.sh
    chmod a+x skim_within_singularity.sh
    echo "  Modified skim_within_singularity.sh (removed cleanup rm command, kept tar extraction)"
else
    echo "  Warning: skim_within_singularity.sh not found"
fi

# Setup CMSSW environment
echo "Setting up CMSSW environment..."
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=el9_amd64_gcc12
scramv1 project CMSSW CMSSW_14_1_4
cd CMSSW_14_1_4/src/
eval `scramv1 runtime -sh`
cd ../..

# Create command script from condor jobs config
echo "Creating command script..."
if [ -f "skim_input_condor_jobs_fromDAS.cfg" ]; then
    # Try to detect the year from available config files
    YEAR_CONFIG=""
    for cfg in skim_input_samples_*_fromDAS.cfg; do
        if [ -f "$cfg" ]; then
            # Extract year from filename (e.g., skim_input_samples_2022a_fromDAS.cfg -> 2022a)
            YEAR_CONFIG=$(echo "$cfg" | sed 's/skim_input_samples_\(.*\)_fromDAS.cfg/\1/')
            break
        fi
    done
    
    if [ -n "$YEAR_CONFIG" ]; then
        cat skim_input_condor_jobs_fromDAS.cfg | awk -v year="$YEAR_CONFIG" '{print"./skim_within_singularity.sh "$1" "$2" "$3" skim_input_samples_"year"_fromDAS.cfg skim_input_files_fromDAS.cfg"}' > lll
        chmod a+x lll
        echo "  Created command script 'lll' for year: $YEAR_CONFIG"
    else
        cat skim_input_condor_jobs_fromDAS.cfg | awk '{print"./skim_within_singularity.sh "$1" "$2" "$3" skim_input_samples_fromDAS.cfg skim_input_files_fromDAS.cfg"}' > lll
        chmod a+x lll
        echo "  Created command script 'lll' (using default config names)"
    fi
else
    echo "  Warning: skim_input_condor_jobs_fromDAS.cfg not found"
    echo "  You may need to run make_skim_input_files_fromDAS.py first"
fi

# Copy condor submission script
echo "Copying condor submission script..."
if [ -f "$SOURCE_DIR/skim_condor_wz_guillermo.sh" ]; then
    cp "$SOURCE_DIR/skim_condor_wz_guillermo.sh" .
    chmod a+x skim_condor_wz_guillermo.sh
    echo "  Copied skim_condor_wz_guillermo.sh"
else
    echo "  Warning: skim_condor_wz_guillermo.sh not found in source"
fi

echo ""
echo "=== DONE ==="
echo "New skimming folder created at: $TARGET_DIR"
echo ""
echo "Next steps:"
echo "1. cd $TARGET_DIR"
echo "2. Review and edit configuration files if needed"
echo "3. Generate input file lists (if not already done):"
echo "   python make_skim_input_files_fromDAS.py --inputCfg=skim_input_samples_<YEAR>_fromDAS.cfg ..."
echo "4. Submit condor jobs:"
echo "   ./skim_condor_wz_guillermo.sh <YEAR> [outputDir]"
echo "   Example: ./skim_condor_wz_guillermo.sh 2022a"
echo "5. Or run jobs interactively using the commands in 'lll'"
echo ""

