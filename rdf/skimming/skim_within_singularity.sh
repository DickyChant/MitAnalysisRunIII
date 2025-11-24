#!/bin/bash 

# unset X509_USER_KEY

echo $1 
echo $2
echo $3
echo $4
echo $5

source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=el9_amd64_gcc12
scramv1 project CMSSW CMSSW_14_1_4 # cmsrel is an alias not on the workers
cd CMSSW_14_1_4/src/
eval `scramv1 runtime -sh` # cmsenv is an alias not on the workers
cd ../..

voms-proxy-info

echo "hostname"
hostname
whoami

tar xvzf skim.tgz

ls -l
echo $PWD

# For condor, write files to current directory
# skim.py writes files like output_1l_${whichSample}_${whichJob}.root to current dir first
# Then it copies them to outputDir subdirectories. We set outputDir to ./ so files stay local
# Condor will transfer them back via transfer_output_remaps
python3 skim.py --whichSample=$1 --whichJob=$2 --group=$3 --inputSamplesCfg=$4 --inputFilesCfg=$5 --outputDir=./
status=$?


ls -hal 

mkdir 1l 
mkdir 2l 
mkdir 3l 
mkdir met 
mkdir pho 

# Get the real sample name corresponding to $1 (whichSample) from inputSamplesCfg ($4)
sample_to_skim=$(cat sample_name.txt)

mkdir -p 1l/$sample_to_skim/
mkdir -p 2l/$sample_to_skim/
mkdir -p 3l/$sample_to_skim/
mkdir -p met/$sample_to_skim/
mkdir -p pho/$sample_to_skim/

# Note: Files are written as output_1l_${whichSample}_${whichJob}.root in current directory
# They may also be copied to ./1l/<sample>/ etc. by skim.py, but condor will transfer
# the files from current directory based on transfer_output_files list

cp output_1l_$1_$2.root 1l/$sample_to_skim/
cp output_2l_$1_$2.root 2l/$sample_to_skim/
cp output_3l_$1_$2.root 3l/$sample_to_skim/
cp output_met_$1_$2.root met/$sample_to_skim/
cp output_pho_$1_$2.root pho/$sample_to_skim/

rm -rf skim.tgz skim.py skim_*.cfg functions_skim.h haddnanoaod.py jsns config

if [ $status -eq 0 ]; then
  echo "SUCCESS"

else
  echo "FAILURE"

fi

ls -l
