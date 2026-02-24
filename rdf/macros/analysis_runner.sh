#!/bin/bash

# Analysis runner script for CMS Connect Condor jobs
# Runs any analysis with --process/--year/--whichJob arguments

echo "hostname"
hostname
whoami

echo "Parameters: " $1 $2 $3 $4 $5

# $1 = process (sample ID)
# $2 = year
# $3 = whichJob
# $4 = condorJob (job ID for output naming)
# $5 = analysisName (e.g. wzAnalysis, fakeAnalysis, etc.)

time python3 $5.py --process=$1 --year=$2 --whichJob=$3
status=$?

# Check for output file and rename with condorJob prefix
if [ -f "fillhisto_$5_sample$1_year$2_job$3.root" ]; then
  mv fillhisto_$5_sample$1_year$2_job$3.root fillhisto_$5$4_sample$1_year$2_job$3.root
  echo "DONE"

elif [ $status -eq 0 ]; then
  echo "DONE NO FILES"

else
  echo "FAILED"

fi
