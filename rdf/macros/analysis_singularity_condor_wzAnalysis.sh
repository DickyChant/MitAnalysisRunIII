#!/bin/sh

# Singularity wrapper for wzAnalysis Condor jobs
# This is a simple wrapper that calls the main condor script

exec analysis_condor_wzAnalysis.sh "$@"

