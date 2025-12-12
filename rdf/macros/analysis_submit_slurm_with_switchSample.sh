#!/bin/sh

if [ $# -lt 1 ]; then
   echo "Usage: $0 [condorJob] [group]"
   echo "  condorJob: Job ID for output naming (default: 1001)"
   echo "  group: Number of job groups 0-N (default: 9)"
   exit
fi

whichAna="analysis_with_switchSample"
group=9

condorJob=1001
if [ $# -ge 1 ]; then
  condorJob=$1
fi

if [ $# -ge 2 ]; then
  group=$2
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Read job configuration file
while IFS= read -r line; do

  set -- $line
  whichSample=$1
  whichYear=$2
  passSel=$3

  if [ "${passSel}" != "no" ]; then

    # Loop over job groups
    for whichJob in $(seq 0 $group); do

      # Create SLURM submission script
      cat << EOF > submit
#!/bin/bash
#SBATCH --job-name=${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}
#SBATCH --output=logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}_%j.out
#SBATCH --error=logs/${whichAna}_${condorJob}_${whichSample}_${whichYear}_${whichJob}_%j.error
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=3000M
#SBATCH --time=04:00:00
srun ./analysis_slurm_with_switchSample.sh ${whichSample} ${whichYear} ${whichJob} ${condorJob} ${whichAna}
EOF

      sbatch submit
      sleep 0.1

    done

  fi

done < ${whichAna}_input_condor_jobs.cfg

rm -f submit
echo "All jobs submitted! Check status with: squeue -u \$USER"

