#!/usr/bin/env python3
"""
Analysis script template that accepts switchSample as a command-line option.

This script follows the same pattern as other analysis scripts but allows
switchSample to be specified directly via --switchSample or --sample option.
It also supports custom sample paths for running on custom skimming output.

Usage:
    # Using switchSample ID (from utilsAna.py)
    python3 analysis_with_switchSample.py --switchSample=<sample_id> --year=<year> --whichJob=<job_id> [--skimType=<skim_type>]
    
    # Using custom sample path directly
    python3 analysis_with_switchSample.py --samplePath=<path> --year=<year> [--customXsec=<xsec>] [--customCategory=<category>]
    
    # Override base directory for SwitchSample lookup
    python3 analysis_with_switchSample.py --switchSample=<id> --baseDir=<base_dir> --year=<year>
"""

import ROOT
import os, sys, getopt, json, time

ROOT.ROOT.EnableImplicitMT(4)
from utilsCategory import plotCategory
from utilsAna import getMClist, getDATAlist, findDIR
from utilsAna import SwitchSample, groupFiles, getTriggerFromJson, getLeptomSelFromJson, getLumi

# Default values
switchSample = None  # Will be set if provided
samplePath = None    # Custom sample path (overrides switchSample)
year = 2022
whichJob = -1
skimType = "2l"  # Default skim type
baseDir = None   # Override base directory for SwitchSample
customXsec = None  # Custom cross section when using samplePath
customCategory = None  # Custom category when using samplePath

