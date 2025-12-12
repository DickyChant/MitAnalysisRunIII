#!/bin/sh
# Wrapper script for Condor that uses Singularity/CMSSW container
# This is the Executable in the Condor submit file

source /cvmfs/cms.cern.ch/cmsset_default.sh
export APPTAINER_BIND="$PWD"
cmssw-cc7 --command-to-run ./analysis_condor_with_switchSample.sh $1 $2 $3 $4 $5
