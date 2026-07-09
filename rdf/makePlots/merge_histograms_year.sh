#!/bin/sh

if [ $# -lt 3 ]; then
   echo "TOO FEW PARAMETERS"
   exit
fi

theAna=$1;
theCondor=$2;
theYear=$3;

export OPTIONMVA=0;
if [[ $# -eq 4 ]]; then

export OPTIONMVA=$4;

fi

if [ ${theYear} = 2027 ]; then

    if [[ -f anaZ/${theAna}${theCondor}_20220_nonprompt.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_nonprompt.root anaZ/${theAna}${theCondor}_2022?_nonprompt.root anaZ/${theAna}${theCondor}_2023?_nonprompt.root anaZ/${theAna}${theCondor}_2024?_nonprompt.root

    fi

    if [[ -f anaZ/${theAna}${theCondor}_20220_wrongsign.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_wrongsign.root anaZ/${theAna}${theCondor}_2022?_wrongsign.root anaZ/${theAna}${theCondor}_2023?_wrongsign.root anaZ/${theAna}${theCondor}_2024?_wrongsign.root

    fi

for i in `seq 0 999`;
do
    if [[ -f anaZ/${theAna}${theCondor}_20220_${i}.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_${i}.root anaZ/${theAna}${theCondor}_2022?_${i}.root anaZ/${theAna}${theCondor}_2023?_${i}.root anaZ/${theAna}${theCondor}_2024?_${i}.root

    fi
 
    if [[ -f anaZ/${theAna}${theCondor}_20220_${i}_2d.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_${i}_2d.root anaZ/${theAna}${theCondor}_2022?_${i}_2d.root anaZ/${theAna}${theCondor}_2023?_${i}_2d.root anaZ/${theAna}${theCondor}_2024?_${i}_2d.root

    fi
 
    if [[ ${OPTIONMVA} == 1 ]]; then

        if [[ -f anaZ/${theAna}${theCondor}_20220_${i}_mva.root ]]; then

        hadd -f anaZ/${theAna}${theCondor}_${theYear}_${i}_mva.root anaZ/${theAna}${theCondor}_2022?_${i}_mva.root anaZ/${theAna}${theCondor}_2023?_${i}_mva.root anaZ/${theAna}${theCondor}_2024?_${i}_mva.root

        fi

    fi

done

elif [ ${theYear} = 2028 ]; then

    if [[ -f anaZ/${theAna}${theCondor}_20220_nonprompt.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_nonprompt.root anaZ/${theAna}${theCondor}_202??_nonprompt.root

    fi

    if [[ -f anaZ/${theAna}${theCondor}_20220_wrongsign.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_wrongsign.root anaZ/${theAna}${theCondor}_202??_wrongsign.root

    fi

for i in `seq 0 999`;
do
    if [[ -f anaZ/${theAna}${theCondor}_20220_${i}.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_${i}.root anaZ/${theAna}${theCondor}_202??_${i}.root

    fi
 
    if [[ -f anaZ/${theAna}${theCondor}_20220_${i}_2d.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_${i}_2d.root anaZ/${theAna}${theCondor}_202??_${i}_2d.root

    fi
 
    if [[ ${OPTIONMVA} == 1 ]]; then

        if [[ -f anaZ/${theAna}${theCondor}_20220_${i}_mva.root ]]; then

        hadd -f anaZ/${theAna}${theCondor}_${theYear}_${i}_mva.root anaZ/${theAna}${theCondor}_202??_${i}_mva.root

        fi

    fi

done

elif [ ${theYear} = 2019 ]; then

    if [[ -f anaZ/${theAna}${theCondor}_20180_nonprompt.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_nonprompt.root anaZ/${theAna}${theCondor}_201??_nonprompt.root

    fi

    if [[ -f anaZ/${theAna}${theCondor}_20180_wrongsign.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_wrongsign.root anaZ/${theAna}${theCondor}_201??_wrongsign.root

    fi

for i in `seq 0 999`;
do
    if [[ -f anaZ/${theAna}${theCondor}_20180_${i}.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_${i}.root anaZ/${theAna}${theCondor}_201??_${i}.root

    fi
 
    if [[ -f anaZ/${theAna}${theCondor}_20180_${i}_2d.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_${i}_2d.root anaZ/${theAna}${theCondor}_201??_${i}_2d.root

    fi
 
    if [[ ${OPTIONMVA} == 1 ]]; then

        if [[ -f anaZ/${theAna}${theCondor}_20180_${i}_mva.root ]]; then

        hadd -f anaZ/${theAna}${theCondor}_${theYear}_${i}_mva.root anaZ/${theAna}${theCondor}_201??_${i}_mva.root

        fi

    fi

done

else

    if [[ -f anaZ/${theAna}${theCondor}_${theYear}0_nonprompt.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_nonprompt.root anaZ/${theAna}${theCondor}_${theYear}?_nonprompt.root

    fi

    if [[ -f anaZ/${theAna}${theCondor}_${theYear}0_wrongsign.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_wrongsign.root anaZ/${theAna}${theCondor}_${theYear}?_wrongsign.root

    fi

for i in `seq 0 999`;
do
    if [[ -f anaZ/${theAna}${theCondor}_${theYear}0_${i}.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_${i}.root anaZ/${theAna}${theCondor}_${theYear}?_${i}.root

    fi

    if [[ -f anaZ/${theAna}${theCondor}_${theYear}0_${i}_2d.root ]]; then

    hadd -f anaZ/${theAna}${theCondor}_${theYear}_${i}_2d.root anaZ/${theAna}${theCondor}_${theYear}?_${i}_2d.root

    fi

    if [[ ${OPTIONMVA} == 1 ]]; then

        if [[ -f anaZ/${theAna}${theCondor}_${theYear}0_${i}_mva.root ]]; then

        hadd -f anaZ/${theAna}${theCondor}_${theYear}_${i}_mva.root anaZ/${theAna}${theCondor}_${theYear}?_${i}_mva.root

        fi

    fi

done

fi
