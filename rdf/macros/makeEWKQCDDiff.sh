#/bin/sh

# This macro reduces the amount of jobs to run to produce EW+QCD results

if [ $# -lt 2 ]; then
   echo "TOO FEW PARAMETERS"
   exit
fi

export ana=$1

export inpNumber=$2;
export outNumber=$(( $inpNumber + 1000 ));

ls fillhisto_${ana}Analysis${inpNumber}_*root | awk '{split($1,a,"sis"ENVIRON["inpNumber"]);print"cp "$1" "a[1]"sis"ENVIRON["outNumber"]""a[2]}' > exe.sh
chmod a+x exe.sh;./exe.sh;rm -f exe.sh;

cp ${ana}Analysis_input_condor_jobs.cfg ${ana}Analysis_input_condor_jobs_bak.cfg

grep -e "77 " -e "79 " -e "89 " -e "90 " ${ana}Analysis_input_condor_jobs.cfg > exe.sh
mv exe.sh ${ana}Analysis_input_condor_jobs.cfg

sed -i 's/versionDoEWKQCD = False/versionDoEWKQCD = True/' ${ana}Analysis.py

rm -f fillhisto_${ana}Analysis${outNumber}_sample?77_year20???_job?.root
rm -f fillhisto_${ana}Analysis${outNumber}_sample?79_year20???_job?.root
rm -f fillhisto_${ana}Analysis${outNumber}_sample?89_year20???_job?.root
rm -f fillhisto_${ana}Analysis${outNumber}_sample?90_year20???_job?.root
