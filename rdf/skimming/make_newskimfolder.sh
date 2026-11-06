#!/bin/sh

SKIM_WORK_DIR=${SKIM_WORK_DIR:-/home/scratch/$USER/skim_work}
REPO_DIR=$(cd "$(dirname "$0")/../.." && pwd)

rm -rf ${SKIM_WORK_DIR}
cp -r ${REPO_DIR}/rdf/skimming ${SKIM_WORK_DIR}
cd ${SKIM_WORK_DIR}
rm config jsns
cp -r ${REPO_DIR}/rdf/macros/jsns .
cp -r ${REPO_DIR}/rdf/macros/config .

if [ $# -eq 1 ] && [ $1 = "online" ]; then

  rm -rf logs

  grep -Ev "tar|rm" skim_within_singularity.sh > skim_new.sh
  diff skim_new.sh skim_within_singularity.sh
  mv skim_new.sh skim_within_singularity.sh
  chmod a+x skim_within_singularity.sh

  source /cvmfs/cms.cern.ch/cmsset_default.sh
  export SCRAM_ARCH=el9_amd64_gcc12
  scramv1 project CMSSW CMSSW_14_1_4
  cd CMSSW_14_1_4/src/
  eval `scramv1 runtime -sh`
  cd ../..

  cat skim_input_condor_jobs_fromDAS.cfg|awk '{print"./skim_within_singularity.sh "$1" "$2" "$3" skim_input_samples_2023_fromDAS.cfg skim_input_files_fromDAS.cfg"}' > lll
  chmod a+x lll

fi

echo "DONE"
