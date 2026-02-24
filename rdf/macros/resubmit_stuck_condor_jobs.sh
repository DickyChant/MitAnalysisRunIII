#!/bin/sh

# Re-run stuck/failed jobs interactively
# Usage: Inspect condor_q output, then re-run failed jobs manually
#
# To find failed jobs:
#   grep FAILED logs/*.error
#   grep -L DONE logs/*.out
#
# To re-run a specific job interactively:
#   python3 wzAnalysis.py --process=179 --year=20220 --whichJob=0

echo "Check for failed jobs with:"
echo "  grep FAILED logs/*.out"
echo "  grep -L DONE logs/*.out"
echo ""
echo "Re-run failed jobs interactively with:"
echo "  python3 <analysis>.py --process=<sample> --year=<year> --whichJob=<job>"
echo ""
echo "Or resubmit via condor:"
echo "  ./submit_condor.sh <anaCode> [condorJob] [group]"
