#/bin/sh

if [ $# -lt 1 ]; then
   echo "TOO FEW PARAMETERS"
   exit
fi

export OUTPUTFOLDER=/scratch/submit/cms/ceballos/analysis
if [[ $# -eq 2 ]] || [[ $2 == 1 ]]; then

export OUTPUTFOLDER=/work/submit/ceballos/analysis

fi

rm -rf ${OUTPUTFOLDER}/macros1001
rm -rf ${OUTPUTFOLDER}/macros1002
rm -rf ${OUTPUTFOLDER}/macros1003
rm -rf ${OUTPUTFOLDER}/macros1004
rm -rf ${OUTPUTFOLDER}/macros1005
rm -rf ${OUTPUTFOLDER}/macros1006
rm -rf ${OUTPUTFOLDER}/macros1007
rm -rf ${OUTPUTFOLDER}/macros1008
rm -rf ${OUTPUTFOLDER}/macros1009
rm -rf ${OUTPUTFOLDER}/macros1010
rm -rf ${OUTPUTFOLDER}/macros1011
rm -rf ${OUTPUTFOLDER}/macros1012
rm -rf ${OUTPUTFOLDER}/macros1013
rm -rf ${OUTPUTFOLDER}/macros1014

rm -rf ${OUTPUTFOLDER}/macros1020
rm -rf ${OUTPUTFOLDER}/macros1021
rm -rf ${OUTPUTFOLDER}/macros1022

cp -r ../macros ${OUTPUTFOLDER}/macros1001
cp -r ../macros ${OUTPUTFOLDER}/macros1002
cp -r ../macros ${OUTPUTFOLDER}/macros1003
cp -r ../macros ${OUTPUTFOLDER}/macros1004
cp -r ../macros ${OUTPUTFOLDER}/macros1005
cp -r ../macros ${OUTPUTFOLDER}/macros1006
cp -r ../macros ${OUTPUTFOLDER}/macros1007
cp -r ../macros ${OUTPUTFOLDER}/macros1008
cp -r ../macros ${OUTPUTFOLDER}/macros1009
cp -r ../macros ${OUTPUTFOLDER}/macros1010
cp -r ../macros ${OUTPUTFOLDER}/macros1011
cp -r ../macros ${OUTPUTFOLDER}/macros1012
cp -r ../macros ${OUTPUTFOLDER}/macros1013
cp -r ../macros ${OUTPUTFOLDER}/macros1014

cp -r ../macros ${OUTPUTFOLDER}/macros1020
cp -r ../macros ${OUTPUTFOLDER}/macros1021
cp -r ../macros ${OUTPUTFOLDER}/macros1022

#makeDataCards = 1 # 1 (mjj diff), 2 (mll diff), 3 (njets diff), 4 (detajj diff), 5 (dphijj diff), 6 (mjj), 7 (mll), 8 (njets), 9 (detajj), 10 (dphijj), 11 (zepvv), 12 (pol3D), 13 (pol2DLX), 14 (polLL)
sed -i 's/makeDataCards = 1/makeDataCards = 2/'  ${OUTPUTFOLDER}/macros1002/sswwAnalysis.py 
sed -i 's/makeDataCards = 1/makeDataCards = 3/'  ${OUTPUTFOLDER}/macros1003/sswwAnalysis.py 
sed -i 's/makeDataCards = 1/makeDataCards = 4/'  ${OUTPUTFOLDER}/macros1004/sswwAnalysis.py 
sed -i 's/makeDataCards = 1/makeDataCards = 5/'  ${OUTPUTFOLDER}/macros1005/sswwAnalysis.py 
sed -i 's/makeDataCards = 1/makeDataCards = 6/'  ${OUTPUTFOLDER}/macros1006/sswwAnalysis.py 
sed -i 's/makeDataCards = 1/makeDataCards = 7/'  ${OUTPUTFOLDER}/macros1007/sswwAnalysis.py 
sed -i 's/makeDataCards = 1/makeDataCards = 8/'  ${OUTPUTFOLDER}/macros1008/sswwAnalysis.py 
sed -i 's/makeDataCards = 1/makeDataCards = 9/'  ${OUTPUTFOLDER}/macros1009/sswwAnalysis.py 
sed -i 's/makeDataCards = 1/makeDataCards = 10/' ${OUTPUTFOLDER}/macros1010/sswwAnalysis.py 
sed -i 's/makeDataCards = 1/makeDataCards = 11/' ${OUTPUTFOLDER}/macros1011/sswwAnalysis.py 
sed -i 's/makeDataCards = 1/makeDataCards = 12/' ${OUTPUTFOLDER}/macros1012/sswwAnalysis.py 
sed -i 's/makeDataCards = 1/makeDataCards = 13/' ${OUTPUTFOLDER}/macros1013/sswwAnalysis.py 
sed -i 's/makeDataCards = 1/makeDataCards = 14/' ${OUTPUTFOLDER}/macros1014/sswwAnalysis.py 

sed -i 's/makeDataCards = 1/makeDataCards = 6/'  ${OUTPUTFOLDER}/macros1020/sswwAnalysis.py
sed -i 's/makeDataCards = 1/makeDataCards = 6/'  ${OUTPUTFOLDER}/macros1021/sswwAnalysis.py
sed -i 's/makeDataCards = 1/makeDataCards = 6/'  ${OUTPUTFOLDER}/macros1022/sswwAnalysis.py

sed -i 's/versionCharges = 0/versionCharges = +1/' ${OUTPUTFOLDER}/macros1021/sswwAnalysis.py
sed -i 's/versionCharges = 0/versionCharges = -1/' ${OUTPUTFOLDER}/macros1022/sswwAnalysis.py

#makeDataCards = 4 # 1 (njets), 2-1006 (lepton flavor), 3-1002 (3D), 4-1001 (BDT 2D), 5-1003 (BDT 1D), 6-1004 (mjj), 7-1005 (mjj diff)
sed -i 's/makeDataCards = 4/makeDataCards = 3/'  ${OUTPUTFOLDER}/macros1002/wzAnalysis.py
sed -i 's/makeDataCards = 4/makeDataCards = 5/'  ${OUTPUTFOLDER}/macros1003/wzAnalysis.py
sed -i 's/makeDataCards = 4/makeDataCards = 6/'  ${OUTPUTFOLDER}/macros1004/wzAnalysis.py
sed -i 's/makeDataCards = 4/makeDataCards = 7/'  ${OUTPUTFOLDER}/macros1005/wzAnalysis.py
sed -i 's/makeDataCards = 4/makeDataCards = 2/'  ${OUTPUTFOLDER}/macros1006/wzAnalysis.py
rm -f ${OUTPUTFOLDER}/macros1007/wzAnalysis.py
rm -f ${OUTPUTFOLDER}/macros1008/wzAnalysis.py
rm -f ${OUTPUTFOLDER}/macros1009/wzAnalysis.py
rm -f ${OUTPUTFOLDER}/macros1010/wzAnalysis.py

sed -i 's/versionCharges = 0/versionCharges = +1/' ${OUTPUTFOLDER}/macros1021/wzAnalysis.py
sed -i 's/versionCharges = 0/versionCharges = -1/' ${OUTPUTFOLDER}/macros1022/wzAnalysis.py

#makeDataCards = 3 # 1 (njets), 2 (lepton flavor), 3 (mjj)
rm -f ${OUTPUTFOLDER}/macros1002/zzAnalysis.py
rm -f ${OUTPUTFOLDER}/macros1003/zzAnalysis.py
rm -f ${OUTPUTFOLDER}/macros1004/zzAnalysis.py
rm -f ${OUTPUTFOLDER}/macros1005/zzAnalysis.py
sed -i 's/makeDataCards = 3/makeDataCards = 2/'  ${OUTPUTFOLDER}/macros1006/zzAnalysis.py 
rm -f ${OUTPUTFOLDER}/macros1007/zzAnalysis.py
rm -f ${OUTPUTFOLDER}/macros1008/zzAnalysis.py
rm -f ${OUTPUTFOLDER}/macros1009/zzAnalysis.py
rm -f ${OUTPUTFOLDER}/macros1010/zzAnalysis.py

sed -i 's/correctionString = ""/correctionString = "_correction"/'  ${OUTPUTFOLDER}/macros1002/zAnalysis.py
sed -i 's/muSelChoice = 0/muSelChoice = 8/'                         ${OUTPUTFOLDER}/macros1002/zAnalysis.py
sed -i 's/elSelChoice = 0/elSelChoice = 7/'                         ${OUTPUTFOLDER}/macros1002/zAnalysis.py

cd ${OUTPUTFOLDER}/macros1006
python3 remake_Analysis_input_condor_jobs.py --ana=zz --isWZMG=0 --isZZMG=0
python3 remake_Analysis_input_condor_jobs.py --ana=wz --isWZMG=0 --isZZMG=0
mv zzAnalysis_input_condor_jobs_new.cfg zzAnalysis_input_condor_jobs.cfg
mv wzAnalysis_input_condor_jobs_new.cfg wzAnalysis_input_condor_jobs.cfg
cd -

cd ${OUTPUTFOLDER}/macros1012
python3 remake_Analysis_input_condor_jobs.py --ana=ssww --isWWPol=1
mv sswwAnalysis_input_condor_jobs_new.cfg sswwAnalysis_input_condor_jobs.cfg
cd -

cd ${OUTPUTFOLDER}/macros1013
python3 remake_Analysis_input_condor_jobs.py --ana=ssww --isWWPol=1
mv sswwAnalysis_input_condor_jobs_new.cfg sswwAnalysis_input_condor_jobs.cfg
cd -

cd ${OUTPUTFOLDER}/macros1014
python3 remake_Analysis_input_condor_jobs.py --ana=ssww --isWWPol=1
mv sswwAnalysis_input_condor_jobs_new.cfg sswwAnalysis_input_condor_jobs.cfg
cd -

if [[ $1 == 1 ]]; then

diff -r ../macros ${OUTPUTFOLDER}/macros1001
diff -r ../macros ${OUTPUTFOLDER}/macros1002
diff -r ../macros ${OUTPUTFOLDER}/macros1003
diff -r ../macros ${OUTPUTFOLDER}/macros1004
diff -r ../macros ${OUTPUTFOLDER}/macros1005
diff -r ../macros ${OUTPUTFOLDER}/macros1006
diff -r ../macros ${OUTPUTFOLDER}/macros1007
diff -r ../macros ${OUTPUTFOLDER}/macros1008
diff -r ../macros ${OUTPUTFOLDER}/macros1009
diff -r ../macros ${OUTPUTFOLDER}/macros1010
diff -r ../macros ${OUTPUTFOLDER}/macros1011
diff -r ../macros ${OUTPUTFOLDER}/macros1012
diff -r ../macros ${OUTPUTFOLDER}/macros1013
diff -r ../macros ${OUTPUTFOLDER}/macros1014

diff -r ../macros ${OUTPUTFOLDER}/macros1020
diff -r ../macros ${OUTPUTFOLDER}/macros1021
diff -r ../macros ${OUTPUTFOLDER}/macros1022

fi
