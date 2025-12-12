#!/bin/bash

# Wrapper script for wzAnalysis to work with the file transfer system
# wzAnalysis uses --process instead of --switchSample

echo "hostname"
hostname
whoami

echo "Parameters: " $1 $2 $3 $4 $5

# $1 = switchSample (process ID for wzAnalysis)
# $2 = year
# $3 = whichJob
# $4 = condorJob (job ID for output naming)
# $5 = analysisName (should be "wzAnalysis")

# wzAnalysis uses --process instead of --switchSample
# wzAnalysis uses skimType="3l" by default
time python3 $5.py --process=$1 --year=$2 --whichJob=$3
status=$?

# Check for output file (wzAnalysis output naming)
if [ -f "fillhisto_$5_sample$1_year$2_job$3.root" ]; then
  mv fillhisto_$5_sample$1_year$2_job$3.root fillhisto_$5$4_sample$1_year$2_job$3.root
  echo "DONE"

elif [ $status -eq 0 ]; then
  echo "DONE NO FILES"

else
  echo "FAILED"

fi

