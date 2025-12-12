#!/bin/sh

# Script to create analysis folder structure in scratch directory
# Similar to make_wz_guillermo_folder.sh for skimming
# This sets up the directory structure needed for running analysis jobs

TARGET_DIR="/home/scratch/stqian/analysis"
SOURCE_DIR="/home/stqian/MitAnalysisRunIII/rdf/macros"
SKIMMING_DIR="/home/stqian/MitAnalysisRunIII/rdf/skimming"

echo "=== Creating analysis folder structure ==="
echo "Target directory: $TARGET_DIR"
echo "Source directory: $SOURCE_DIR"
echo ""

# Remove old directory if it exists (optional - comment out if you want to keep existing)
# if [ -d "$TARGET_DIR" ]; then
#     echo "Removing existing directory: $TARGET_DIR"
#     rm -rf "$TARGET_DIR"
# fi

# Create target directory
echo "Creating target directory..."
mkdir -p "$TARGET_DIR" || {
    echo "Error: Failed to create target directory: $TARGET_DIR"
    exit 1
}

# Create directory structure for analysis outputs
echo "Creating analysis directory structure..."

# Create main output directories for different skim types
for skimtype in 1l 2l 3l met pho; do
    mkdir -p "$TARGET_DIR/outputs/${skimtype}"
    echo "  Created: $TARGET_DIR/outputs/${skimtype}"
done

# Create directory for histograms and other analysis outputs
mkdir -p "$TARGET_DIR/histograms"
mkdir -p "$TARGET_DIR/logs"
mkdir -p "$TARGET_DIR/file_lists"
mkdir -p "$TARGET_DIR/configs"

echo "  Created: $TARGET_DIR/histograms"
echo "  Created: $TARGET_DIR/logs"
echo "  Created: $TARGET_DIR/file_lists"
echo "  Created: $TARGET_DIR/configs"

# Create symlinks or copies of necessary files from macros directory
echo ""
echo "Setting up analysis files..."

# Copy key analysis scripts
if [ -d "$SOURCE_DIR" ]; then
    cd "$SOURCE_DIR" || {
        echo "Error: Cannot change to source directory: $SOURCE_DIR"
        exit 1
    }
    
    # Copy analysis scripts
    echo "  Copying analysis scripts..."
    for script in *Analysis.py analysis_with_switchSample.py; do
        if [ -f "$script" ]; then
            cp "$script" "$TARGET_DIR/" 2>/dev/null && echo "    Copied: $script" || echo "    Skipped: $script"
        fi
    done
    
    # Copy utility scripts
    echo "  Copying utility scripts..."
    for util in utils*.py collect_files_for_job.py; do
        if [ -f "$util" ]; then
            cp "$util" "$TARGET_DIR/" 2>/dev/null && echo "    Copied: $util" || echo "    Skipped: $util"
        fi
    done
    
    # Copy submission scripts (including wzAnalysis-specific submit_wzAnalysis_condor.sh)
    echo "  Copying submission scripts..."
    for submit in analysis_*.sh submit_*.sh; do
        if [ -f "$submit" ]; then
            cp "$submit" "$TARGET_DIR/" 2>/dev/null && echo "    Copied: $submit" || echo "    Skipped: $submit"
        fi
    done
    # Also copy wzAnalysis-specific worker scripts explicitly
    for wzscript in analysis_condor_wzAnalysis.sh analysis_singularity_condor_wzAnalysis.sh analysis_slurm_wzAnalysis.sh; do
        if [ -f "$wzscript" ]; then
            cp "$wzscript" "$TARGET_DIR/" 2>/dev/null && echo "    Copied: $wzscript" || echo "    Skipped: $wzscript"
        fi
    done
    
    # Copy header files
    echo "  Copying header files..."
    for header in *.h; do
        if [ -f "$header" ]; then
            cp "$header" "$TARGET_DIR/" 2>/dev/null && echo "    Copied: $header" || echo "    Skipped: $header"
        fi
    done
    
    # Copy config and jsns directories
    echo "  Copying config and jsns directories..."
    if [ -d "config" ]; then
        cp -r config "$TARGET_DIR/" && echo "    Copied: config/" || echo "    Failed to copy: config/"
    fi
    
    if [ -d "jsns" ]; then
        cp -r jsns "$TARGET_DIR/" && echo "    Copied: jsns/" || echo "    Failed to copy: jsns/"
    fi
    
    # Copy data and weights directories if they exist
    if [ -d "data" ]; then
        cp -r data "$TARGET_DIR/" && echo "    Copied: data/" || echo "    Failed to copy: data/"
    fi
    
    if [ -d "weights_mva" ]; then
        cp -r weights_mva "$TARGET_DIR/" && echo "    Copied: weights_mva/" || echo "    Failed to copy: weights_mva/"
    fi
    
    if [ -d "jsonpog-integration" ]; then
        cp -r jsonpog-integration "$TARGET_DIR/" && echo "    Copied: jsonpog-integration/" || echo "    Failed to copy: jsonpog-integration/"
    fi
    
    cd - > /dev/null
