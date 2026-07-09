#!/bin/bash

if [ $# -lt 1 ]; then
   echo "TOO FEW PARAMETERS"
   exit
fi

export YEAR=$1;

for preFix in 102 103 104 105;
do

for postFix in 0 1 2 3 4 5 6 7 8 9;
do

   python3 lumiAnalysis.py --year=${YEAR} --process=${preFix}${postFix};

done
done
