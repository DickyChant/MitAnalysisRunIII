#!/bin/sh

if [ $# -lt 1 ]; then
   echo "TOO FEW PARAMETERS"
   exit
fi

theAna=$1

if [ $theAna -eq 1 ]; then
 cat wzAnalysis_input_condor_jobs.cfg|grep -v no|awk '{print"nohup python3 wzAnalysis.py --process="$1" --year="$2" --whichJob=-1 >& logwz_"NR"&"}' > lll_wz

elif [ $theAna -eq 5 ]; then
 cat fakeAnalysis_input_condor_jobs.cfg|grep -v no|awk '{print"nohup python3 fakeAnalysis.py --process="$1" --year="$2" --whichJob=-1 >& logfake_"NR"&"}' > lll_fake

elif [ $theAna -eq 6 ]; then
 cat triggerAnalysis_input_condor_jobs.cfg|grep -v no|awk '{print"nohup python3 triggerAnalysis.py --process="$1" --year="$2" --whichJob=-1 >& logtrigger_"NR"&"}' > lll_trigger

elif [ $theAna -eq 7 ]; then
 cat metAnalysis_input_condor_jobs.cfg|grep -v no|awk '{print"nohup python3 metAnalysis.py --process="$1" --year="$2" --whichJob=-1 >& logmet_"NR"&"}' > lll_met

elif [ $theAna -eq 9 ]; then
 cat puAnalysis_input_condor_jobs.cfg|grep -v no|awk '{print"nohup python3 puAnalysis.py --process="$1" --year="$2" --whichJob=-1 >& logpu_"NR"&"}' > lll_pu

fi
