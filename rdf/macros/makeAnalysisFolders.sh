#/bin/sh

if [ $# -lt 1 ]; then
   echo "TOO FEW PARAMETERS"
   exit
fi

export OUTPUTFOLDER=${ANALYSIS_OUTPUT_DIR:-/home/scratch/$USER/analysis}

rm -rf ${OUTPUTFOLDER}/macros1001
rm -rf ${OUTPUTFOLDER}/macros1002
rm -rf ${OUTPUTFOLDER}/macros1003
rm -rf ${OUTPUTFOLDER}/macros1004
rm -rf ${OUTPUTFOLDER}/macros1005
rm -rf ${OUTPUTFOLDER}/macros1006

cp -r ../macros ${OUTPUTFOLDER}/macros1001
cp -r ../macros ${OUTPUTFOLDER}/macros1002
cp -r ../macros ${OUTPUTFOLDER}/macros1003
cp -r ../macros ${OUTPUTFOLDER}/macros1004
cp -r ../macros ${OUTPUTFOLDER}/macros1005
cp -r ../macros ${OUTPUTFOLDER}/macros1006

#makeDataCards = 4 # 1 (njets), 2-1006 (lepton flavor), 3-1002 (3D), 4-1001 (BDT 2D), 5-1003 (BDT 1D), 6-1004 (mjj), 7-1005 (mjj diff)
sed -i 's/makeDataCards = 4/makeDataCards = 3/'  ${OUTPUTFOLDER}/macros1002/wzAnalysis.py
sed -i 's/makeDataCards = 4/makeDataCards = 5/'  ${OUTPUTFOLDER}/macros1003/wzAnalysis.py
sed -i 's/makeDataCards = 4/makeDataCards = 6/'  ${OUTPUTFOLDER}/macros1004/wzAnalysis.py
sed -i 's/makeDataCards = 4/makeDataCards = 7/'  ${OUTPUTFOLDER}/macros1005/wzAnalysis.py
sed -i 's/makeDataCards = 4/makeDataCards = 2/'  ${OUTPUTFOLDER}/macros1006/wzAnalysis.py

cd ${OUTPUTFOLDER}/macros1006
python3 remake_Analysis_input_condor_jobs.py --ana=wz --isWZMG=0
mv wzAnalysis_input_condor_jobs_new.cfg wzAnalysis_input_condor_jobs.cfg
cd -

sed -i 's/no//' ${OUTPUTFOLDER}/macros1001/wzAnalysis_input_condor_jobs.cfg

if [[ $1 == 1 ]]; then

diff -r ../macros ${OUTPUTFOLDER}/macros1001
diff -r ../macros ${OUTPUTFOLDER}/macros1002
diff -r ../macros ${OUTPUTFOLDER}/macros1003
diff -r ../macros ${OUTPUTFOLDER}/macros1004
diff -r ../macros ${OUTPUTFOLDER}/macros1005
diff -r ../macros ${OUTPUTFOLDER}/macros1006

fi
