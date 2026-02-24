#!/bin/sh

# Singularity wrapper for Condor jobs (CMS Connect)
# This is a simple wrapper that calls the main condor script

exec analysis_condor.sh "$@"
