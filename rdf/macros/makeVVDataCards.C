#include <TROOT.h>
#include <TFile.h>
#include <TTree.h>
#include <TSystem.h>
#include <TString.h>
#include <TRandom.h>
#include <TH1D.h>
#include <TH2D.h>
#include <TMath.h>
#include <iostream>
#include <fstream>
#include "TLorentzVector.h"
#include "TColor.h"

#include "../makePlots/common.h"

// whichAna = 0 (WZ), fidAna = 0 (SR), 1 (CR)
// whichAna = 0 (ZZ), fidAna = 0 (SR)

void makeVVDataCards(int whichAna = 0, int fidAna = 0, TString InputDir = "anaZ", TString anaSel = "wwAnalysis1001", int year = 20221){

  if(fidAna < 0 || fidAna > 2) printf("Wrong fidAna(%d)\n",fidAna);

  plotBaseNames[kPlotNonPrompt] = "NonPromptWZ";

  int theYear = 0;
  TString theTagYear = "NULL";
  double triggerEffUnc = 1.000;
  double lumiU[4] = {1.000, 1.000, 1.000, 1.000};
  if     (year == 20220) {triggerEffUnc = 1.005; lumiU[0] = 1.0138; lumiU[1] = 1.0000; lumiU[2] = 1.0000; lumiU[3] = 1.0000; theYear = 2022; theTagYear = "2022";}
  else if(year == 20221) {triggerEffUnc = 1.005; lumiU[0] = 1.0138; lumiU[1] = 1.0000; lumiU[2] = 1.0000; lumiU[3] = 1.0000; theYear = 2022; theTagYear = "2022EE";}
  else if(year ==  2022) {triggerEffUnc = 1.005; lumiU[0] = 1.0138; lumiU[1] = 1.0000; lumiU[2] = 1.0000; lumiU[3] = 1.0000; theYear = 2022; theTagYear = "2022";}
  else if(year == 20230) {triggerEffUnc = 1.005; lumiU[0] = 1.0017; lumiU[1] = 1.0127; lumiU[2] = 1.0000; lumiU[3] = 1.0000; theYear = 2023; theTagYear = "2023";}
  else if(year == 20231) {triggerEffUnc = 1.005; lumiU[0] = 1.0017; lumiU[1] = 1.0127; lumiU[2] = 1.0000; lumiU[3] = 1.0000; theYear = 2023; theTagYear = "2023BPix";}
  else if(year ==  2023) {triggerEffUnc = 1.005; lumiU[0] = 1.0017; lumiU[1] = 1.0127; lumiU[2] = 1.0000; lumiU[3] = 1.0000; theYear = 2023; theTagYear = "2023";}
  else if(year == 20240) {triggerEffUnc = 1.005; lumiU[0] = 1.0020; lumiU[1] = 1.0068; lumiU[2] = 1.0144; lumiU[3] = 1.0000; theYear = 2024; theTagYear = "2024";}
  else if(year == 20250) {triggerEffUnc = 1.005; lumiU[0] = 1.0000; lumiU[1] = 1.0000; lumiU[2] = 1.0000; lumiU[3] = 1.0500; theYear = 2025; theTagYear = "2025";}
  else {printf("Wrong year!\n"); return;}

  int jumpValue = 200;

  double systValue;
  TFile *inputFile;
  TFile *outputFile;
  const int endTheory = 113;
  const int nSystTotal = 168;
  const int nSystDataCardTotal = 110; // (nSystTotal-endTheory)*2 = nSystDataCardTotal

  TH1D *histo_Baseline[nPlotCategories];
  TH1D *histo_QCDScaleUp[nPlotCategories];
  TH1D *histo_QCDScaleDown[nPlotCategories];
  TH1D *histo_PSUp[nPlotCategories];
  TH1D *histo_PSDown[nPlotCategories];

  TH1D *histo_Syst[nSystTotal][nPlotCategories];
  TH1D *histo_SystDataCard[nSystDataCardTotal][nPlotCategories];
  TH1D *histo_PDFUp  [101][nPlotCategories];
  TH1D *histo_PDFDown[101][nPlotCategories];

  const int numberBTagSyst = 4;
  TString BtagSFNames[numberBTagSyst] = {"CMS_btag_fixedWP_bc_correlated",    Form("CMS_btag_fixedWP_bc_uncorrelated_%s",theTagYear.Data()),
                                         "CMS_btag_fixedWP_light_correlated", Form("CMS_btag_fixedWP_light_uncorrelated_%s",theTagYear.Data())};

  const int numberJESSyst = 28;
  TString jesNames[numberJESSyst] = {"", "AbsoluteMPFBias", "AbsoluteScale", "AbsoluteStat", "FlavorQCD", "Fragmentation", "PileUpDataMC", "PileUpPtBB", "PileUpPtEC1", "PileUpPtEC2", "PileUpPtHF", "PileUpPtRef", "RelativeFSR", "RelativeJEREC1", "RelativeJEREC2", "RelativeJERHF", "RelativePtBB", "RelativePtEC1", "RelativePtEC2", "RelativePtHF", "RelativeBal", "RelativeSample", "RelativeStatEC", "RelativeStatFSR", "RelativeStatHF", "SinglePionECAL", "SinglePionHCAL", "TimePtEta"};

  jesNames[ 3] = Form("%s_%s"  ,jesNames[ 3].Data(),theTagYear.Data()); // AbsoluteStat
  jesNames[13] = Form("%s_%s"  ,jesNames[13].Data(),theTagYear.Data()); // RelativeJEREC1
  jesNames[14] = Form("%s_%s"  ,jesNames[14].Data(),theTagYear.Data()); // RelativeJEREC2
  jesNames[17] = Form("%s_%s"  ,jesNames[17].Data(),theTagYear.Data()); // RelativePtEC1
  jesNames[18] = Form("%s_%s"  ,jesNames[18].Data(),theTagYear.Data()); // RelativePtEC2
  jesNames[21] = Form("%s_%s"  ,jesNames[21].Data(),theTagYear.Data()); // RelativeSample
  jesNames[22] = Form("%s_%s"  ,jesNames[22].Data(),theTagYear.Data()); // RelativeStatEC
  jesNames[23] = Form("%s_%s"  ,jesNames[23].Data(),theTagYear.Data()); // RelativeStatFSR
  jesNames[24] = Form("%s_%s"  ,jesNames[24].Data(),theTagYear.Data()); // RelativeStatHF
  jesNames[27] = Form("%s_%s"  ,jesNames[27].Data(),theTagYear.Data()); // TimePtEta

  TString nameSyst[nSystDataCardTotal];
  nameSyst[  0] = Form("CMS_eff_m_reco_%sUp",theTagYear.Data());
  nameSyst[  1] = Form("CMS_eff_m_reco_%sDown",theTagYear.Data());
  nameSyst[  2] = Form("CMS_eff_m_id_%sUp",theTagYear.Data());
  nameSyst[  3] = Form("CMS_eff_m_id_%sDown",theTagYear.Data());
  nameSyst[  4] = Form("CMS_eff_m_iso_%sUp",theTagYear.Data());
  nameSyst[  5] = Form("CMS_eff_m_iso_%sDown",theTagYear.Data());
  nameSyst[  6] = Form("CMS_eff_e_reco_%sUp",theTagYear.Data());
  nameSyst[  7] = Form("CMS_eff_e_reco_%sDown",theTagYear.Data());
  nameSyst[  8] = Form("CMS_eff_e_idUp");
  nameSyst[  9] = Form("CMS_eff_e_idDown");
  nameSyst[10 ] = "pileup_13p6TeVUp";
  nameSyst[11 ] = "pileup_13p6TeVDown";
  nameSyst[12 ] = Form("CMS_SMP25013_WWtrigger_%sUp",theTagYear.Data());
  nameSyst[13 ] = Form("CMS_SMP25013_WWtrigger_%sDown",theTagYear.Data());
  nameSyst[14 ] = Form("CMS_SMP25013_eff_m_tightid_%sUp",theTagYear.Data());
  nameSyst[15 ] = Form("CMS_SMP25013_eff_m_tightid_%sDown",theTagYear.Data());
  nameSyst[16 ] = Form("CMS_SMP25013_eff_e_tightid_%sUp",theTagYear.Data());
  nameSyst[17 ] = Form("CMS_SMP25013_eff_e_tightid_%sDown",theTagYear.Data());
  nameSyst[18 ] = Form("%sUp"  ,BtagSFNames[ 0].Data());
  nameSyst[19 ] = Form("%sDown",BtagSFNames[ 0].Data());
  nameSyst[20 ] = Form("%sUp"  ,BtagSFNames[ 1].Data());
  nameSyst[21 ] = Form("%sDown",BtagSFNames[ 1].Data());
  nameSyst[22 ] = Form("%sUp"  ,BtagSFNames[ 2].Data());
  nameSyst[23 ] = Form("%sDown",BtagSFNames[ 2].Data());
  nameSyst[24 ] = Form("%sUp"  ,BtagSFNames[ 3].Data());
  nameSyst[25 ] = Form("%sDown",BtagSFNames[ 3].Data());
  nameSyst[26 ] = "dummy";
  nameSyst[27 ] = "dummy";
  nameSyst[28 ] = "dummy";
  nameSyst[29 ] = "dummy";
  nameSyst[30 ] = "dummy";
  nameSyst[31 ] = "dummy";
  nameSyst[32 ] = "dummy";
  nameSyst[33 ] = "dummy";
  nameSyst[34 ] = "dummy";
  nameSyst[35 ] = "dummy";
  nameSyst[36 ] = "dummy";
  nameSyst[37 ] = "dummy";
  nameSyst[38 ] = "dummy";
  nameSyst[39 ] = "dummy";
  nameSyst[40 ] = "dummy";
  nameSyst[41 ] = "dummy";
  nameSyst[42 ] = Form("CMS_scale_m_%sUp",theTagYear.Data());
  nameSyst[43 ] = Form("CMS_scale_m_%sDown",theTagYear.Data());
  nameSyst[44 ] = Form("CMS_scale_e_%sUp",theTagYear.Data());
  nameSyst[45 ] = Form("CMS_scale_e_%sDown",theTagYear.Data());
  nameSyst[46 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 0].Data());
  nameSyst[47 ] = Form("CMS_scale_j_%sDown",jesNames[ 0].Data());
  nameSyst[48 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 1].Data());
  nameSyst[49 ] = Form("CMS_scale_j_%sDown",jesNames[ 1].Data());
  nameSyst[50 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 2].Data());
  nameSyst[51 ] = Form("CMS_scale_j_%sDown",jesNames[ 2].Data());
  nameSyst[52 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 3].Data());
  nameSyst[53 ] = Form("CMS_scale_j_%sDown",jesNames[ 3].Data());
  nameSyst[54 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 4].Data());
  nameSyst[55 ] = Form("CMS_scale_j_%sDown",jesNames[ 4].Data());
  nameSyst[56 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 5].Data());
  nameSyst[57 ] = Form("CMS_scale_j_%sDown",jesNames[ 5].Data());
  nameSyst[58 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 6].Data());
  nameSyst[59 ] = Form("CMS_scale_j_%sDown",jesNames[ 6].Data());
  nameSyst[60 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 7].Data());
  nameSyst[61 ] = Form("CMS_scale_j_%sDown",jesNames[ 7].Data());
  nameSyst[62 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 8].Data());
  nameSyst[63 ] = Form("CMS_scale_j_%sDown",jesNames[ 8].Data());
  nameSyst[64 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 9].Data());
  nameSyst[65 ] = Form("CMS_scale_j_%sDown",jesNames[ 9].Data());
  nameSyst[66 ] = Form("CMS_scale_j_%sUp"  ,jesNames[10].Data());
  nameSyst[67 ] = Form("CMS_scale_j_%sDown",jesNames[10].Data());
  nameSyst[68 ] = Form("CMS_scale_j_%sUp"  ,jesNames[11].Data());
  nameSyst[69 ] = Form("CMS_scale_j_%sDown",jesNames[11].Data());
  nameSyst[70 ] = Form("CMS_scale_j_%sUp"  ,jesNames[12].Data());
  nameSyst[71 ] = Form("CMS_scale_j_%sDown",jesNames[12].Data());
  nameSyst[72 ] = Form("CMS_scale_j_%sUp"  ,jesNames[13].Data());
  nameSyst[73 ] = Form("CMS_scale_j_%sDown",jesNames[13].Data());
  nameSyst[74 ] = Form("CMS_scale_j_%sUp"  ,jesNames[14].Data());
  nameSyst[75 ] = Form("CMS_scale_j_%sDown",jesNames[14].Data());
  nameSyst[76 ] = Form("CMS_scale_j_%sUp"  ,jesNames[15].Data());
  nameSyst[77 ] = Form("CMS_scale_j_%sDown",jesNames[15].Data());
  nameSyst[78 ] = Form("CMS_scale_j_%sUp"  ,jesNames[16].Data());
  nameSyst[79 ] = Form("CMS_scale_j_%sDown",jesNames[16].Data());
  nameSyst[80 ] = Form("CMS_scale_j_%sUp"  ,jesNames[17].Data());
  nameSyst[81 ] = Form("CMS_scale_j_%sDown",jesNames[17].Data());
  nameSyst[82 ] = Form("CMS_scale_j_%sUp"  ,jesNames[18].Data());
  nameSyst[83 ] = Form("CMS_scale_j_%sDown",jesNames[18].Data());
  nameSyst[84 ] = Form("CMS_scale_j_%sUp"  ,jesNames[19].Data());
  nameSyst[85 ] = Form("CMS_scale_j_%sDown",jesNames[19].Data());
  nameSyst[86 ] = Form("CMS_scale_j_%sUp"  ,jesNames[20].Data());
  nameSyst[87 ] = Form("CMS_scale_j_%sDown",jesNames[20].Data());
  nameSyst[88 ] = Form("CMS_scale_j_%sUp"  ,jesNames[21].Data());
  nameSyst[89 ] = Form("CMS_scale_j_%sDown",jesNames[21].Data());
  nameSyst[90 ] = Form("CMS_scale_j_%sUp"  ,jesNames[22].Data());
  nameSyst[91 ] = Form("CMS_scale_j_%sDown",jesNames[22].Data());
  nameSyst[92 ] = Form("CMS_scale_j_%sUp"  ,jesNames[23].Data());
  nameSyst[93 ] = Form("CMS_scale_j_%sDown",jesNames[23].Data());
  nameSyst[94 ] = Form("CMS_scale_j_%sUp"  ,jesNames[24].Data());
  nameSyst[95 ] = Form("CMS_scale_j_%sDown",jesNames[24].Data());
  nameSyst[96 ] = Form("CMS_scale_j_%sUp"  ,jesNames[25].Data());
  nameSyst[97 ] = Form("CMS_scale_j_%sDown",jesNames[25].Data());
  nameSyst[98 ] = Form("CMS_scale_j_%sUp"  ,jesNames[26].Data());
  nameSyst[99 ] = Form("CMS_scale_j_%sDown",jesNames[26].Data());
  nameSyst[100] = Form("CMS_scale_j_%sUp"  ,jesNames[27].Data());
  nameSyst[101] = Form("CMS_scale_j_%sDown",jesNames[27].Data());
  nameSyst[102] = Form("CMS_res_j_%sUp",theTagYear.Data());
  nameSyst[103] = Form("CMS_res_j_%sDown",theTagYear.Data());
  nameSyst[104] = Form("CMS_scale_met_jer_%sUp",theTagYear.Data());
  nameSyst[105] = Form("CMS_scale_met_jer_%sDown",theTagYear.Data());
  nameSyst[106] = Form("CMS_scale_met_jes_%sUp",theTagYear.Data());
  nameSyst[107] = Form("CMS_scale_met_jes_%sDown",theTagYear.Data());
  nameSyst[108] = Form("CMS_scale_met_unclustered_energy_%sUp",theTagYear.Data());
  nameSyst[109] = Form("CMS_scale_met_unclustered_energy_%sDown",theTagYear.Data());

  //int BinXF = 4; double minXF = -0.5; double maxXF = 3.5;
  int BinXF = 1; double minXF = -0.5; double maxXF = 3.5;

  if(anaSel.Contains("zzAnalysis")) {
    printf("Modifying default binning\n");
    //BinXF = 3; minXF = -0.5; maxXF = 2.5;
    BinXF = 1; minXF = -0.5; maxXF = 2.5;
  }

  for(int ic=0; ic<nPlotCategories; ic++) {
    histo_Baseline[ic] = new TH1D(Form("histo_%s",plotBaseNames[ic].Data()),Form("histo_%s",plotBaseNames[ic].Data()), BinXF, minXF, maxXF);
    TString plotBaseNamesTemp =  plotBaseNames[ic];
    histo_QCDScaleUp  [ic] = (TH1D*)histo_Baseline[ic]->Clone(Form("histo_%s_QCD_scale_%s_ACCEPTUp"  , plotBaseNames[ic].Data(), plotBaseNamesTemp.Data()));
    histo_QCDScaleDown[ic] = (TH1D*)histo_Baseline[ic]->Clone(Form("histo_%s_QCD_scale_%s_ACCEPTDown", plotBaseNames[ic].Data(), plotBaseNamesTemp.Data()));
    histo_PSUp  [ic]       = (TH1D*)histo_Baseline[ic]->Clone(Form("histo_%s_PS_%s_ACCEPTUp"  , plotBaseNames[ic].Data(), plotBaseNamesTemp.Data()));
    histo_PSDown[ic]       = (TH1D*)histo_Baseline[ic]->Clone(Form("histo_%s_PS_%s_ACCEPTDown", plotBaseNames[ic].Data(), plotBaseNamesTemp.Data()));
  }

  for(int j=0; j<nSystTotal; j++){
    for(int ic=0; ic<nPlotCategories; ic++) histo_Syst[j][ic] = new TH1D(Form("histo_%s_%d",plotBaseNames[ic].Data(),j),Form("histo_%s_%d",plotBaseNames[ic].Data(),j), BinXF, minXF, maxXF);
  }
  for(int j=0; j<nSystDataCardTotal; j++){
    for(int ic=0; ic<nPlotCategories; ic++) histo_SystDataCard[j][ic] = new TH1D(Form("histo_%s_%s",plotBaseNames[ic].Data(),nameSyst[j].Data()),Form("histo_%s_%s",plotBaseNames[ic].Data(),nameSyst[j].Data()), BinXF, minXF, maxXF);
  }
  for(int j=0; j<101; j++){
    for(int ic=0; ic<nPlotCategories; ic++) histo_PDFUp  [j][ic] = new TH1D(Form("histo_%s_pdf%dUp"  ,plotBaseNames[ic].Data(),j),Form("histo_%s_pdf%dUp"  ,plotBaseNames[ic].Data(),j), BinXF, minXF, maxXF);
    for(int ic=0; ic<nPlotCategories; ic++) histo_PDFDown[j][ic] = new TH1D(Form("histo_%s_pdf%dDown",plotBaseNames[ic].Data(),j),Form("histo_%s_pdf%dDown",plotBaseNames[ic].Data(),j), BinXF, minXF, maxXF);
  }

  inputFile = new TFile(Form("%s/fillhisto_%s_%d_%d.root",InputDir.Data(),anaSel.Data(),year,300+fidAna*jumpValue), "read");
  for(unsigned ic=kPlotData; ic!=nPlotCategories; ic++) {
    histo_Baseline[ic] = (TH1D*)inputFile->Get(Form("histo%d", ic)); assert(histo_Baseline[ic]); histo_Baseline[ic]->SetDirectory(0);
    histo_Baseline[ic]->SetNameTitle(Form("histo_%s",plotBaseNames[ic].Data()),Form("histo_%s",plotBaseNames[ic].Data()));
  }
  delete inputFile;

  for(int j=0; j<nSystTotal; j++){
    inputFile = new TFile(Form("%s/fillhisto_%s_%d_%d.root",InputDir.Data(),anaSel.Data(),year,300+fidAna*jumpValue+1+j), "read");
    for(unsigned ic=kPlotData; ic!=nPlotCategories; ic++) {
      histo_Syst[j][ic] = (TH1D*)inputFile->Get(Form("histo%d", ic)); assert(histo_Syst[j][ic]); histo_Syst[j][ic]->SetDirectory(0);
      histo_Syst[j][ic]->SetNameTitle(Form("histo_%s_%s",plotBaseNames[ic].Data(),nameSyst[j].Data()),Form("histo_%s_%s",plotBaseNames[ic].Data(),nameSyst[j].Data()));
    }
    delete inputFile;
  }

  for(unsigned ic=0; ic<nPlotCategories; ic++) {
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    for(int nb=1; nb<=histo_Baseline[ic]->GetNbinsX(); nb++){
      histo_Baseline[ic]->SetBinContent(nb, TMath::Max((float)histo_Baseline[ic]->GetBinContent(nb),0.0f));

      // compute QCD scale uncertainties bin-by-bin
      double diffQCDScale[6] = {
       TMath::Abs(histo_Syst[4][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[5][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[6][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[7][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[8][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[9][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb))};

      double systQCDScale = diffQCDScale[0];
      for(int nqcd=1; nqcd<6; nqcd++) {
        if(diffQCDScale[nqcd] > systQCDScale) systQCDScale = diffQCDScale[nqcd];
      }

      if(histo_Baseline[ic]->GetBinContent(nb) > 0) 
        systQCDScale = 1.0+systQCDScale/histo_Baseline[ic]->GetBinContent(nb);
      else systQCDScale = 1;

      histo_QCDScaleUp  [ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)*systQCDScale);
      histo_QCDScaleDown[ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)/systQCDScale);

      // compute PS uncertainties bin-by-bin
      double diffPS[4] = {
       TMath::Abs(histo_Syst[0][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[1][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[2][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb)),
       TMath::Abs(histo_Syst[3][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb))};

      double systPS = diffPS[0];
      for(int nps=1; nps<4; nps++) {
        if(diffPS[nps] > systPS) systPS = diffPS[nps];
      }

      if(histo_Baseline[ic]->GetBinContent(nb) > 0) 
        systPS = 1.0+systPS/histo_Baseline[ic]->GetBinContent(nb);
      else systPS = 1;

      histo_PSUp  [ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)*systPS);
      histo_PSDown[ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)/systPS);

      histo_Baseline    [ic]->SetBinContent(nb, TMath::Max((float)histo_Baseline    [ic]->GetBinContent(nb),0.0f));
      histo_QCDScaleUp  [ic]->SetBinContent(nb, TMath::Max((float)histo_QCDScaleUp  [ic]->GetBinContent(nb),0.0f));
      histo_QCDScaleDown[ic]->SetBinContent(nb, TMath::Max((float)histo_QCDScaleDown[ic]->GetBinContent(nb),0.0f));
      histo_PSUp        [ic]->SetBinContent(nb, TMath::Max((float)histo_PSUp        [ic]->GetBinContent(nb),0.0f));
      histo_PSDown      [ic]->SetBinContent(nb, TMath::Max((float)histo_PSDown      [ic]->GetBinContent(nb),0.0f));
      for(int j=0; j<nSystTotal; j++) histo_Syst[j][ic]->SetBinContent(nb, TMath::Max((float)histo_Syst[j][ic]->GetBinContent(nb),0.0f));

      // compute PDF uncertainties
      if(histo_Baseline[ic]->GetBinContent(nb) > 0 && TMath::Abs(histo_Baseline[ic]->GetBinContent(nb)-histo_Syst[10][ic]->GetBinContent(nb))/histo_Baseline[ic]->GetBinContent(nb) > 0.001) printf("PDF problem %f %f %f\n", histo_Baseline[ic]->GetBinContent(nb),histo_Syst[10][ic]->GetBinContent(nb),TMath::Abs(histo_Baseline[ic]->GetBinContent(nb)-histo_Syst[10][ic]->GetBinContent(nb)));
      for(int npdf=0; npdf<100; npdf++){
        double diff = 0;
        if(histo_Baseline[ic]->GetBinContent(nb) > 0) diff = TMath::Abs(histo_Syst[npdf+11][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb))/histo_Baseline[ic]->GetBinContent(nb);
        if(diff > 0.05) printf("Large PDFUnc(%d) %s %d %f\n",npdf,plotBaseNames[ic].Data(),nb,diff);
        diff = min(diff,0.15);
        histo_PDFUp  [npdf][ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)*(1.0+diff));
        histo_PDFDown[npdf][ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)/(1.0+diff));
      }
      histo_PDFUp  [100][ic]->SetBinContent(nb, histo_Syst[111][ic]->GetBinContent(nb));
      histo_PDFDown[100][ic]->SetBinContent(nb, histo_Syst[112][ic]->GetBinContent(nb));

      // making symmetric uncertainties
      if(histo_Baseline[ic]->GetBinContent(nb) > 0) {
        for(int nuis=0; nuis<nSystTotal-endTheory; nuis++) {
          histo_SystDataCard[2*nuis][ic]->SetBinContent(nb,histo_Syst[endTheory+nuis][ic]->GetBinContent(nb));
          systValue = histo_SystDataCard[2*nuis][ic]->GetBinContent(nb) / histo_Baseline[ic]->GetBinContent(nb);
          if(systValue > 0) histo_SystDataCard[2*nuis+1][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb)/systValue);
          else {
                            histo_SystDataCard[2*nuis  ][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb));
                            histo_SystDataCard[2*nuis+1][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb));
               }
        }
        // a
        systValue = histo_SystDataCard[42][ic]->GetBinContent(nb) / histo_Baseline[ic]->GetBinContent(nb);
        if     (systValue > 0 && systValue > 1.15) systValue = 1.15;
        else if(systValue > 0 && systValue < 0.85) systValue = 0.85;
        histo_SystDataCard[42][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb)*systValue);
        systValue = histo_SystDataCard[42][ic]->GetBinContent(nb) / histo_Baseline[ic]->GetBinContent(nb);
        if(systValue > 0) histo_SystDataCard[43][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb)/systValue);
        else {
                          histo_SystDataCard[42][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb));
                          histo_SystDataCard[43][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb));
             }
        // b
        systValue = histo_SystDataCard[44][ic]->GetBinContent(nb) / histo_Baseline[ic]->GetBinContent(nb);
        if     (systValue > 0 && systValue > 1.15) systValue = 1.15;
        else if(systValue > 0 && systValue < 0.85) systValue = 0.85;
        histo_SystDataCard[44][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb)*systValue);
        systValue = histo_SystDataCard[44][ic]->GetBinContent(nb) / histo_Baseline[ic]->GetBinContent(nb);
        if(systValue > 0) histo_SystDataCard[45][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb)/systValue);
        else {
                          histo_SystDataCard[44][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb));
                          histo_SystDataCard[45][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb));
             }
        // c
        systValue = (histo_SystDataCard[102][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb))/10.0;
        histo_SystDataCard[102][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb)+systValue);
        systValue = histo_SystDataCard[102][ic]->GetBinContent(nb) / histo_Baseline[ic]->GetBinContent(nb);
        if(systValue > 0) histo_SystDataCard[103][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb)/systValue);
        else {
                          histo_SystDataCard[102][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb));
                          histo_SystDataCard[103][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb));
             }
      }
      else {
        for(int nuis=0; nuis<nSystDataCardTotal; nuis++) {
          histo_SystDataCard[nuis][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb));
        }
      }
    } // loop over bins
  } // loop over categories

  // Begin Nonprompt study
  const int nNonPromptSyst = 12;
  TString namenonPromptSyst[nSystTotal];
  namenonPromptSyst[ 0] = "CMS_SMP24001WZ_fake_m0Up";
  namenonPromptSyst[ 1] = "CMS_SMP24001WZ_fake_m1Down";
  namenonPromptSyst[ 2] = "CMS_SMP24001WZ_fake_m2Up";
  namenonPromptSyst[ 3] = "CMS_SMP24001WZ_fake_e0Up";
  namenonPromptSyst[ 4] = "CMS_SMP24001WZ_fake_e1Up";
  namenonPromptSyst[ 5] = "CMS_SMP24001WZ_fake_e2Up";
  namenonPromptSyst[ 6] = "CMS_SMP24001WZ_fake_m0Down";
  namenonPromptSyst[ 7] = "CMS_SMP24001WZ_fake_m1Up";
  namenonPromptSyst[ 8] = "CMS_SMP24001WZ_fake_m2Down";
  namenonPromptSyst[ 9] = "CMS_SMP24001WZ_fake_e0Down";
  namenonPromptSyst[10] = "CMS_SMP24001WZ_fake_e1Down";
  namenonPromptSyst[11] = "CMS_SMP24001WZ_fake_e2Down";
  const int totalNumberFakeSyst = 6;
  TH1D *histo_InputNonPromtUnc[totalNumberFakeSyst];
  TH1D *histo_NonPromtUnc[nNonPromptSyst];
  if(anaSel.Contains("wzAnalysis")){
    inputFile = new TFile(Form("%s/fillhisto_%s_%d_nonprompt.root",InputDir.Data(),anaSel.Data(),year), "read");
    int startH = 0; if(fidAna == 1) startH = totalNumberFakeSyst;
    for(int j=0; j<totalNumberFakeSyst; j++){
      histo_InputNonPromtUnc[j] = (TH1D*)inputFile->Get(Form("histoNonPrompt_%d", j+startH));
      histo_NonPromtUnc[j+                  0] = (TH1D*)histo_InputNonPromtUnc[j]->Clone(Form("histo_%s_%s", plotBaseNames[kPlotNonPrompt].Data(), namenonPromptSyst[j+                  0].Data())); histo_NonPromtUnc[j+		    0]->SetDirectory(0);
      histo_NonPromtUnc[j+totalNumberFakeSyst] = (TH1D*)histo_InputNonPromtUnc[j]->Clone(Form("histo_%s_%s", plotBaseNames[kPlotNonPrompt].Data(), namenonPromptSyst[j+totalNumberFakeSyst].Data())); histo_NonPromtUnc[j+totalNumberFakeSyst]->SetDirectory(0);
    }
    delete inputFile;

    for(int j=0; j<totalNumberFakeSyst; j++){
      for(int nb=1; nb<=histo_Baseline[kPlotNonPrompt]->GetNbinsX(); nb++){
        if(histo_Baseline[kPlotNonPrompt]->GetBinContent(nb) > 0) {
          systValue = histo_NonPromtUnc[j+0]->GetBinContent(nb) / histo_Baseline[kPlotNonPrompt]->GetBinContent(nb);
          if     (systValue > 1.15) systValue = 1.15;
          else if(systValue < 0.85) systValue = 0.85;
          histo_NonPromtUnc[j+0]->SetBinContent(nb,histo_Baseline[kPlotNonPrompt]->GetBinContent(nb)*systValue);
          printf("fake(%d,%d) = %.3f\n",j,nb,systValue);
          if(systValue > 0) histo_NonPromtUnc[j+totalNumberFakeSyst]->SetBinContent(nb,histo_Baseline[kPlotNonPrompt]->GetBinContent(nb)/systValue);
        }
      }
    }
  }
  // End Nonprompt study

  TString additionalSuffix = "";
  if(whichAna != 0){ 
    additionalSuffix = "_alt";
  }

  TString outputLimits = Form("datacard_%s_%d_bin%d%s.root",anaSel.Data(),year,fidAna,additionalSuffix.Data());
  outputFile = new TFile(outputLimits, "RECREATE");
  outputFile->cd();
  for(unsigned ic=kPlotData; ic!=nPlotCategories; ic++) {
    if(histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    histo_Baseline[ic]->Write();
    for(int j=0; j<nSystDataCardTotal; j++) histo_SystDataCard[j][ic]->Write();

    histo_QCDScaleUp  [ic]->Write();
    histo_QCDScaleDown[ic]->Write();
    histo_PSUp        [ic]->Write();
    histo_PSDown      [ic]->Write();
    for(int npdf=0; npdf<101; npdf++){
      histo_PDFUp  [npdf][ic]->Write();
      histo_PDFDown[npdf][ic]->Write();
    }
  }
  if(anaSel.Contains("wzAnalysis")) for(int j=0; j<nNonPromptSyst; j++) histo_NonPromtUnc[j]->Write();
  outputFile->Close();

  // Filling datacards txt file
  char outputLimitsCard[200];
  sprintf(outputLimitsCard,"datacard_%s_%d_bin%d%s.txt",anaSel.Data(),year,fidAna,additionalSuffix.Data());
  ofstream newcardShape;
  newcardShape.open(outputLimitsCard);
  newcardShape << Form("imax * number of channels\n");
  newcardShape << Form("jmax * number of background minus 1\n");
  newcardShape << Form("kmax * number of nuisance parameters\n");

  newcardShape << Form("shapes    *   *   %s  histo_$PROCESS histo_$PROCESS_$SYSTEMATIC\n",outputLimits.Data());
  newcardShape << Form("shapes data_obs * %s  histo_Data\n",outputLimits.Data());

  newcardShape << Form("Observation %f\n",histo_Baseline[kPlotData]->GetSumOfWeights());

  newcardShape << Form("bin   ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    newcardShape << Form("ch%d ",fidAna);

  }
  newcardShape << Form("\n");

  newcardShape << Form("process  ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    newcardShape << Form("%s  ", plotBaseNames[ic].Data());
  }
  newcardShape << Form("\n");

  newcardShape << Form("process  ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if     (ic != kPlotWZ &&
            ic != kPlotZZ
           ) newcardShape << Form("%d  ", ic);
    else if(ic == kPlotWZ) newcardShape << Form("%d  ", -9);
    else if(ic == kPlotZZ) newcardShape << Form("%d  ", -10);
  }
  newcardShape << Form("\n");

  newcardShape << Form("rate  ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    newcardShape << Form("%f  ", histo_Baseline[ic]->GetSumOfWeights());
  }
  newcardShape << Form("\n");

  if(anaSel.Contains("wzAnalysis")){
    bool isTraditionalSyst = false;
    if(isTraditionalSyst == true){
      newcardShape << Form("CMS_SMP24001WZ_fake_m      lnN ");
      for (int ic=0; ic<nPlotCategories; ic++){
        if(!histo_Baseline[ic]) continue;
        if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
        if(ic == kPlotNonPrompt) newcardShape << Form("%6.3f ",1.15);
        else                     newcardShape << Form("- "); 
      }
      newcardShape << Form("\n");

      newcardShape << Form("CMS_SMP24001WZ_fake_e lnN ");
      for (int ic=0; ic<nPlotCategories; ic++){
        if(!histo_Baseline[ic]) continue;
        if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
        if(ic == kPlotNonPrompt) newcardShape << Form("%6.3f ",1.15);
        else                     newcardShape << Form("- ");
      }
      newcardShape << Form("\n");
    } // isTraditionalSyst == true
    else {
      newcardShape << Form("CMS_SMP24001WZ_fake_m0 shape ");
      for (int ic=0; ic<nPlotCategories; ic++){
        if(!histo_Baseline[ic]) continue;
        if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
        if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
        else                     newcardShape << Form("- "); 
      }
      newcardShape << Form("\n");

      newcardShape << Form("CMS_SMP24001WZ_fake_m1 shape ");
      for (int ic=0; ic<nPlotCategories; ic++){
        if(!histo_Baseline[ic]) continue;
        if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
        if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
        else                     newcardShape << Form("- "); 
      }
      newcardShape << Form("\n");

      newcardShape << Form("CMS_SMP24001WZ_fake_m2 shape ");
      for (int ic=0; ic<nPlotCategories; ic++){
        if(!histo_Baseline[ic]) continue;
        if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
        if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
        else                     newcardShape << Form("- "); 
      }
      newcardShape << Form("\n");

      newcardShape << Form("CMS_SMP24001WZ_fake_e0 shape ");
      for (int ic=0; ic<nPlotCategories; ic++){
        if(!histo_Baseline[ic]) continue;
        if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
        if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
        else                     newcardShape << Form("- "); 
      }
      newcardShape << Form("\n");

      newcardShape << Form("CMS_SMP24001WZ_fake_e1 shape ");
      for (int ic=0; ic<nPlotCategories; ic++){
        if(!histo_Baseline[ic]) continue;
        if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
        if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
        else                     newcardShape << Form("- "); 
      }
      newcardShape << Form("\n");

      newcardShape << Form("CMS_SMP24001WZ_fake_e2 shape ");
      for (int ic=0; ic<nPlotCategories; ic++){
        if(!histo_Baseline[ic]) continue;
        if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
        if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
        else                     newcardShape << Form("- "); 
      }
      newcardShape << Form("\n");
    } // isTraditionalSyst == false
  }

  for(int nl=0; nl<4; nl++){
    if(lumiU[nl] == 1) continue;
    newcardShape << Form("lumi_13p6TeV_%d lnN ", nl);
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("- ");
      else                     newcardShape << Form("%6.3f ",lumiU[nl]);
    }
    newcardShape << Form("\n");
  }

  newcardShape << Form("CMS_SMP25013_trigger_%s   lnN     ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("%6.3f ",triggerEffUnc);
  }
  newcardShape << Form("\n");

  // BTagging uncertainties
  for(int n_unc=0; n_unc<numberBTagSyst; n_unc++){
    newcardShape << Form("%s shape ",BtagSFNames[n_unc].Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("- ");
      else                     newcardShape << Form("1.0 ");
    }
    newcardShape << Form("\n");
  }

  newcardShape << Form("CMS_eff_m_reco_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_eff_m_id_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_eff_m_iso_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_eff_e_reco_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");
 
  newcardShape << Form("CMS_eff_e_id shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_SMP25013_eff_m_tightid_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_SMP25013_eff_e_tightid_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("pileup_13p6TeV shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");
 
  // JES uncertainties --> starting at 1, 0 == total (not used)
  for(int n_unc=1; n_unc<numberJESSyst; n_unc++){
    newcardShape << Form("CMS_scale_j_%s shape ",jesNames[n_unc].Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if     (ic == kPlotNonPrompt) newcardShape << Form("- ");
      else                          newcardShape << Form("1.0 ");
    }
    newcardShape << Form("\n");
  }

  newcardShape << Form("CMS_res_j_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");
 
  newcardShape << Form("CMS_scale_m_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");
 
  newcardShape << Form("CMS_scale_e_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  //newcardShape << Form("CMS_scale_met_jer_%s shape ",theTagYear.Data());
  //for (int ic=0; ic<nPlotCategories; ic++){
  //  if(!histo_Baseline[ic]) continue;
  //  if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
  //  if(ic == kPlotNonPrompt) newcardShape << Form("- ");
  //  else		     newcardShape << Form("1.0 ");
  //}
  //newcardShape << Form("\n");

  //newcardShape << Form("CMS_scale_met_jes_%s shape ",theTagYear.Data());
  //for (int ic=0; ic<nPlotCategories; ic++){
  //  if(!histo_Baseline[ic]) continue;
  //  if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
  //  if(ic == kPlotNonPrompt) newcardShape << Form("- ");
  //  else		     newcardShape << Form("1.0 ");
  //}
  //newcardShape << Form("\n");

  newcardShape << Form("CMS_scale_met_unclustered_energy_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else		     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  for(unsigned ic=0; ic<nPlotCategories; ic++) {
    if(ic== kPlotData || ic == kPlotNonPrompt || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    newcardShape << Form("QCD_scale_%s_ACCEPT shape ",plotBaseNames[ic].Data());
    for(unsigned ic2=0; ic2<nPlotCategories; ic2++) {
      if(ic2 == kPlotData || histo_Baseline[ic2]->GetSumOfWeights() <= 0) continue;
      if(ic==ic2) newcardShape << Form("1.0  ");
      else        newcardShape << Form("-  ");
      }
      newcardShape << Form("\n");
  } 

  for(unsigned ic=0; ic<nPlotCategories; ic++) {
    if(ic== kPlotData || ic == kPlotNonPrompt || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    newcardShape << Form("PS_%s_ACCEPT shape ",plotBaseNames[ic].Data());
    for(unsigned ic2=0; ic2<nPlotCategories; ic2++) {
      if(ic2 == kPlotData || histo_Baseline[ic2]->GetSumOfWeights() <= 0) continue;
      if(ic==ic2) newcardShape << Form("1.0  ");
      else        newcardShape << Form("-  ");
      }
      newcardShape << Form("\n");
  } 

  for(int npdf=100; npdf<=100; npdf++){
    newcardShape << Form("pdf%d shape ",npdf);
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("- ");
      else                     newcardShape << Form("1.0 ");
    }
    newcardShape << Form("\n");
  }

  newcardShape << Form("pdfqq   lnN     ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("%6.3f ",1.01);
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_ww_wznorm  rateParam * %s 1 [0.1,4.9]\n",plotBaseNames[kPlotWZ].Data());
  newcardShape << Form("CMS_ww_zznorm  rateParam * %s 1 [0.1,4.9]\n",plotBaseNames[kPlotZZ].Data());

  newcardShape << Form("ch%d autoMCStats 0\n",fidAna);

  newcardShape.close();

}
