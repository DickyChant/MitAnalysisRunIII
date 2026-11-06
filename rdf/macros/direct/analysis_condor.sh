#!/bin/sh

# Worker node script for direct NanoAOD mode (CMS Connect)
# Sets up CMS environment, enables direct NanoAOD reading via XRootD,
# then runs the analysis.
#
# Key difference from standard mode: no data files are transferred.
# The analysis reads raw NanoAOD directly from the CMS grid via XRootD.

source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc7_amd64_gcc12
scramv1 project CMSSW CMSSW_13_3_1
cd CMSSW_13_3_1/src/
eval $(scramv1 runtime -sh)
cd ../..

echo "hostname: $(hostname)"
echo "whoami: $(whoami)"
echo "Parameters: $1 $2 $3 $4 $5"

# Check VOMS proxy
voms-proxy-info

# Extract the tarball
echo "Extracting $5.tgz..."
tar xzf $5.tgz

# Enable direct NanoAOD mode
export USE_DIRECT_NANOAOD=1
export FILELIST_DIR="direct/filelists"

echo "Direct NanoAOD mode enabled"
echo "FILELIST_DIR=${FILELIST_DIR}"
echo "File lists available:"
ls -la ${FILELIST_DIR}/*.txt 2>/dev/null | head -5

# XRootD environment setup for reliable grid access
export XRD_NETWORKSTACK=IPv4
export XRD_REQUESTTIMEOUT=600
export XRD_REDIRECTLIMIT=255
export XRD_CONNECTIONRETRY=4
export XRD_STREAMTIMEOUT=120

echo ""
echo "Starting analysis..."

# Run the analysis
# $1 = process (sample ID)
# $2 = year
# $3 = whichJob
# $4 = condorJob
# $5 = analysisName

time python3 $5.py --process=$1 --year=$2 --whichJob=$3
status=$?

# Check for output file and rename with condorJob prefix
if [ -f "fillhisto_$5_sample$1_year$2_job$3.root" ]; then
  mv fillhisto_$5_sample$1_year$2_job$3.root fillhisto_$5$4_sample$1_year$2_job$3.root
  echo "DONE"
elif [ $status -eq 0 ]; then
  echo "DONE NO FILES"
else
  echo "FAILED (exit code: $status)"
fi

# Clean up
rm -rf functions* *.pyc $5.tgz \
*Analysis.py analysis_runner.sh functions.h utils*.py \
data weights_mva tmva_helper_xml.* \
mysf.* \
jsns config jsonpog-integration direct

ls -l