else
    echo "  Warning: Source directory does not exist: $SOURCE_DIR"
fi

# Make scripts executable
echo ""
echo "Making scripts executable..."
cd "$TARGET_DIR" || exit 1
chmod +x *.sh 2>/dev/null
chmod +x collect_files_for_job.py 2>/dev/null
echo "  Made scripts executable"

# Copy job configuration files (including wzAnalysis_input_condor_jobs.cfg)
echo ""
echo "Copying job configuration files..."
if [ -d "$SOURCE_DIR" ]; then
    cd "$SOURCE_DIR" || exit 1
    for cfg in *_input_condor_jobs.cfg; do
        if [ -f "$cfg" ]; then
            cp "$cfg" "$TARGET_DIR/" 2>/dev/null && echo "    Copied: $cfg" || echo "    Skipped: $cfg"
        fi
    done
    cd - > /dev/null
else
    echo "  Warning: Source directory does not exist, cannot copy config files"
fi

# Create example job configuration file if it doesn't exist
if [ ! -f "$TARGET_DIR/analysis_with_switchSample_input_condor_jobs.cfg" ]; then
    echo ""
    echo "Creating example job configuration file..."
    cat > "$TARGET_DIR/analysis_with_switchSample_input_condor_jobs.cfg" << 'EOF'
# Analysis job configuration file
# Format: <switchSample> <year> [no]
# Lines starting with # are comments
# Add "no" at the end to skip a line

# Example: Process sample 101 (DY) for year 20220
101 20220

# Example: Process sample 102 (WW) for year 20220
102 20220

# Example: Skip this line
# 103 20220 no
EOF
    echo "  Created: analysis_with_switchSample_input_condor_jobs.cfg"
fi

# Create a README with instructions
echo ""
echo "Creating README..."
cat > README.md << 'EOF'
# Analysis Directory

This directory contains the analysis setup for running Condor jobs.

## Directory Structure

```
analysis/
├── outputs/          # Analysis output files (organized by skim type)
│   ├── 1l/
│   ├── 2l/
│   ├── 3l/
│   ├── met/
│   └── pho/
├── histograms/       # Histogram output files
├── logs/            # Condor job logs
├── file_lists/      # File lists for job submission
├── configs/         # Configuration files
├── config/           # Analysis configuration
├── jsns/             # JSON files
├── data/              # Scale factors, weights, etc.
└── weights_mva/      # MVA weights
```

## Quick Start

1. **Create job configuration file**:
   ```bash
   # Edit or create analysis_with_switchSample_input_condor_jobs.cfg
   # Format: <switchSample> <year> [no]
   ```

2. **Submit jobs**:
   ```bash
   ./analysis_submit_condor_with_switchSample.sh 1001 9
   ```

3. **Monitor jobs**:
   ```bash
   condor_q -submitter $USER
   ```

4. **Check outputs**:
   ```bash
   ls -lh fillhisto_*.root
   ```

## File Locations

- **Output files**: `fillhisto_*.root` (in current directory after job completion)
- **Logs**: `logs/analysis_with_switchSample_*.{log,out,error}`
- **File lists**: `file_lists/analysis_with_switchSample_*.txt`

