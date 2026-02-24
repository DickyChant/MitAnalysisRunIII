#!/bin/sh

if [ $# -lt 1 ]; then
   echo "TOO FEW PARAMETERS"
   exit
fi

YEAR=$1

USERPROXY=`id -u`
echo ${USERPROXY}

OUTPUT_FOLDER=${SKIM_OUTPUT_DIR:-/home/scratch/$USER/skims}

voms-proxy-init --voms cms --valid 168:00 -pwstdin < $HOME/.grid-cert-passphrase

tar cvzf skim.tgz --exclude='*.csv' \
skim.py skim_*.cfg \
functions_skim.h haddnanoaod.py \
jsns/* config/*

mkdir -p logs;

while IFS= read -r line; do

set -- $line
whichSample=$1
whichJob=$2
group=$3
sampleName=$4

if [ ! -d " ${OUTPUT_FOLDER}/nanoaod/skims_submit/pho/${sampleName}" ]; then
  echo "creating output folders"  ${OUTPUT_FOLDER}/nanoaod/skims_submit/nl/${sampleName}
  mkdir -p  ${OUTPUT_FOLDER}/nanoaod/skims_submit/1l/${sampleName}
  mkdir -p  ${OUTPUT_FOLDER}/nanoaod/skims_submit/2l/${sampleName}
  mkdir -p  ${OUTPUT_FOLDER}/nanoaod/skims_submit/3l/${sampleName}
  mkdir -p  ${OUTPUT_FOLDER}/nanoaod/skims_submit/met/${sampleName}
  mkdir -p  ${OUTPUT_FOLDER}/nanoaod/skims_submit/pho/${sampleName}
fi

cat << EOF > submit
Universe   = vanilla
Executable = skim.sh
Arguments  = ${whichSample} ${whichJob} ${group} skim_input_samples_${YEAR}_fromDAS.cfg skim_input_files_fromDAS.cfg
RequestMemory = 6000
RequestCpus = 1
RequestDisk = DiskUsage
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_output_files = ""
Log    = logs/simple_skim_${whichSample}_${whichJob}.log
Output = logs/simple_skim_${whichSample}_${whichJob}.out
Error  = logs/simple_skim_${whichSample}_${whichJob}.error
transfer_input_files = skim.tgz, skim_within_singularity.sh
use_x509userproxy = True
x509userproxy = /tmp/x509up_u${USERPROXY}
Queue
EOF

condor_submit submit

done < skim_input_condor_jobs_fromDAS.cfg

rm -f submit