def main():
    global switchSample, samplePath, year, whichJob, skimType, baseDir, customXsec, customCategory
    
    # Parse command-line arguments
    valid = ['year=', 'switchSample=', 'sample=', 'samplePath=', 'path=', 'whichJob=', 
             'skimType=', 'baseDir=', 'customXsec=', 'customCategory=', 'help']
    usage = "Usage: analysis_with_switchSample.py [options]\n"
    usage += "\nOptions:\n"
    usage += "  --switchSample=<id> or --sample=<id>  : Sample ID from utilsAna.py\n"
    usage += "  --samplePath=<path> or --path=<path>  : Direct path to sample directory (overrides switchSample)\n"
    usage += "  --year=<year>                          : Year (default: {})\n".format(year)
    usage += "  --whichJob=<job_id>                    : Job ID (default: {})\n".format(whichJob)
    usage += "  --skimType=<type>                      : Skim type (default: {})\n".format(skimType)
    usage += "  --baseDir=<dir>                        : Override base directory for SwitchSample lookup\n"
    usage += "  --customXsec=<xsec>                    : Custom cross section (required with --samplePath)\n"
    usage += "  --customCategory=<cat>                 : Custom category (optional with --samplePath)\n"
    usage += "  --help                                 : Show this help message"
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", valid)
    except getopt.GetoptError as ex:
        print(usage)
        print("Error: " + str(ex))
        sys.exit(1)

    for opt, arg in opts:
        if opt == "--help":
            print(usage)
            sys.exit(0)
        elif opt == "--year":
            year = int(arg)
        elif opt == "--switchSample" or opt == "--sample":
            switchSample = int(arg)
        elif opt == "--samplePath" or opt == "--path":
            samplePath = os.path.abspath(arg) if not os.path.isabs(arg) else arg
        elif opt == "--whichJob":
            whichJob = int(arg)
        elif opt == "--skimType":
            skimType = str(arg)
        elif opt == "--baseDir":
            baseDir = str(arg)
        elif opt == "--customXsec":
            customXsec = float(arg)
        elif opt == "--customCategory":
            customCategory = str(arg)

    # Validate that either switchSample or samplePath is provided
    if switchSample is None and samplePath is None:
        print("Error: Must provide either --switchSample or --samplePath")
        print(usage)
        sys.exit(1)
    
    if switchSample is not None and samplePath is not None:
        print("Warning: Both --switchSample and --samplePath provided. Using --samplePath (overriding switchSample)")
        switchSample = None

    # Handle custom path mode
    if samplePath is not None:
        if not os.path.exists(samplePath):
            print("Error: Sample path does not exist: {}".format(samplePath))
            sys.exit(1)
        if customXsec is None:
            print("Error: --customXsec is required when using --samplePath")
            sys.exit(1)
        
        # Use custom path
        sample_dir = samplePath
        xsec = customXsec
        category = plotCategory(customCategory) if customCategory else plotCategory("kPlotOther")
        
        print("=" * 60)
        print("Analysis Configuration (Custom Path Mode):")
        print("  Sample path: {}".format(sample_dir))
        print("  Cross section: {}".format(xsec))
        print("  Category: {}".format(category))
        print("  year: {}".format(year))
        print("  whichJob: {}".format(whichJob))
        print("=" * 60)
        
        # Get files from custom path
        files = findDIR(sample_dir)
        if len(files) == 0:
            print("Warning: No files found in {}".format(sample_dir))
            print("Retrying in 10 seconds...")
            time.sleep(10)
            files = findDIR(sample_dir)
        
        if len(files) == 0:
            print("Error: No files found after retry. Exiting.")
            sys.exit(1)
        
        print("Total files found: {}".format(len(files)))
        
        # Extract PDType from path
        PDType = os.path.basename(sample_dir).split("+")[0] if "+" in os.path.basename(sample_dir) else os.path.basename(sample_dir)
        isData = False  # Assume MC unless specified otherwise
        
    else:
        # Use switchSample mode
        # Override base directory if provided
        if baseDir is not None:
            # Temporarily modify SwitchSample behavior by patching dirT2
            # Note: This is a workaround - ideally SwitchSample would accept baseDir parameter
            print("Warning: --baseDir option requires modification of utilsAna.py SwitchSample function")
            print("Consider using --samplePath instead for custom directories")
        
        # Validate switchSample (pass year for year-dependent paths)
        sample_info = SwitchSample(switchSample, skimType, year)
        if sample_info == "BKGdefault, xsecDefault, category":
            print("Error: Invalid switchSample value: {}".format(switchSample))
            print("Please check utilsAna.py for valid sample IDs.")
            sys.exit(1)
        
        # Print configuration
        print("=" * 60)
        print("Analysis Configuration (SwitchSample Mode):")
        print("  switchSample: {}".format(switchSample))
        print("  year: {}".format(year))
        print("  whichJob: {}".format(whichJob))
        print("  skimType: {}".format(skimType))
        print("  Sample directory: {}".format(sample_info[0]))
        print("  Cross section: {}".format(sample_info[1]))
        print("  Category: {}".format(sample_info[2]))
        print("=" * 60)
        
        # Get cross section and other info from SwitchSample
        xsec = sample_info[1]
        category = sample_info[2]
        sample_dir = sample_info[0]
        
        # Extract PDType from directory name
        PDType = os.path.basename(sample_dir).split("+")[0] if "+" in os.path.basename(sample_dir) else "Unknown"
        
        # Determine if this is MC or Data based on switchSample value
        isData = (switchSample >= 1000)
        
        if isData:
            print("Processing DATA sample...")
            # Get file list for data
            files = getDATAlist(switchSample, year, skimType)
            if len(files) == 0:
                print("Warning: No files found for switchSample={}, year={}, skimType={}".format(
                    switchSample, year, skimType))
                print("Retrying in 10 seconds...")
                time.sleep(10)
                files = getDATAlist(switchSample, year, skimType)
            
            if len(files) == 0:
                print("Error: No files found after retry. Exiting.")
                sys.exit(1)
            
            print("Total files found: {}".format(len(files)))
            xsec = 1.0  # Data doesn't need cross section
            weight = 1.0
        else:
            print("Processing MC sample...")
            # Get file list (pass year for year-dependent paths)
            files = getMClist(switchSample, skimType, year)
            if len(files) == 0:
                print("Warning: No files found for switchSample={}, year={}, skimType={}".format(
                    switchSample, year, skimType))
                print("Retrying in 10 seconds...")
                time.sleep(10)
                files = getMClist(switchSample, skimType)
            
            if len(files) == 0:
                print("Error: No files found after retry. Exiting.")
                sys.exit(1)
            
            print("Total files found: {}".format(len(files)))
    
    # Get luminosity
    lumi = getLumi(year)
    print("Luminosity for year {}: {}".format(year, lumi))
    
    # Group files if whichJob is specified
    group = 1  # Default group size, adjust as needed
    if whichJob != -1:
        groupedFile = groupFiles(files, group)
        if whichJob >= len(groupedFile):
            print("Error: whichJob {} is out of range (max: {})".format(whichJob, len(groupedFile) - 1))
            sys.exit(1)
        files = groupedFile[whichJob]
        if len(files) == 0:
            print("Error: No files in job/group: {} / {}".format(whichJob, group))
            sys.exit(1)
        print("Using {} files for job {}".format(len(files), whichJob))
    
    # Create RDataFrame
    print("Creating RDataFrame from {} files...".format(len(files)))
    df = ROOT.RDataFrame("Events", files)
    nevents = df.Count().GetValue()
    print("Total events in files: {}".format(nevents))
    
    # Get genEventSumWeight for MC (if available and not data)
    if not isData:
        dfRuns = ROOT.RDataFrame("Runs", files)
        genEventSumWeight = dfRuns.Sum("genEventSumw").GetValue()
        genEventSumNoWeight = dfRuns.Sum("genEventCount").GetValue()
        
        if genEventSumWeight > 0:
            weight = (xsec / genEventSumWeight) * lumi
            weightApprox = (xsec / genEventSumNoWeight) * lumi
            print("Weight (exact/approx): {} / {}".format(weight, weightApprox))
        else:
            print("Warning: genEventSumWeight is 0, cannot calculate proper weight")
            weight = 1.0
    else:
        weight = 1.0
    
    # Determine sample identifier for analysis function
    sample_id = switchSample if switchSample is not None else 0  # Use 0 for custom paths
    
    # Call your analysis function here
    # analysis(df, sample_id, category, weight, year, PDType, "true" if isData else "false", whichJob, ...)
    print("\n" + "=" * 60)
    print("Analysis processing would happen here...")
    print("Please implement your analysis() function based on your needs.")
    print("\nExample call:")
    print("  analysis(df, {}, {}, {}, {}, '{}', '{}', {}, ...)".format(
        sample_id, category, weight, year, PDType, "true" if isData else "false", whichJob))
    print("=" * 60)

if __name__ == "__main__":
    main()


