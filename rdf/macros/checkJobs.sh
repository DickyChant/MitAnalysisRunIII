#!/bin/sh

if [ $# -lt 3 ]; then
   echo "Usage: ./checkJobs.sh <analysis> <condorJob> <year>"
   exit
fi

export theAna=$1
export condorJob=$2
export year=$3

export group=10

ls logs/${theAna}Analysis_${condorJob}_*_${year}_3.out 2>/dev/null|wc -l|awk '{printf("%d\n",$1*ENVIRON["group"])}'|awk -f ~/bin/sum2.awk;
grep "Total files" logs/${theAna}Analysis_${condorJob}_*_${year}_3.out 2>/dev/null|awk '{a=$3;if(a>ENVIRON["group"])a=ENVIRON["group"];printf("%d\n",a)}'|awk -f ~/bin/sum2.awk;
grep "Total files" logs/${theAna}Analysis_${condorJob}_*_${year}_5.out 2>/dev/null|awk '{a=$3;if(a>ENVIRON["group"])a=ENVIRON["group"];printf("%d\n",a)}'|awk -f ~/bin/sum2.awk;
grep "Total files" logs/${theAna}Analysis_${condorJob}_*_${year}_7.out 2>/dev/null|awk '{a=$3;if(a>ENVIRON["group"])a=ENVIRON["group"];printf("%d\n",a)}'|awk -f ~/bin/sum2.awk;

grep FAILED logs/${theAna}Analysis_${condorJob}_*_${year}_*;
grep DONE   logs/${theAna}Analysis_${condorJob}_*_${year}_*|wc;
grep DONE   logs/${theAna}Analysis_${condorJob}_*_${year}_*|grep -v FILES|wc;
ls fillhisto_${theAna}Analysis${condorJob}*year${year}*|wc