## Notes

- Make sure your skim files are accessible (paths configured in `utilsAna.py`)
- VOMS proxy is initialized automatically by the submission script
- Files are transferred from CMS Connect storage to remote Condor nodes

## See Also

- `CMS_CONNECT_EXECUTION_GUIDE.md` - Detailed execution guide
- `CMS_CONNECT_FILE_TRANSFER.md` - File transfer documentation
EOF
echo "  Created: README.md"

# Create a helper script to check setup
echo ""
echo "Creating setup check script..."
cat > check_setup.sh << 'EOF'
#!/bin/bash
# Script to check if analysis setup is complete

echo "=== Checking Analysis Setup ==="
echo ""

ERRORS=0
WARNINGS=0

# Check required directories
echo "Checking directories..."
for dir in outputs/histograms logs file_lists configs; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir exists"
    else
        echo "  ✗ $dir missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check required files
echo ""
echo "Checking required files..."
for file in utilsAna.py collect_files_for_job.py analysis_submit_condor_with_switchSample.sh; do
    if [ -f "$file" ]; then
        echo "  ✓ $file exists"
    else
        echo "  ✗ $file missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check config directories
echo ""
echo "Checking config directories..."
for dir in config jsns; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir exists"
    else
        echo "  ⚠ $dir missing (may be needed)"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# Check job config file
echo ""
echo "Checking job configuration..."
if [ -f "analysis_with_switchSample_input_condor_jobs.cfg" ]; then
    line_count=$(grep -v '^#' analysis_with_switchSample_input_condor_jobs.cfg | grep -v '^$' | wc -l)
    echo "  ✓ Job config file exists ($line_count jobs configured)"
else
    echo "  ⚠ Job config file missing (create analysis_with_switchSample_input_condor_jobs.cfg)"
    WARNINGS=$((WARNINGS + 1))
fi

# Summary
echo ""
echo "=== Summary ==="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✓ Setup is complete!"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "✓ Setup is mostly complete ($WARNINGS warnings)"
    exit 0
else
    echo "✗ Setup has $ERRORS errors and $WARNINGS warnings"
    exit 1
fi
EOF
chmod +x check_setup.sh
echo "  Created: check_setup.sh"

echo ""
echo "=== DONE ==="
echo "Analysis folder created at: $TARGET_DIR"
echo ""
echo "Files copied include:"
echo "  ✓ All *Analysis.py scripts (including wzAnalysis.py)"
echo "  ✓ All submission scripts (including submit_wzAnalysis_condor.sh)"
echo "  ✓ All worker scripts (including wzAnalysis-specific ones)"
echo "  ✓ All job config files (including wzAnalysis_input_condor_jobs.cfg)"
echo "  ✓ All utility scripts and supporting files"
echo ""
echo "Next steps:"
echo "1. cd $TARGET_DIR"
echo "2. Run setup check: ./check_setup.sh"
echo ""
echo "For WZ Analysis:"
echo "3. Verify wzAnalysis_input_condor_jobs.cfg has your samples"
echo "   (All entries in the file will be processed automatically)"
echo "4. Verify file paths in utilsAna.py point to your 3l skim files"
echo "5. Submit WZ jobs: ./submit_wzAnalysis_condor.sh 1001 1"
echo ""
echo "For other analyses:"
echo "3. Edit job configuration: <analysis>_input_condor_jobs.cfg"
echo "4. Submit jobs: ./analysis_submit_condor_with_switchSample.sh 1001 9"
echo ""
echo "Directory structure:"
echo "  $TARGET_DIR/"
echo "  ├── outputs/          # Analysis outputs (by skim type)"
echo "  ├── histograms/       # Histogram files"
echo "  ├── logs/             # Condor logs"
echo "  ├── file_lists/       # File lists for jobs"
echo "  ├── configs/          # Configuration files"
echo "  ├── wzAnalysis.py     # WZ analysis script"
echo "  ├── submit_wzAnalysis_condor.sh  # WZ submission script"
echo "  ├── wzAnalysis_input_condor_jobs.cfg  # WZ job config"
echo "  └── [other analysis files]"
echo ""

