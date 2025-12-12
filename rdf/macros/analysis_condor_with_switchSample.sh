#!/bin/sh

# This script runs on the Condor worker node
# It sets up the environment, extracts the tarball, and runs the analysis

source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc7_amd64_gcc12
scramv1 project CMSSW CMSSW_13_3_1 # cmsrel is an alias not on the workers
cd CMSSW_13_3_1/src/
eval `scramv1 runtime -sh` # cmsenv is an alias not on the workers
cd ../..

voms-proxy-info

# Extract the tarball containing all analysis files
tar xzf $5.tgz

echo $PWD

# Run the analysis script
# $1 = switchSample
# $2 = year
# $3 = whichJob
# $4 = condorJob
# $5 = analysisName (e.g., "analysis_with_switchSample")
./analysis_slurm_with_switchSample.sh $1 $2 $3 $4 $5

# Clean up
rm -rf functions* *.pyc $5.tgz \
*Analysis.py analysis_slurm_with_switchSample.sh functions.h utils*.py \
data weights_mva tmva_helper_xml.* \
mysf.* \
jsns config jsonpog-integration 

ls -l
