#!/bin/sh

# Condor submission script for analysis_with_switchSample
# This script creates a tarball with all necessary files and submits Condor jobs

if [ $# -lt 1 ]; then
   echo "Usage: $0 [condorJob] [group]"
   echo "  condorJob: Job ID for output naming (default: 1001)"
   echo "  group: Number of job groups 0-N (default: 9)"
   exit
fi

whichAna="analysis_with_switchSample"
group=9

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
*Analysis.py analysis_slurm_with_switchSample.sh functions.h utils*.py \
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

# Read job configuration file and submit jobs
echo "Reading job configuration from ${whichAna}_input_condor_jobs.cfg..."
jobCount=0

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

    # Loop over job groups
    for whichJob in $(seq 0 $group); do

      # Create Condor submission file
      cat << EOF > submit
Universe   = vanilla
Executable = analysis_singularity_condor_with_switchSample.sh
Arguments  = ${whichSample} ${whichYear} ${whichJob} ${condorJob} ${whichAna}
RequestMemory = 4000
RequestCpus = 1
RequestDisk = DiskUsage
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
Log    = logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.log
Output = logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.out
Error  = logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}.error
transfer_input_files = analysis_condor_with_switchSample.sh,${whichAna}.tgz
use_x509userproxy = True
x509userproxy = /tmp/x509up_u${USERPROXY}
Requirements = ( BOSCOCluster =!= "t3serv008.mit.edu" && BOSCOCluster =!= "ce03.cmsaf.mit.edu" && BOSCOCluster =!= "eofe8.mit.edu") && (Machine != "t3btch003.mit.edu")
+DESIRED_Sites = "mit_tier2,mit_tier3"
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
echo "Total jobs submitted: ${jobCount}"
echo "Job ID prefix: ${condorJob}"
echo "Check status with: condor_q"
echo "Check logs in: logs/"
echo "=========================================="
