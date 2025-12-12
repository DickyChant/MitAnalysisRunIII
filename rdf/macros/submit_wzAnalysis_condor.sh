#!/bin/sh

# Condor submission script for wzAnalysis
# This script creates a tarball with all necessary files and submits Condor jobs
# Uses the file transfer system for CMS Connect

if [ $# -lt 1 ]; then
   echo "Usage: $0 [condorJob] [group]"
   echo "  condorJob: Job ID for output naming (default: 1001)"
   echo "  group: Number of job groups 0-N (default: 1, wzAnalysis typically uses group=1)"
   exit
fi

whichAna="wzAnalysis"
group=1  # wzAnalysis typically uses group=1

condorJob=1001
if [ $# -ge 1 ]; then
  condorJob=$1
fi

if [ $# -ge 2 ]; then
  group=$2
fi

if [ ! -f "${whichAna}_input_condor_jobs.cfg" ]; then
   echo "Error: Job configuration file ${whichAna}_input_condor_jobs.cfg not found!"
   echo "Please create it with format: <switchSample> <year> [no]"
   exit 1
fi

# Get user proxy ID for VOMS
USERPROXY=`id -u`
echo "User proxy ID: ${USERPROXY}"

# Initialize VOMS proxy (required for accessing CMS data)
echo "Initializing VOMS proxy..."
voms-proxy-init --voms cms --valid 168:00 -pwstdin < $HOME/.grid-cert-passphrase

# Create tarball with all necessary files
echo "Creating tarball ${whichAna}.tgz..."
tar cvzf ${whichAna}.tgz \
*Analysis.py analysis_slurm*.sh functions.h utils*.py \
data/* weights_mva/* tmva_helper_xml.* \
mysf.h \
jsns/* config/* jsonpog-integration/* 2>/dev/null

if [ ! -f "${whichAna}.tgz" ]; then
   echo "Error: Failed to create tarball!"
   exit 1
fi

echo "Tarball created: ${whichAna}.tgz"

# Create logs directory
mkdir -p logs

# Create directory for file lists (for CMS Connect file transfer)
mkdir -p file_lists

# Read job configuration file and submit jobs
echo "Reading job configuration from ${whichAna}_input_condor_jobs.cfg..."

# Count total entries first (for summary)
totalEntries=0
skippedEntries=0
while IFS= read -r line; do
  if [ -z "$line" ] || [ "${line:0:1}" = "#" ]; then
    continue
  fi
  set -- $line
  passSel=$3
  if [ "${passSel}" = "no" ]; then
    skippedEntries=$((skippedEntries + 1))
  else
    totalEntries=$((totalEntries + 1))
  fi
done < ${whichAna}_input_condor_jobs.cfg

echo "Found ${totalEntries} entries to process (${skippedEntries} skipped)"
echo ""

jobCount=0
processedSamples=0

while IFS= read -r line; do

  # Skip empty lines and comments
  if [ -z "$line" ] || [ "${line:0:1}" = "#" ]; then
    continue
  fi

  set -- $line
  whichSample=$1
  whichYear=$2
  passSel=$3

  if [ "${passSel}" != "no" ]; then
    processedSamples=$((processedSamples + 1))
    echo "Processing sample ${whichSample} for year ${whichYear} (${processedSamples}/${totalEntries})..."

    # Loop over job groups
    for whichJob in $(seq 0 $group); do

      # Collect file list for this job (from local CMS Connect storage)
      # wzAnalysis uses skimType="3l" by default
      skimType="3l"
      fileListName="file_lists/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.txt"
      echo "Collecting files for sample=${whichSample}, year=${whichYear}, job=${whichJob}..."
      
      # Collect files using Python script
      # Redirect stderr to .err file, stdout (file paths) to .txt file
      python3 collect_files_for_job.py ${whichSample} ${whichYear} ${whichJob} ${skimType} $((group+1)) > ${fileListName} 2>${fileListName}.err
      
      # Filter out any non-file paths (debug messages that might have leaked to stdout)
      # Keep only lines that look like file paths (contain .root or start with /)
      if [ -f "${fileListName}" ]; then
        grep -E '\.root$|^/' "${fileListName}" > "${fileListName}.tmp" 2>/dev/null
        if [ -s "${fileListName}.tmp" ]; then
          mv "${fileListName}.tmp" "${fileListName}"
        else
          # If filtering removed everything, keep original (might be valid)
          rm -f "${fileListName}.tmp"
        fi
      fi
      
      if [ ! -s "${fileListName}" ]; then
        echo "Warning: No files found for sample=${whichSample}, year=${whichYear}, job=${whichJob}"
        echo "Error output:"
        cat ${fileListName}.err
        # Skip this job if no files found
        continue
      fi
      
      fileCount=$(wc -l < ${fileListName})
      echo "  Found ${fileCount} files to transfer"
      
      # Verify first file is actually a file path (not a debug message)
      firstFile=$(head -n1 ${fileListName} 2>/dev/null)
      if [ -z "$firstFile" ] || [ "$firstFile" = "year:" ] || [ "$firstFile" = "dirT2:" ] || [ ! -f "$firstFile" ]; then
        echo "  Warning: First entry in file list doesn't look like a valid file path: '$firstFile'"
        echo "  This might indicate debug output leaked to the file list"
        echo "  Check ${fileListName}.err for details"
        # Try to recover by filtering more aggressively
        grep -E '^/.*\.root$' "${fileListName}" > "${fileListName}.filtered" 2>/dev/null
        if [ -s "${fileListName}.filtered" ]; then
          mv "${fileListName}.filtered" "${fileListName}"
          fileCount=$(wc -l < ${fileListName})
          echo "  After aggressive filtering: ${fileCount} valid file paths"
          firstFile=$(head -n1 ${fileListName} 2>/dev/null)
        fi
      fi
      
      # Calculate total size of files (for disk request)
      totalSize=0
      while IFS= read -r filepath; do
        if [ -f "$filepath" ]; then
          size=$(stat -f%z "$filepath" 2>/dev/null || stat -c%s "$filepath" 2>/dev/null || echo 0)
          totalSize=$((totalSize + size))
        fi
      done < ${fileListName}
      
      # Convert to GB (with 20% overhead)
      diskGB=$((totalSize / 1024 / 1024 / 1024 + 1))
      diskGB=$((diskGB + diskGB / 5))  # Add 20% overhead
      if [ $diskGB -lt 10 ]; then
        diskGB=10  # Minimum 10GB
      fi
      
      echo "  Estimated disk needed: ${diskGB}GB"
      
      # Create Condor submission file with file transfer
      # Build transfer_input_files list
      transferFiles="analysis_condor_wzAnalysis.sh,analysis_slurm_wzAnalysis.sh,${whichAna}.tgz,${fileListName}"
      
      # Check if files are on local filesystem (CMS Connect storage)
      firstFile=$(head -n1 ${fileListName} 2>/dev/null)
      if [ -n "$firstFile" ] && [ -f "$firstFile" ]; then
        # Files are local - transfer them directly (ROOT files are already binary/compressed)
        echo "  Adding ${fileCount} files to transfer list..."
        
        # Add files directly to transfer list
        fileCounter=0
        while IFS= read -r filepath; do
          if [ -f "$filepath" ]; then
            transferFiles="${transferFiles},${filepath}"
            fileCounter=$((fileCounter + 1))
          else
            echo "  Warning: File not found: ${filepath}"
          fi
        done < ${fileListName}
        
        echo "  Added ${fileCounter} files to transfer list"
        
        # Update disk request - files are transferred as-is, no extraction needed
        diskGB=$((diskGB + 2))  # Add 2GB overhead for file handling
      else
        echo "  Warning: First file not found or file list is empty"
        echo "  First file: ${firstFile}"
      fi
      
      # Create Condor submission file
      # Note: wzAnalysis uses analysis_condor_wzAnalysis.sh which calls analysis_slurm_wzAnalysis.sh
      cat << EOF > submit
Universe   = vanilla
Executable = analysis_singularity_condor_wzAnalysis.sh
Arguments  = ${whichSample} ${whichYear} ${whichJob} ${condorJob} ${whichAna}
RequestMemory = 4000
RequestCpus = 1
RequestDisk = ${diskGB}GB
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
Log    = logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.log
Output = logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.out
Error  = logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.error
transfer_input_files = ${transferFiles}
use_x509userproxy = True
x509userproxy = /tmp/x509up_u${USERPROXY}
# Requirements = ( BOSCOCluster =!= "t3serv008.mit.edu" && BOSCOCluster =!= "ce03.cmsaf.mit.edu" && BOSCOCluster =!= "eofe8.mit.edu") && (Machine != "t3btch003.mit.edu")
# +DESIRED_Sites = "mit_tier2,mit_tier3"
Queue
EOF

      condor_submit submit
      jobCount=$((jobCount + 1))
      sleep 0.1

    done

  fi

done < ${whichAna}_input_condor_jobs.cfg

rm -f submit

echo ""
echo "=========================================="
echo "Submission complete!"
echo "Total samples processed: ${processedSamples}"
echo "Total jobs submitted: ${jobCount}"
echo "Job ID prefix: ${condorJob}"
echo "Group size: $((group+1)) jobs per sample"
echo ""
echo "Check status with: condor_q"
echo "Check logs in: logs/"
echo "Check file lists in: file_lists/"
echo "=========================================="

