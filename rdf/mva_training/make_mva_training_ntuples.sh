#/bin/sh

if [ $# -lt 1 ]; then
   echo "TOO FEW PARAMETERS"
   exit
fi

if [ $1 = "1" ]; then

cp wzAnalysis.py wzAnalysis_with_ntuples.py
sed -i 's/doNtuples = False/doNtuples = True/' wzAnalysis.py
sed -i 's/useFR = 1/useFR = 0/' wzAnalysis.py

nohup python3 wzAnalysis.py --process=103 --year=20220 --whichJob=-1 >& logwz_00&
nohup python3 wzAnalysis.py --process=108 --year=20220 --whichJob=-1 >& logwz_01&
nohup python3 wzAnalysis.py --process=149 --year=20220 --whichJob=-1 >& logwz_02&
nohup python3 wzAnalysis.py --process=178 --year=20220 --whichJob=-1 >& logwz_03&
nohup python3 wzAnalysis.py --process=179 --year=20220 --whichJob=-1 >& logwz_04&
nohup python3 wzAnalysis.py --process=203 --year=20221 --whichJob=-1 >& logwz_05&
nohup python3 wzAnalysis.py --process=208 --year=20221 --whichJob=-1 >& logwz_06&
nohup python3 wzAnalysis.py --process=249 --year=20221 --whichJob=-1 >& logwz_07&
nohup python3 wzAnalysis.py --process=278 --year=20221 --whichJob=-1 >& logwz_08&
nohup python3 wzAnalysis.py --process=279 --year=20221 --whichJob=-1 >& logwz_09&
nohup python3 wzAnalysis.py --process=303 --year=20230 --whichJob=-1 >& logwz_10&
nohup python3 wzAnalysis.py --process=308 --year=20230 --whichJob=-1 >& logwz_11&
nohup python3 wzAnalysis.py --process=349 --year=20230 --whichJob=-1 >& logwz_12&
nohup python3 wzAnalysis.py --process=378 --year=20230 --whichJob=-1 >& logwz_13&
nohup python3 wzAnalysis.py --process=379 --year=20230 --whichJob=-1 >& logwz_14&
nohup python3 wzAnalysis.py --process=403 --year=20231 --whichJob=-1 >& logwz_15&
nohup python3 wzAnalysis.py --process=408 --year=20231 --whichJob=-1 >& logwz_16&
nohup python3 wzAnalysis.py --process=449 --year=20231 --whichJob=-1 >& logwz_17&
nohup python3 wzAnalysis.py --process=478 --year=20231 --whichJob=-1 >& logwz_18&
nohup python3 wzAnalysis.py --process=479 --year=20231 --whichJob=-1 >& logwz_19&
nohup python3 wzAnalysis.py --process=503 --year=20240 --whichJob=-1 >& logwz_20&
nohup python3 wzAnalysis.py --process=508 --year=20240 --whichJob=-1 >& logwz_21&
nohup python3 wzAnalysis.py --process=549 --year=20240 --whichJob=-1 >& logwz_22&
nohup python3 wzAnalysis.py --process=578 --year=20240 --whichJob=-1 >& logwz_23&
nohup python3 wzAnalysis.py --process=579 --year=20240 --whichJob=-1 >& logwz_24&

elif [ $1 = "10" ]; then

mv wzAnalysis_with_ntuples.py wzAnalysis.py
hadd -f ntupleWZAna_year2027.root ntupleWZAna_*.root

fi
