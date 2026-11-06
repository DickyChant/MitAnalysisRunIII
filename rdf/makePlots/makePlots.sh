#!/bin/sh

export NSEL=$1;
export APPLYSCALING=$2;
export YEAR=$3;

if [ $NSEL == 'fake' ]; then
  export legendBSM="";
  export isNeverBlinded=0;
  export isBlinded=0;
  export fidAnaName="";
  export mlfitResult="";
  export channelName="XXX"; 

  export SF_DY=0.9;
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_0.root","fakemsel_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_2.root","fakemsel_dphilmet", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_4.root","fakemsel_met", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_6.root","fakemsel_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_8.root","fakemsel_ptloose", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_10.root","fakemsel_etaloose", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_12.root","fakemsel_pttight", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_14.root","fakemsel_etatight", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_16.root","fakemsel_sel0_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_18.root","fakemsel_sel1_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_20.root","fakemsel_sel2_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_22.root","fakemsel_sel3_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_24.root","fakemsel_sel4_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_26.root","fakemsel_sel5_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_28.root","fakemsel_sel0_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_30.root","fakemsel_sel1_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_32.root","fakemsel_sel2_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_34.root","fakemsel_sel3_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_36.root","fakemsel_sel4_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_38.root","fakemsel_sel5_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_40.root","fakemsel_ptl", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_42.root","fakemsel_tthmva", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';

  export SF_DY=0.8;
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_1.root","fakeesel_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_3.root","fakeesel_dphilmet", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_5.root","fakeesel_met", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_7.root","fakeesel_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_9.root","fakeesel_ptloose", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_11.root","fakeesel_etaloose", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_13.root","fakeesel_pttight", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_15.root","fakeesel_etatight", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_17.root","fakeesel_sel0_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_19.root","fakeesel_sel1_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_21.root","fakeesel_sel2_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_23.root","fakeesel_sel3_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_25.root","fakeesel_sel4_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_27.root","fakeesel_sel5_mt_fix", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_29.root","fakeesel_sel0_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_31.root","fakeesel_sel1_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_33.root","fakeesel_sel2_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_35.root","fakeesel_sel3_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_37.root","fakeesel_sel4_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_39.root","fakeesel_sel5_mt", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_41.root","fakeesel_ptl", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"X","GeV","anaZ/fillhisto_fakeAnalysis1001_'${YEAR}'_43.root","fakeesel_tthmva", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';

