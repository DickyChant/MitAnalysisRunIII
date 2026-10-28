#!/bin/sh

if [ $# -lt 2 ]; then
   echo "TOO FEW PARAMETERS"
   exit
fi

export theOption=$2

if [ $theOption -eq 0 ]; then

  export theAna=wwAnalysis$1
  export whichAna=0

  for year in 20220 20221 20230 20231 20240 20250;
  do

  for bin in 1 2 3 4;
  do

  for isFid in 0 1;
  do

  root -l -q -b makeWWDataCards.C'('${whichAna}','${bin}',"anaZ","'${theAna}'",'${year}','${isFid}')'

  done
  done
  done

elif [ $theOption -eq 1 ]; then
  if [ $# -lt 3 ]; then
     echo "TOO FEW PARAMETERS"
     exit
  fi

  export theAna=wwAnalysis$1
  export whichAna=$3

  for year in 20220 20221 20230 20231 20240 20250;
  do

  for bin in 1 2 3;
  do

  for isFid in 0;
  do

  root -l -q -b makeWWDataCards.C'('${whichAna}','${bin}',"anaZ","'${theAna}'",'${year}','${isFid}')'

  done
  done
  done

elif [ $theOption -eq 2 ]; then


  for year in 20220 20221 20230 20231 20240 20250;
  do

  export theAnaWZ=wzAnalysis$1
  export theAnaZZ=zzAnalysis$1

  for bin in 0 1;
  do
  root -l -q -b makeVVDataCards.C'(0,'${bin}',"anaZ","'${theAnaWZ}'",'${year}')'

  done

  root -l -q -b makeVVDataCards.C'(0,0,"anaZ","'${theAnaZZ}'",'${year}')'
  done

fi
