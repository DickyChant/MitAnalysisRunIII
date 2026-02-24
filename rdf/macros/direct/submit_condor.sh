#!/bin/sh

# CMS Connect Condor submission for direct NanoAOD analysis
# No skim files needed - worker nodes read raw NanoAOD via XRootD
#
# This is much lighter than the standard submission:
# - No file list collection
# - No data file transfer (just code tarball)
# - Worker nodes stream data directly from the CMS grid
#
# Prerequisites:
#   - Pre-built XRootD file lists in filelists/ (run resolve_sample_files.py first)
#   - Valid VOMS proxy

if [ $# -lt 1 ]; then
   echo "Usage: $0 <anaCode> [condorJob] [group]"
   echo "  anaCode:   1=wz, 5=fake, 6=trigger, 7=met, 9=pu"
   echo "  condorJob: Job ID for output naming (default: 1001)"
   echo "  group:     Number of job groups 0-N (default: depends on analysis)"
   echo ""
   echo "This submits 'direct mode' jobs that read raw NanoAOD via XRootD."
   echo "No skim files are needed. File lists must be pre-generated."
   exit
fi

theAna=$1

# Map analysis code to analysis name and skim type
whichAna="DUMMY"
skimType="2l"
group=9

if [ $theAna -eq 1 ]; then
  whichAna="wzAnalysis"
  skimType="3l"
  group=1

elif [ $theAna -eq 5 ]; then
  whichAna="fakeAnalysis"
  skimType="1l"

elif [ $theAna -eq 6 ]; then
  whichAna="triggerAnalysis"
  skimType="2l"

elif [ $theAna -eq 7 ]; then
  whichAna="metAnalysis"
  skimType="met"

elif [ $theAna -eq 9 ]; then
  whichAna="puAnalysis"
  skimType="2l"

fi

if [ ${whichAna} = "DUMMY" ]; then
   echo "BAD PARAMETER: anaCode=$theAna"
   echo "Valid codes: 1=wz, 5=fake, 6=trigger, 7=met, 9=pu"
   exit 1
fi

condorJob=1001
if [ $# -ge 2 ]; then
  condorJob=$2
fi

if [ $# -ge 3 ]; then
  group=$3
fi

echo "=== Direct NanoAOD Mode ==="
echo "Analysis: ${whichAna} (code ${theAna})"
echo "Skim type: ${skimType}"
echo "Condor job ID: ${condorJob}"
echo "Group size: $((group+1)) jobs per sample"
echo ""

# Check file lists exist
if [ ! -d "filelists" ] || [ -z "$(ls filelists/*.txt 2>/dev/null)" ]; then
   echo "ERROR: No file lists found in filelists/"
   echo "Generate them first:"
   echo "  python3 resolve_sample_files.py --config=../${whichAna}_input_condor_jobs.cfg"
   exit 1
fi

# Check config file
cfgFile="../${whichAna}_input_condor_jobs.cfg"
if [ ! -f "${cfgFile}" ]; then
   echo "Error: Job configuration file ${cfgFile} not found!"
   exit 1
fi

# Verify file lists for configured samples
echo "Checking file lists for configured samples..."
missingLists=0
while IFS= read -r line; do
  if [ -z "$line" ] || [ "${line:0:1}" = "#" ]; then continue; fi
  set -- $line
  whichSample=$1
  passSel=$3
  if [ "${passSel}" = "no" ]; then continue; fi

  if [ $whichSample -lt 1000 ]; then
    # MC sample
    if [ ! -f "filelists/${whichSample}.txt" ]; then
      echo "  MISSING: filelists/${whichSample}.txt"
      missingLists=$((missingLists + 1))
    fi
  else
    # Data sample
    whichYear=$2
    yearShort=$((whichYear / 10))
    if [ ! -f "filelists/data_${whichSample}_${yearShort}.txt" ]; then
      echo "  MISSING: filelists/data_${whichSample}_${yearShort}.txt"
      missingLists=$((missingLists + 1))
    fi
  fi
done < ${cfgFile}

if [ $missingLists -gt 0 ]; then
  echo ""
  echo "ERROR: ${missingLists} file lists are missing."
  echo "Generate them with resolve_sample_files.py before submitting."
  exit 1
fi
echo "All file lists present."
echo ""

# Get user proxy ID for VOMS
USERPROXY=$(id -u)
echo "User proxy ID: ${USERPROXY}"

# Initialize VOMS proxy
echo "Initializing VOMS proxy..."
voms-proxy-init --voms cms --valid 168:00 -pwstdin < $HOME/.grid-cert-passphrase

# Create tarball with analysis code + file lists (from parent directory)
echo "Creating tarball ${whichAna}.tgz..."
cd ..
tar czf ${whichAna}.tgz \
*Analysis.py analysis_runner.sh functions.h utils*.py \
data/* weights_mva/* tmva_helper_xml.* \
mysf.h \
jsns/* config/* jsonpog-integration/* \
direct/filelists/*.txt 2>/dev/null
mv ${whichAna}.tgz direct/
cd direct/

if [ ! -f "${whichAna}.tgz" ]; then
   echo "Error: Failed to create tarball!"
   exit 1
fi
echo "Tarball created: ${whichAna}.tgz"

# Create logs directory
mkdir -p logs

# Read job configuration and submit jobs
echo "Reading job configuration from ${cfgFile}..."

# Count entries
totalEntries=0
skippedEntries=0
while IFS= read -r line; do
  if [ -z "$line" ] || [ "${line:0:1}" = "#" ]; then continue; fi
  set -- $line
  passSel=$3
  if [ "${passSel}" = "no" ]; then
    skippedEntries=$((skippedEntries + 1))
  else
    totalEntries=$((totalEntries + 1))
  fi
done < ${cfgFile}

echo "Found ${totalEntries} entries to process (${skippedEntries} skipped)"
echo ""

jobCount=0
processedSamples=0

while IFS= read -r line; do

  if [ -z "$line" ] || [ "${line:0:1}" = "#" ]; then continue; fi

  set -- $line
  whichSample=$1
  whichYear=$2
  passSel=$3

  if [ "${passSel}" != "no" ]; then
    processedSamples=$((processedSamples + 1))
    echo "Processing sample ${whichSample} for year ${whichYear} (${processedSamples}/${totalEntries})..."

    for whichJob in $(seq 0 $group); do

      cat << EOF > submit
Universe   = vanilla
Executable = analysis_singularity_condor.sh
Arguments  = ${whichSample} ${whichYear} ${whichJob} ${condorJob} ${whichAna}
RequestMemory = 4000
RequestCpus = 1
RequestDisk = 10GB
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
Log    = logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.log
Output = logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.out
Error  = logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.error
transfer_input_files = analysis_singularity_condor.sh,analysis_condor.sh,${whichAna}.tgz
use_x509userproxy = True
x509userproxy = /tmp/x509up_u${USERPROXY}
Queue
EOF

      condor_submit submit
      jobCount=$((jobCount + 1))
      sleep 0.1

    done

  fi

done < ${cfgFile}

rm -f submit

echo ""
echo "=========================================="
echo "Submission complete! (Direct NanoAOD mode)"
echo "Total samples processed: ${processedSamples}"
echo "Total jobs submitted: ${jobCount}"
echo "Analysis: ${whichAna}"
echo "Job ID prefix: ${condorJob}"
echo ""
echo "Key differences from standard mode:"
echo "  - No skim files transferred"
echo "  - Workers read data via XRootD from CMS grid"
echo "  - Disk request: 10GB (code only, no data)"
echo ""
echo "Check status with: condor_q"
echo "Check logs in: logs/"
echo "=========================================="