elif [ $NSEL == 'wz' ]; then
  export legendBSM="";
  export isNeverBlinded=0;
  export isBlinded=0;
  export fidAnaName="";
  export mlfitResult="";
  export channelName="XXX"; 
  export SF_DY=1;
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Min(m_{ll})","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_0.root","wzsel_mllmin", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"|m_{ll}-m_{Z}|","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_1.root","wzsel_mllz", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{3l}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_2.root","wzsel_m3l", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"p_{T}^{l-W}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_3.root","wzsel_ptlw", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"N_{b jets}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_4.root","wzsel_nbtagjet", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Leading p_{T}^{l-Z}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_5.root","wzsel_ptlz1", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Leading p_{T}^{l-Z}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_6.root","wzbsel_ptlz1", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Trailing p_{T}^{l-Z}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_7.root","wzsel_ptlz2", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Trailing p_{T}^{l-Z}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_8.root","wzbsel_ptlz2", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{T}^{W}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_9.root","wzsel_mtw", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{T}^{W}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_10.root","wzbsel_mtw", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Lepton type","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_11.root","wzsel_ltype", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Lepton type","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_12.root","wzbsel_ltype", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"N_{jets}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_13.root","wzsel_njets", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"N_{jets}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_14.root","wzbsel_njets", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"p_{T}^{miss}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_15.root","wzsel_ptmiss", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"p_{T}^{miss}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_16.root","wzbsel_ptmiss", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"N_{jets}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_17.root","wzjjsel_njets", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"N_{jets}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_18.root","wzbjjsel_njets", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{jj}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_19.root","wzjjsel_mjj", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{jj}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_20.root","wzbjjsel_mjj", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"#Delta#eta_{jj}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_21.root","wzjjsel_detajj", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"#Delta#eta_{jj}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_22.root","wzbjjsel_detajj", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"#Delta#phi_{jj}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_23.root","wzjjsel_dphijj", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"#Delta#phi_{jj}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_24.root","wzbjjsel_dphijj", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"BDT","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_25.root","wzjjsel_bdt_vbfincl", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"BDT","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_26.root","wzbjjsel_bdt_vbfincl", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"N_{jets}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_27.root","wzvbssel_njets", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"N_{jets}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_28.root","wzbvbssel_njets", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{jj}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_29.root","wzvbssel_mjj", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{jj}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_30.root","wzbvbssel_mjj", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"#Delta#eta_{jj}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_31.root","wzvbssel_detajj", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"#Delta#eta_{jj}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_32.root","wzbvbssel_detajj", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"#Delta#phi_{jj}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_33.root","wzvbssel_dphijj", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"#Delta#phi_{jj}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_34.root","wzbvbssel_dphijj", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"BDT","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_35.root","wzvbssel_bdt_vbfincl", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"BDT","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_36.root","wzbvbssel_bdt_vbfincl", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{3l}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_37.root","llgsel_m3l", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Lepton type","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_38.root","llgsel_ltype", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"p_{T}^{#gamma}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_39.root","llgsel_ptle", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"p_{T}^{#gamma}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_40.root","llgsel_ptlm", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"N_{b jets}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_51.root","whsel_nbtagjet", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"N_{jets}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_52.root","whsel_njets", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Lepton type","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_53.root","whsel_ltype", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Min(m_{ll})","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_54.root","whsel_mllmin", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"#Delta R_{ll}","","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_55.root","whsel_drllmin", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"p_{T}^{l3}","GeV","anaZ/fillhisto_wzAnalysis1001_'${YEAR}'_56.root","whsel_ptl3", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';

elif [ $NSEL == 'met' ]; then
  export legendBSM="";
  export isNeverBlinded=0;
  export isBlinded=0;
  export fidAnaName="";
  export mlfitResult="";
  export channelName="XXX"; 
  export SF_DY=1;

  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{tot}","GeV","anaZ/fillhistoMETAna1001_'${YEAR}'_0.root","metsel0_mtot", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{tot}","GeV","anaZ/fillhistoMETAna1001_'${YEAR}'_1.root","metsel1_mtot", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{tot}","GeV","anaZ/fillhistoMETAna1001_'${YEAR}'_2.root","metsel2_mtot", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{tot}","GeV","anaZ/fillhistoMETAna1001_'${YEAR}'_3.root","metsel3_mtot", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{tot}","GeV","anaZ/fillhistoMETAna1001_'${YEAR}'_4.root","metsel4_mtot", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"m_{tot}","GeV","anaZ/fillhistoMETAna1001_'${YEAR}'_5.root","metsel5_mtot", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';

  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Min(m_{ll})","GeV","anaZ/fillhistoMETAna1001_'${YEAR}'_6.root","metsel0_mllmin", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Min(m_{ll})","GeV","anaZ/fillhistoMETAna1001_'${YEAR}'_7.root","metsel1_mllmin", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Min(m_{ll})","GeV","anaZ/fillhistoMETAna1001_'${YEAR}'_8.root","metsel2_mllmin", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Min(m_{ll})","GeV","anaZ/fillhistoMETAna1001_'${YEAR}'_9.root","metsel3_mllmin", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Min(m_{ll})","GeV","anaZ/fillhistoMETAna1001_'${YEAR}'_10.root","metsel4_mllmin", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';
  root -q -b -l MitAnalysisRunIII/rdf/makePlots/finalPlot.C+'(0,1,"Min(m_{ll})","GeV","anaZ/fillhistoMETAna1001_'${YEAR}'_11.root","metsel5_mllmin", 0,'${YEAR}',"'${legendBSM}'",'${SF_DY}', '${isBlinded}',"",1,'${APPLYSCALING}',"'${mlfitResult}'","'${channelName}'")';

fi

