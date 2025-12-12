#!/bin/bash

echo "hostname"
hostname
whoami

# Setup CMSSW environment if needed (uncomment if required)
# cd ~/releases/CMSSW_14_1_4/src/
# eval `scramv1 runtime -sh`
# cd -

echo "Parameters: " $1 $2 $3 $4 $5

# $1 = switchSample (or 0 for custom path)
# $2 = year
# $3 = whichJob
# $4 = condorJob (job ID for output naming)
# $5 = analysisName (e.g., "analysis_with_switchSample")

time python3 $5.py --switchSample=$1 --year=$2 --whichJob=$3
status=$?

# Check for output file (adjust filename pattern if needed)
if [ -f "fillhisto_$5_sample$1_year$2_job$3.root" ]; then
  mv fillhisto_$5_sample$1_year$2_job$3.root fillhisto_$5$4_sample$1_year$2_job$3.root
  echo "DONE"

elif [ $status -eq 0 ]; then
  echo "DONE NO FILES"

else
  echo "FAILED"

fi

