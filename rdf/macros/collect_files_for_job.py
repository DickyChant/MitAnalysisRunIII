#!/usr/bin/env python3
"""
Collect file lists for Condor jobs from local CMS Connect storage.

This script is called at submission time to determine which files need to be
transferred to remote Condor worker nodes. It resolves local paths and collects
the actual file paths that will be needed for a specific job.

Usage:
    python3 collect_files_for_job.py <switchSample> <year> <whichJob> <skimType> <group>
    
Output:
    Writes a file list to stdout (one file per line) that can be used for Condor transfer.
"""

import sys
import os

# Add current directory to path to import utilsAna
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utilsAna import SwitchSample, getMClist, getDATAlist, groupFiles

def collect_files(switchSample, year, whichJob, skimType="2l", group=10):
    """
    Collect file list for a specific job.
    
    Args:
        switchSample: Sample ID
        year: Year
        whichJob: Job ID (0-based)
        skimType: Skim type (default: "2l")
        group: Number of groups (default: 10)
    
    Returns:
        List of file paths (as strings)
    """
    files = []
    
    # Determine if this is data or MC
    isData = (switchSample >= 1000)
    
    if isData:
        # Get data files (returns ROOT.vector('string'))
        allFilesVec = getDATAlist(switchSample, year, skimType)
    else:
        # Get MC files (returns ROOT.vector('string'))
        allFilesVec = getMClist(switchSample, skimType, year)
    
    # Convert ROOT vector to Python list
    allFiles = [str(allFilesVec[i]) for i in range(allFilesVec.size())]
    
    # Group files
    groupedFiles = groupFiles(allFiles, group)
    
    if whichJob >= len(groupedFiles):
        print(f"Error: whichJob {whichJob} is out of range (max: {len(groupedFiles)-1})", file=sys.stderr)
        return []
    
    # Get files for this specific job
    files = groupedFiles[whichJob]
    
    return files

def main():
    if len(sys.argv) < 4:
        print("Usage: {} <switchSample> <year> <whichJob> [skimType] [group]".format(sys.argv[0]), file=sys.stderr)
        print("  switchSample: Sample ID", file=sys.stderr)
        print("  year: Year", file=sys.stderr)
        print("  whichJob: Job ID (0-based)", file=sys.stderr)
        print("  skimType: Skim type (default: 2l)", file=sys.stderr)
        print("  group: Number of groups (default: 10)", file=sys.stderr)
        sys.exit(1)
    
    switchSample = int(sys.argv[1])
    year = int(sys.argv[2])
    whichJob = int(sys.argv[3])
    skimType = sys.argv[4] if len(sys.argv) > 4 else "2l"
    group = int(sys.argv[5]) if len(sys.argv) > 5 else 10
    
    # Collect files
    files = collect_files(switchSample, year, whichJob, skimType, group)
    
    # Output file list (one per line)
    for f in files:
        print(f)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

