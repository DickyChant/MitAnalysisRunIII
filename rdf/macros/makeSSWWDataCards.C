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
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>
#include "TLorentzVector.h"
#include "TColor.h"

#include "../makePlots/common.h"

namespace {
TFile* openCheckedFile(const TString& path, const char* mode = "READ") {
  TFile* f = TFile::Open(path, mode);
  if (!f || f->IsZombie()) {
    if (f) { f->Close(); delete f; }
    throw std::runtime_error(std::string("Cannot open ROOT file: ") + path.Data());
  }
  return f;
}
TH1D* getCheckedHistogram(TFile* f, const TString& name, const TString& fileName) {
  TH1D* h = dynamic_cast<TH1D*>(f->Get(name));
  if (!h) throw std::runtime_error(std::string("Missing/non-TH1D histogram ") + name.Data() + " in " + fileName.Data());
  h->SetDirectory(nullptr);
  return h;
}
void checkSameBinning(const TH1D* a, const TH1D* b, const TString& what) {
  if (!a || !b || a->GetNbinsX() != b->GetNbinsX())
    throw std::runtime_error(std::string("Incompatible bin count: ") + what.Data());
  for (int i=1; i<=a->GetNbinsX()+1; ++i) {
    const double x=a->GetXaxis()->GetBinLowEdge(i), y=b->GetXaxis()->GetBinLowEdge(i);
    if (std::fabs(x-y) > 1.e-9*std::max(1.0,std::fabs(x)))
      throw std::runtime_error(std::string("Incompatible bin edges: ") + what.Data());
  }
}
TH1D* cloneDetached(const TH1D* source, const TString& name) {
  if (!source) throw std::runtime_error(std::string("Cannot clone null histogram: ") + name.Data());
  TH1D* clone = dynamic_cast<TH1D*>(source->Clone(name));
  if (!clone) throw std::runtime_error(std::string("Failed to clone histogram: ") + name.Data());
  clone->SetDirectory(nullptr);
  return clone;
}
void scaleToIntegral(TH1D* h, double target, const TString& what) {
  if (!h) throw std::runtime_error(std::string("Null histogram: ") + what.Data());
  const double sum=h->GetSumOfWeights();
  if (!std::isfinite(sum) || std::fabs(sum)<1.e-12)
    throw std::runtime_error(std::string("Zero/non-finite normalization integral: ") + what.Data());
  h->Scale(target/sum);
}
}

// whichAna = 0 (SSWW), fidAna = 0/2/4 (WW), 1/3/5 (WWb)
// whichAna = 0 (WZ), fidAna = 0 (WZ), 1 (WZb)

void makeSSWWDataCards(int whichAna = 0, int fidAna = 0, TString InputDir = "anaZ", TString anaSel = "sswwAnalysis1001", int year = 20220, bool applyPostFitSF = false){

  if (fidAna < 0 || fidAna > 6) { std::cerr << "ERROR: invalid fidAna=" << fidAna << std::endl; return; }
  if (InputDir.IsNull() || anaSel.IsNull()) { std::cerr << "ERROR: InputDir/anaSel cannot be empty." << std::endl; return; }

  int isTypeFakeSyst = 2;
  plotBaseNames[kPlotNonPrompt] = "NonPrompt";
  if     (anaSel.Contains("wzAnalysis")) {plotBaseNames[kPlotNonPrompt] = "NonWZPrompt";}
  else if(anaSel.Contains("zzAnalysis")) {plotBaseNames[kPlotNonPrompt] = "NonZZPrompt"; isTypeFakeSyst = 0;}

  if(anaSel.Contains("wzAnalysis") || anaSel.Contains("sswwAnalysis")) {
    TString chargeString = "";
    if     (anaSel.Contains("021")) chargeString = "P";
    else if(anaSel.Contains("022")) chargeString = "M";

    plotBaseNames[kPlotEWKSSWW]   = plotBaseNames[kPlotEWKSSWW]   + chargeString.Data();
    plotBaseNames[kPlotQCDSSWW]   = plotBaseNames[kPlotQCDSSWW]   + chargeString.Data();
    plotBaseNames[kPlotEWKWZ]     = plotBaseNames[kPlotEWKWZ]     + chargeString.Data();
    plotBaseNames[kPlotWZ]        = plotBaseNames[kPlotWZ]        + chargeString.Data();
    plotBaseNames[kPlotTVX]       = plotBaseNames[kPlotTVX]       + chargeString.Data();
    plotBaseNames[kPlotNonPrompt] = plotBaseNames[kPlotNonPrompt] + chargeString.Data();
  }

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
  int startHistogram = 0;
  TString postFixFile = "_mva";
  TString postFixHist = "MVA";
  if     (anaSel.Contains("wzAnalysis")) {startHistogram = 300; postFixFile = ""; postFixHist = "";}
  else if(anaSel.Contains("zzAnalysis")) {startHistogram = 300; postFixFile = ""; postFixHist = "";}

  bool isTheorySignal[nPlotCategories];
  double maxTheoryUnc[nPlotCategories];
  double postFitSF[nPlotCategories];
  for (int ic=0; ic<nPlotCategories; ic++){
    if(ic == kPlotEWKSSWW ||
       ic == kPlotSignal0 ||
       ic == kPlotSignal1 ||
       ic == kPlotSignal2 ||
       ic == kPlotSignal3 ||
       ic == kPlotSignal4 ||
       ic == kPlotSignal5 ||
       ic == kPlotWZ ||
       ic == kPlotEWKWZ ||
       ic == kPlotZZ ||
       ic == kPlotTVX) {
      isTheorySignal[ic] = true;
      maxTheoryUnc[ic] = 1.0;
    } else {
      isTheorySignal[ic] = false;
      maxTheoryUnc[ic] = 0.20;
    }
    postFitSF[ic] = 1.0; // default
  }

  // Begin scale expectations to observations (step 1)
  if(applyPostFitSF == true){
    if     (anaSel.Contains("sswwAnalysis1001") || anaSel.Contains("sswwAnalysis1006")) {
      postFitSF[kPlotSignal0] = 1.000;
      postFitSF[kPlotSignal1] = 1.000;
      postFitSF[kPlotSignal2] = 1.000;
      postFitSF[kPlotSignal3] = 1.000;
      postFitSF[kPlotSignal4] = 1.000;
      postFitSF[kPlotSignal5] = 1.000;
    }
    else if(anaSel.Contains("sswwAnalysis1002") || anaSel.Contains("sswwAnalysis1007")) {
      postFitSF[kPlotSignal0] = 1.000;
      postFitSF[kPlotSignal1] = 1.000;
      postFitSF[kPlotSignal2] = 1.000;
      postFitSF[kPlotSignal3] = 1.000;
      postFitSF[kPlotSignal4] = 1.000;
      postFitSF[kPlotSignal5] = 1.000;
    }
    else if(anaSel.Contains("sswwAnalysis1003") || anaSel.Contains("sswwAnalysis1008")) {
      postFitSF[kPlotSignal0] = 1.000;
      postFitSF[kPlotSignal1] = 1.000;
      postFitSF[kPlotSignal2] = 1.000;
      postFitSF[kPlotSignal3] = 1.000;
      postFitSF[kPlotSignal4] = 1.000;
      postFitSF[kPlotSignal5] = 1.000;
    }
    else if(anaSel.Contains("sswwAnalysis1004") || anaSel.Contains("sswwAnalysis1009")) {
      postFitSF[kPlotSignal0] = 1.000;
      postFitSF[kPlotSignal1] = 1.000;
      postFitSF[kPlotSignal2] = 1.000;
      postFitSF[kPlotSignal3] = 1.000;
      postFitSF[kPlotSignal4] = 1.000;
      postFitSF[kPlotSignal5] = 1.000;
    }
    else if(anaSel.Contains("sswwAnalysis1005") || anaSel.Contains("sswwAnalysis1010")) {
      postFitSF[kPlotSignal0] = 1.000;
      postFitSF[kPlotSignal1] = 1.000;
      postFitSF[kPlotSignal2] = 1.000;
      postFitSF[kPlotSignal3] = 1.000;
      postFitSF[kPlotSignal4] = 1.000;
      postFitSF[kPlotSignal5] = 1.000;
    }
  }
  // End scale expectations to observations (step 1)

  double systValue;
  TFile *inputFile;
  TFile *outputFile;
  const int endTheory = 113;
  const int nSystTotal = 169;
  const int nSystDataCardTotal = 112; // (nSystTotal-endTheory)*2 = nSystDataCardTotal

  TH1D *histo_Baseline[nPlotCategories];
  TH1D *histo_QCDScaleUp[nPlotCategories];
  TH1D *histo_QCDScaleDown[nPlotCategories];
  TH1D *histo_PSUp[nPlotCategories];
  TH1D *histo_PSDown[nPlotCategories];

  TH1D *histo_Syst[nSystTotal][nPlotCategories];
  TH1D *histo_SystDataCard[nSystDataCardTotal][nPlotCategories];
  TH1D *histo_PDFUp  [101][nPlotCategories];
  TH1D *histo_PDFDown[101][nPlotCategories];
  // Initialize every pointer so optional categories/systematics can be safely
  // skipped and all owned histograms can be released at the end.
  for (int ic=0; ic<nPlotCategories; ++ic) {
    histo_Baseline[ic]=nullptr; histo_QCDScaleUp[ic]=nullptr; histo_QCDScaleDown[ic]=nullptr;
    histo_PSUp[ic]=nullptr; histo_PSDown[ic]=nullptr;
    for (int j=0; j<nSystTotal; ++j) histo_Syst[j][ic]=nullptr;
    for (int j=0; j<nSystDataCardTotal; ++j) histo_SystDataCard[j][ic]=nullptr;
    for (int j=0; j<101; ++j) { histo_PDFUp[j][ic]=nullptr; histo_PDFDown[j][ic]=nullptr; }
  }

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
  nameSyst[12 ] = Form("CMS_SMP26030_WWtrigger_%sUp",theTagYear.Data());
  nameSyst[13 ] = Form("CMS_SMP26030_WWtrigger_%sDown",theTagYear.Data());
  nameSyst[14 ] = Form("CMS_SMP26030_eff_m_tightid_%sUp",theTagYear.Data());
  nameSyst[15 ] = Form("CMS_SMP26030_eff_m_tightid_%sDown",theTagYear.Data());
  nameSyst[16 ] = Form("CMS_SMP26030_eff_e_tightid_%sUp",theTagYear.Data());
  nameSyst[17 ] = Form("CMS_SMP26030_eff_e_tightid_%sDown",theTagYear.Data());
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
  nameSyst[42 ] = "ewkCorrUp";
  nameSyst[43 ] = "ewkCorrDown";
  nameSyst[44 ] = Form("CMS_scale_m_%sUp",theTagYear.Data());
  nameSyst[45 ] = Form("CMS_scale_m_%sDown",theTagYear.Data());
  nameSyst[46 ] = Form("CMS_scale_e_%sUp",theTagYear.Data());
  nameSyst[47 ] = Form("CMS_scale_e_%sDown",theTagYear.Data());
  nameSyst[48 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 0].Data());
  nameSyst[49 ] = Form("CMS_scale_j_%sDown",jesNames[ 0].Data());
  nameSyst[50 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 1].Data());
  nameSyst[51 ] = Form("CMS_scale_j_%sDown",jesNames[ 1].Data());
  nameSyst[52 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 2].Data());
  nameSyst[53 ] = Form("CMS_scale_j_%sDown",jesNames[ 2].Data());
  nameSyst[54 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 3].Data());
  nameSyst[55 ] = Form("CMS_scale_j_%sDown",jesNames[ 3].Data());
  nameSyst[56 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 4].Data());
  nameSyst[57 ] = Form("CMS_scale_j_%sDown",jesNames[ 4].Data());
  nameSyst[58 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 5].Data());
  nameSyst[59 ] = Form("CMS_scale_j_%sDown",jesNames[ 5].Data());
  nameSyst[60 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 6].Data());
  nameSyst[61 ] = Form("CMS_scale_j_%sDown",jesNames[ 6].Data());
  nameSyst[62 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 7].Data());
  nameSyst[63 ] = Form("CMS_scale_j_%sDown",jesNames[ 7].Data());
  nameSyst[64 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 8].Data());
  nameSyst[65 ] = Form("CMS_scale_j_%sDown",jesNames[ 8].Data());
  nameSyst[66 ] = Form("CMS_scale_j_%sUp"  ,jesNames[ 9].Data());
  nameSyst[67 ] = Form("CMS_scale_j_%sDown",jesNames[ 9].Data());
  nameSyst[68 ] = Form("CMS_scale_j_%sUp"  ,jesNames[10].Data());
  nameSyst[69 ] = Form("CMS_scale_j_%sDown",jesNames[10].Data());
  nameSyst[70 ] = Form("CMS_scale_j_%sUp"  ,jesNames[11].Data());
  nameSyst[71 ] = Form("CMS_scale_j_%sDown",jesNames[11].Data());
  nameSyst[72 ] = Form("CMS_scale_j_%sUp"  ,jesNames[12].Data());
  nameSyst[73 ] = Form("CMS_scale_j_%sDown",jesNames[12].Data());
  nameSyst[74 ] = Form("CMS_scale_j_%sUp"  ,jesNames[13].Data());
  nameSyst[75 ] = Form("CMS_scale_j_%sDown",jesNames[13].Data());
  nameSyst[76 ] = Form("CMS_scale_j_%sUp"  ,jesNames[14].Data());
  nameSyst[77 ] = Form("CMS_scale_j_%sDown",jesNames[14].Data());
  nameSyst[78 ] = Form("CMS_scale_j_%sUp"  ,jesNames[15].Data());
  nameSyst[79 ] = Form("CMS_scale_j_%sDown",jesNames[15].Data());
  nameSyst[80 ] = Form("CMS_scale_j_%sUp"  ,jesNames[16].Data());
  nameSyst[81 ] = Form("CMS_scale_j_%sDown",jesNames[16].Data());
  nameSyst[82 ] = Form("CMS_scale_j_%sUp"  ,jesNames[17].Data());
  nameSyst[83 ] = Form("CMS_scale_j_%sDown",jesNames[17].Data());
  nameSyst[84 ] = Form("CMS_scale_j_%sUp"  ,jesNames[18].Data());
  nameSyst[85 ] = Form("CMS_scale_j_%sDown",jesNames[18].Data());
  nameSyst[86 ] = Form("CMS_scale_j_%sUp"  ,jesNames[19].Data());
  nameSyst[87 ] = Form("CMS_scale_j_%sDown",jesNames[19].Data());
  nameSyst[88 ] = Form("CMS_scale_j_%sUp"  ,jesNames[20].Data());
  nameSyst[89 ] = Form("CMS_scale_j_%sDown",jesNames[20].Data());
  nameSyst[90 ] = Form("CMS_scale_j_%sUp"  ,jesNames[21].Data());
  nameSyst[91 ] = Form("CMS_scale_j_%sDown",jesNames[21].Data());
  nameSyst[92 ] = Form("CMS_scale_j_%sUp"  ,jesNames[22].Data());
  nameSyst[93 ] = Form("CMS_scale_j_%sDown",jesNames[22].Data());
  nameSyst[94 ] = Form("CMS_scale_j_%sUp"  ,jesNames[23].Data());
  nameSyst[95 ] = Form("CMS_scale_j_%sDown",jesNames[23].Data());
  nameSyst[96 ] = Form("CMS_scale_j_%sUp"  ,jesNames[24].Data());
  nameSyst[97 ] = Form("CMS_scale_j_%sDown",jesNames[24].Data());
  nameSyst[98 ] = Form("CMS_scale_j_%sUp"  ,jesNames[25].Data());
  nameSyst[99 ] = Form("CMS_scale_j_%sDown",jesNames[25].Data());
  nameSyst[100] = Form("CMS_scale_j_%sUp"  ,jesNames[26].Data());
  nameSyst[101] = Form("CMS_scale_j_%sDown",jesNames[26].Data());
  nameSyst[102] = Form("CMS_scale_j_%sUp"  ,jesNames[27].Data());
  nameSyst[103] = Form("CMS_scale_j_%sDown",jesNames[27].Data());
  nameSyst[104] = Form("CMS_res_j_%sUp",theTagYear.Data());
  nameSyst[105] = Form("CMS_res_j_%sDown",theTagYear.Data());
  nameSyst[106] = Form("CMS_scale_met_jer_%sUp",theTagYear.Data());
  nameSyst[107] = Form("CMS_scale_met_jer_%sDown",theTagYear.Data());
  nameSyst[108] = Form("CMS_scale_met_jes_%sUp",theTagYear.Data());
  nameSyst[109] = Form("CMS_scale_met_jes_%sDown",theTagYear.Data());
  nameSyst[110] = Form("CMS_scale_met_unclustered_energy_%sUp",theTagYear.Data());
  nameSyst[111] = Form("CMS_scale_met_unclustered_energy_%sDown",theTagYear.Data());

  TString nameFakeSyst = "random";
  if     (anaSel.Contains("sswwAnalysis")) {
    nameFakeSyst = "ssww";
  }
  else if(anaSel.Contains("wzAnalysis")) {
    nameFakeSyst = "wz";
  }
  else if(anaSel.Contains("zzAnalysis")) {
    nameFakeSyst = "zz";
  }
  else {
    printf("Wrong option\n");
    return;
  }

  const TString baselineFileName = Form("%s/fillhisto_%s_%d_%d%s.root",InputDir.Data(),anaSel.Data(),year,startHistogram+fidAna*jumpValue,postFixFile.Data());
  inputFile = openCheckedFile(baselineFileName);
  for (int ic=kPlotData; ic<nPlotCategories; ++ic) {
    histo_Baseline[ic] = getCheckedHistogram(inputFile, Form("histo%s%d",postFixHist.Data(),ic), baselineFileName);
    histo_Baseline[ic]->SetNameTitle(Form("histo_%s",plotBaseNames[ic].Data()),Form("histo_%s",plotBaseNames[ic].Data()));
  }
  inputFile->Close(); delete inputFile; inputFile=nullptr;

  for(int ic=0; ic<nPlotCategories; ic++) {
    TString plotBaseNamesTemp =  plotBaseNames[ic];
    if     (ic == kPlotSignal0 || ic == kPlotSignal1 || ic == kPlotSignal2 || ic == kPlotSignal3 || ic == kPlotSignal4 || ic == kPlotSignal5 || ic == kPlotEWKSSWW) plotBaseNamesTemp = "EWKSSWW";
    histo_QCDScaleUp  [ic] = cloneDetached(histo_Baseline[ic],Form("histo_%s_QCD_scale_%s_ACCEPTUp"  , plotBaseNames[ic].Data(), plotBaseNamesTemp.Data()));
    histo_QCDScaleDown[ic] = cloneDetached(histo_Baseline[ic],Form("histo_%s_QCD_scale_%s_ACCEPTDown", plotBaseNames[ic].Data(), plotBaseNamesTemp.Data()));
    histo_PSUp  [ic]       = cloneDetached(histo_Baseline[ic],Form("histo_%s_PS_%s_ACCEPTUp"  , plotBaseNames[ic].Data(), plotBaseNamesTemp.Data()));
    histo_PSDown[ic]       = cloneDetached(histo_Baseline[ic],Form("histo_%s_PS_%s_ACCEPTDown", plotBaseNames[ic].Data(), plotBaseNamesTemp.Data()));
  }

  for(int j=0; j<nSystDataCardTotal; j++){
    for(int ic=0; ic<nPlotCategories; ic++) {
      if(
        (ic == kPlotEWKSSWW ||
         ic == kPlotSignal0 ||
         ic == kPlotSignal1 ||
         ic == kPlotSignal2 ||
         ic == kPlotSignal3 ||
         ic == kPlotSignal4 ||
         ic == kPlotSignal5) &&
         nameSyst[j].Contains("ewkCorr")) {
        histo_SystDataCard[j][ic] = cloneDetached(histo_Baseline[ic],Form("histo_%s_WW%s",plotBaseNames[ic].Data(),nameSyst[j].Data()));
      }
      else if(
        (ic == kPlotEWKWZ) &&
         nameSyst[j].Contains("ewkCorr")) {
        histo_SystDataCard[j][ic] = cloneDetached(histo_Baseline[ic],Form("histo_%s_WZ%s",plotBaseNames[ic].Data(),nameSyst[j].Data()));
      }
      else {
        histo_SystDataCard[j][ic] = cloneDetached(histo_Baseline[ic],Form("histo_%s_%s",plotBaseNames[ic].Data(),nameSyst[j].Data()));
      }
    }
  }
  for(int j=0; j<101; j++){
    for(int ic=0; ic<nPlotCategories; ic++) histo_PDFUp  [j][ic] = cloneDetached(histo_Baseline[ic],Form("histo_%s_pdf%dUp"  ,plotBaseNames[ic].Data(),j));
    for(int ic=0; ic<nPlotCategories; ic++) histo_PDFDown[j][ic] = cloneDetached(histo_Baseline[ic],Form("histo_%s_pdf%dDown",plotBaseNames[ic].Data(),j));
  }

  for(int j=0; j<nSystTotal; j++){
    const TString systFileName = Form("%s/fillhisto_%s_%d_%d%s.root",InputDir.Data(),anaSel.Data(),year,startHistogram+fidAna*jumpValue+1+j,postFixFile.Data());
    inputFile = openCheckedFile(systFileName);
    for(int ic=kPlotData; ic<nPlotCategories; ic++) {
      histo_Syst[j][ic] = getCheckedHistogram(inputFile,Form("histo%s%d",postFixHist.Data(),ic),systFileName);
      checkSameBinning(histo_Baseline[ic],histo_Syst[j][ic],Form("systematic %d/category %d",j,ic));
    }
    inputFile->Close(); delete inputFile; inputFile=nullptr;
  }

  for(unsigned ic=0; ic<nPlotCategories; ic++) {
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    for(int nb=1; nb<=histo_Baseline[ic]->GetNbinsX(); nb++){
      histo_Baseline[ic]->SetBinContent(nb, TMath::Max((float)histo_Baseline[ic]->GetBinContent(nb),0.000001f));
      // Allow for maximum 50% stat. unc.
      if(histo_Baseline[ic]->GetBinError(nb)/histo_Baseline[ic]->GetBinContent(nb) > 0.5) histo_Baseline[ic]->SetBinError(nb,0.5*histo_Baseline[ic]->GetBinContent(nb));

      for(int j=0; j<nSystTotal; j++) histo_Syst[j][ic]->SetBinContent(nb, TMath::Max((float)histo_Syst[j][ic]->GetBinContent(nb),0.000001f));

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
        systQCDScale = 1.0+TMath::Min(systQCDScale/histo_Baseline[ic]->GetBinContent(nb),maxTheoryUnc[ic]);
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
        systPS = 1.0+TMath::Min(systPS/histo_Baseline[ic]->GetBinContent(nb),maxTheoryUnc[ic]);
      else systPS = 1;

      histo_PSUp  [ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)*systPS);
      histo_PSDown[ic]->SetBinContent(nb, histo_Baseline[ic]->GetBinContent(nb)/systPS);

      histo_Baseline    [ic]->SetBinContent(nb, TMath::Max((float)histo_Baseline    [ic]->GetBinContent(nb),0.000001f));
      histo_QCDScaleUp  [ic]->SetBinContent(nb, TMath::Max((float)histo_QCDScaleUp  [ic]->GetBinContent(nb),0.000001f));
      histo_QCDScaleDown[ic]->SetBinContent(nb, TMath::Max((float)histo_QCDScaleDown[ic]->GetBinContent(nb),0.000001f));
      histo_PSUp        [ic]->SetBinContent(nb, TMath::Max((float)histo_PSUp        [ic]->GetBinContent(nb),0.000001f));
      histo_PSDown      [ic]->SetBinContent(nb, TMath::Max((float)histo_PSDown      [ic]->GetBinContent(nb),0.000001f));
      for(int j=0; j<nSystTotal; j++) histo_Syst[j][ic]->SetBinContent(nb, TMath::Max((float)histo_Syst[j][ic]->GetBinContent(nb),0.000001f));

      // compute PDF uncertainties
      if(histo_Baseline[ic]->GetBinContent(nb) > 0 && TMath::Abs(histo_Baseline[ic]->GetBinContent(nb)-histo_Syst[10][ic]->GetBinContent(nb))/histo_Baseline[ic]->GetBinContent(nb) > 0.001) printf("PDF problem %f %f %f\n", histo_Baseline[ic]->GetBinContent(nb),histo_Syst[10][ic]->GetBinContent(nb),TMath::Abs(histo_Baseline[ic]->GetBinContent(nb)-histo_Syst[10][ic]->GetBinContent(nb)));
      for(int npdf=0; npdf<100; npdf++){
        double diff = 0;
        if(histo_Baseline[ic]->GetBinContent(nb) > 0) diff = TMath::Abs(histo_Syst[npdf+11][ic]->GetBinContent(nb)-histo_Baseline[ic]->GetBinContent(nb))/histo_Baseline[ic]->GetBinContent(nb);
        if(diff > 0.05) printf("Large PDFUnc(%d) %s %d %f\n",npdf,plotBaseNames[ic].Data(),nb,diff);
        diff = std::min(diff,0.15);
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
        for(int nuis=0; nuis<nSystTotal-endTheory; nuis++) {
          systValue = histo_SystDataCard[2*nuis][ic]->GetBinContent(nb) / histo_Baseline[ic]->GetBinContent(nb);
          if     (systValue > 0 && systValue > 1.45/1) systValue = 1.45/1;
          else if(systValue > 0 && systValue < 1/1.45) systValue = 1/1.45;
          histo_SystDataCard[2*nuis][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb)*systValue);
          systValue = histo_SystDataCard[2*nuis][ic]->GetBinContent(nb) / histo_Baseline[ic]->GetBinContent(nb);
          if(systValue > 0) histo_SystDataCard[2*nuis+1][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb)/systValue);
          else {
                            histo_SystDataCard[2*nuis  ][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb));
                            histo_SystDataCard[2*nuis+1][ic]->SetBinContent(nb,histo_Baseline[ic]->GetBinContent(nb));
               }
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
  TString namenonPromptSyst[nNonPromptSyst];
  namenonPromptSyst[ 0] = Form("CMS_SMP26030_fake_%s_m0Up"  ,nameFakeSyst.Data());
  namenonPromptSyst[ 1] = Form("CMS_SMP26030_fake_%s_m1Down",nameFakeSyst.Data());
  namenonPromptSyst[ 2] = Form("CMS_SMP26030_fake_%s_m2Up"  ,nameFakeSyst.Data());
  namenonPromptSyst[ 3] = Form("CMS_SMP26030_fake_%s_e0Up"  ,nameFakeSyst.Data());
  namenonPromptSyst[ 4] = Form("CMS_SMP26030_fake_%s_e1Up"  ,nameFakeSyst.Data());
  namenonPromptSyst[ 5] = Form("CMS_SMP26030_fake_%s_e2Up"  ,nameFakeSyst.Data());
  namenonPromptSyst[ 6] = Form("CMS_SMP26030_fake_%s_m0Down",nameFakeSyst.Data());
  namenonPromptSyst[ 7] = Form("CMS_SMP26030_fake_%s_m1Up"  ,nameFakeSyst.Data());
  namenonPromptSyst[ 8] = Form("CMS_SMP26030_fake_%s_m2Down",nameFakeSyst.Data());
  namenonPromptSyst[ 9] = Form("CMS_SMP26030_fake_%s_e0Down",nameFakeSyst.Data());
  namenonPromptSyst[10] = Form("CMS_SMP26030_fake_%s_e1Down",nameFakeSyst.Data());
  namenonPromptSyst[11] = Form("CMS_SMP26030_fake_%s_e2Down",nameFakeSyst.Data());
  const int totalNumberFakeSyst = 6;
  TH1D *histo_InputNonPromtUnc[totalNumberFakeSyst] = {};
  TH1D *histo_NonPromtUnc[nNonPromptSyst] = {};
  if(isTypeFakeSyst != 0){
    const TString nonPromptFileName = Form("%s/fillhisto_%s_%d_nonprompt.root",InputDir.Data(),anaSel.Data(),year);
    inputFile = openCheckedFile(nonPromptFileName);
    int startH = totalNumberFakeSyst*fidAna;
    for(int j=0; j<totalNumberFakeSyst; j++){
      histo_InputNonPromtUnc[j] = getCheckedHistogram(inputFile,Form("histoNonPrompt_%d",j+startH),nonPromptFileName);
      checkSameBinning(histo_Baseline[kPlotNonPrompt],histo_InputNonPromtUnc[j],Form("nonprompt variation %d",j));
      histo_NonPromtUnc[j+                  0] = cloneDetached(histo_InputNonPromtUnc[j],Form("histo_%s_%s", plotBaseNames[kPlotNonPrompt].Data(), namenonPromptSyst[j+                  0].Data())); histo_NonPromtUnc[j+		    0]->SetDirectory(0);
      histo_NonPromtUnc[j+totalNumberFakeSyst] = cloneDetached(histo_InputNonPromtUnc[j],Form("histo_%s_%s", plotBaseNames[kPlotNonPrompt].Data(), namenonPromptSyst[j+totalNumberFakeSyst].Data())); histo_NonPromtUnc[j+totalNumberFakeSyst]->SetDirectory(0);
    }
    inputFile->Close(); delete inputFile; inputFile=nullptr;

    for(int j=0; j<totalNumberFakeSyst; j++){
      // Making sure there are not negative events
      for(int nb=1; nb<=histo_Baseline[kPlotNonPrompt]->GetNbinsX(); nb++){
        histo_NonPromtUnc[j+                  0]->SetBinContent(nb, TMath::Max((float)histo_NonPromtUnc[j+                  0]->GetBinContent(nb),0.000001f));
        histo_NonPromtUnc[j+totalNumberFakeSyst]->SetBinContent(nb, TMath::Max((float)histo_NonPromtUnc[j+totalNumberFakeSyst]->GetBinContent(nb),0.000001f));
      }
      // Renormalizing distributions
      if(anaSel.Contains("sswwAnalysis")){
        scaleToIntegral(histo_NonPromtUnc[j+0],histo_Baseline[kPlotNonPrompt]->GetSumOfWeights(),namenonPromptSyst[j+0]);
        scaleToIntegral(histo_NonPromtUnc[j+totalNumberFakeSyst],histo_Baseline[kPlotNonPrompt]->GetSumOfWeights(),namenonPromptSyst[j+totalNumberFakeSyst]);
      }
      // Computing uncertainties
      for(int nb=1; nb<=histo_Baseline[kPlotNonPrompt]->GetNbinsX(); nb++){
        if(histo_Baseline[kPlotNonPrompt]->GetBinContent(nb) > 0) {
          systValue = histo_NonPromtUnc[j+0]->GetBinContent(nb) / histo_Baseline[kPlotNonPrompt]->GetBinContent(nb);
          if(fabs(systValue-1) > 0.40) printf("fake(%d,%d) = %.3f\n",j,nb,systValue);
          if     (systValue > 1.4/1) systValue = 1.4/1;
          else if(systValue < 1/1.4) systValue = 1/1.4;
          histo_NonPromtUnc[j+0]->SetBinContent(nb,histo_Baseline[kPlotNonPrompt]->GetBinContent(nb)*systValue);
          if(systValue > 0) histo_NonPromtUnc[j+totalNumberFakeSyst]->SetBinContent(nb,histo_Baseline[kPlotNonPrompt]->GetBinContent(nb)/systValue);
        }
      }
    }
  }
  // End Nonprompt study

  // Begin wrongsign study
  const int nwrongsignSyst = 4;
  TString namewrongsignSyst[nwrongsignSyst];
  namewrongsignSyst[ 0] = Form("CMS_SMP26030_wrongsign_stat_%sUp",theTagYear.Data());
  namewrongsignSyst[ 1] =      "CMS_SMP26030_wrongsign_methodUp";
  namewrongsignSyst[ 2] = Form("CMS_SMP26030_wrongsign_stat_%sDown",theTagYear.Data());
  namewrongsignSyst[ 3] =      "CMS_SMP26030_wrongsign_methodDown";
  const int totalNumberWSSyst = 2;
  TH1D *histo_InputWSUnc[totalNumberWSSyst] = {};
  TH1D *histo_WSUnc[nwrongsignSyst] = {};
  if(anaSel.Contains("sswwAnalysis")){
    const TString wrongSignFileName = Form("%s/fillhisto_%s_%d_wrongsign.root",InputDir.Data(),anaSel.Data(),year);
    inputFile = openCheckedFile(wrongSignFileName);
    int startH = totalNumberWSSyst*fidAna;
    for(int j=0; j<totalNumberWSSyst; j++){
      histo_InputWSUnc[j] = getCheckedHistogram(inputFile,Form("histoWS_%d",j+startH),wrongSignFileName);
      checkSameBinning(histo_Baseline[kPlotWS],histo_InputWSUnc[j],Form("wrong-sign variation %d",j));
      histo_WSUnc[j+                0] = cloneDetached(histo_InputWSUnc[j],Form("histo_%s_%s", plotBaseNames[kPlotWS].Data(), namewrongsignSyst[j+                0].Data())); histo_WSUnc[j+                0]->SetDirectory(0);
      histo_WSUnc[j+totalNumberWSSyst] = cloneDetached(histo_InputWSUnc[j],Form("histo_%s_%s", plotBaseNames[kPlotWS].Data(), namewrongsignSyst[j+totalNumberWSSyst].Data())); histo_WSUnc[j+totalNumberWSSyst]->SetDirectory(0);
    }
    inputFile->Close(); delete inputFile; inputFile=nullptr;

    for(int j=0; j<totalNumberWSSyst; j++){
      for(int nb=1; nb<=histo_Baseline[kPlotWS]->GetNbinsX(); nb++){
        histo_WSUnc[j+                0]->SetBinContent(nb, TMath::Max((float)histo_WSUnc[j+                0]->GetBinContent(nb),0.000001f));
        histo_WSUnc[j+totalNumberWSSyst]->SetBinContent(nb, TMath::Max((float)histo_WSUnc[j+totalNumberWSSyst]->GetBinContent(nb),0.000001f));
        if(histo_Baseline[kPlotWS]->GetBinContent(nb) > 0) {
          systValue = histo_WSUnc[j+0]->GetBinContent(nb) / histo_Baseline[kPlotWS]->GetBinContent(nb);
          if     (systValue > 1.45/1) systValue = 1.45/1;
          else if(systValue < 1/1.45) systValue = 1/1.45;
          histo_WSUnc[j+0]->SetBinContent(nb,histo_Baseline[kPlotWS]->GetBinContent(nb)*systValue);
          printf("ws(%d,%d) = %.3f\n",j,nb,systValue);
          if(systValue > 0) histo_WSUnc[j+totalNumberWSSyst]->SetBinContent(nb,histo_Baseline[kPlotWS]->GetBinContent(nb)/systValue);
        }
      }
    }
  }
  // End wrongsign study

  TString additionalSuffix = "";
  if(whichAna != 0){
    additionalSuffix = "_alt";
  }

  // Begin renormalize
  for(int ic=kPlotData; ic<nPlotCategories; ic++) {
    if(histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(isTheorySignal[ic] == false)  continue;
    scaleToIntegral(histo_QCDScaleUp[ic],histo_Baseline[ic]->GetSumOfWeights(),histo_QCDScaleUp[ic]->GetName());
    scaleToIntegral(histo_QCDScaleDown[ic],histo_Baseline[ic]->GetSumOfWeights(),histo_QCDScaleDown[ic]->GetName());
    scaleToIntegral(histo_PSUp[ic],histo_Baseline[ic]->GetSumOfWeights(),histo_PSUp[ic]->GetName());
    scaleToIntegral(histo_PSDown[ic],histo_Baseline[ic]->GetSumOfWeights(),histo_PSDown[ic]->GetName());
    for(int npdf=0; npdf<101; npdf++){
      scaleToIntegral(histo_PDFUp[npdf][ic],histo_Baseline[ic]->GetSumOfWeights(),histo_PDFUp[npdf][ic]->GetName());
      scaleToIntegral(histo_PDFDown[npdf][ic],histo_Baseline[ic]->GetSumOfWeights(),histo_PDFDown[npdf][ic]->GetName());
    }
    for(int j=0; j<nSystDataCardTotal; j++) {
      TString histName = histo_SystDataCard[j][ic]->GetName();
      if(histName.Contains("pileup")) {
        scaleToIntegral(histo_SystDataCard[j][ic],histo_Baseline[ic]->GetSumOfWeights(),histo_SystDataCard[j][ic]->GetName());
      }
      if(histName.Contains("ewkCorr")) {
        scaleToIntegral(histo_SystDataCard[j][ic],histo_Baseline[ic]->GetSumOfWeights(),histo_SystDataCard[j][ic]->GetName());
      }
    }
  }
  // End renormalize

  // Begin Fix a feature affecting first bin
  for(int ic=kPlotData; ic<nPlotCategories; ic++) {
    if(histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotData) {
      histo_Baseline[ic]->SetBinError(1,sqrt(histo_Baseline[ic]->GetBinContent(1)));
    } else {
      if(histo_Baseline[ic]->GetNbinsX() >= 2 && histo_Baseline[ic]->GetBinContent(1) > 0 && histo_Baseline[ic]->GetBinError(1)/histo_Baseline[ic]->GetBinContent(1) > 0.10) {
        float relativeUncBin2 = 0.01;
        if(histo_Baseline[ic]->GetBinContent(2) > 0) relativeUncBin2 = histo_Baseline[ic]->GetBinError(2)/histo_Baseline[ic]->GetBinContent(2);
        histo_Baseline[ic]->SetBinError(1,relativeUncBin2*histo_Baseline[ic]->GetBinContent(1));
      }
    }
  }
  // End Fix a feature affecting first bin

  // Begin scale expectations to observations (step 2)
  for(int ic=kPlotData; ic<nPlotCategories; ic++) {
    histo_Baseline[ic]->Scale(postFitSF[ic]);
    for(int j=0; j<nSystDataCardTotal; j++) histo_SystDataCard[j][ic]->Scale(postFitSF[ic]);

    histo_QCDScaleUp  [ic]->Scale(postFitSF[ic]);
    histo_QCDScaleDown[ic]->Scale(postFitSF[ic]);
    histo_PSUp        [ic]->Scale(postFitSF[ic]);
    histo_PSDown      [ic]->Scale(postFitSF[ic]);
    for(int npdf=0; npdf<101; npdf++){
      histo_PDFUp  [npdf][ic]->Scale(postFitSF[ic]);
      histo_PDFDown[npdf][ic]->Scale(postFitSF[ic]);
    }
  }
  // End scale expectations to observations (step 2)

  if(anaSel.Contains("wzAnalysis")) histo_Baseline[kPlotQCDSSWW]->Scale(0.0);

  TString outputLimits = Form("datacard_%s_%d_bin%d%s.root",anaSel.Data(),year,fidAna,additionalSuffix.Data());
  outputFile = openCheckedFile(outputLimits, "RECREATE");
  outputFile->cd();
  for(int ic=kPlotData; ic<nPlotCategories; ic++) {
    if(histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    histo_Baseline[ic]->Write();
    for(int j=0; j<nSystDataCardTotal; j++) { if(nameSyst[j]=="dummy") continue; histo_SystDataCard[j][ic]->Write(); }

    histo_QCDScaleUp  [ic]->Write();
    histo_QCDScaleDown[ic]->Write();
    histo_PSUp        [ic]->Write();
    histo_PSDown      [ic]->Write();
    for(int npdf=0; npdf<101; npdf++){
      histo_PDFUp  [npdf][ic]->Write();
      histo_PDFDown[npdf][ic]->Write();
    }
  }
  if(isTypeFakeSyst != 0) for(int j=0; j<nNonPromptSyst; j++) histo_NonPromtUnc[j]->Write();
  if(anaSel.Contains("sswwAnalysis")) for(int j=0; j<nwrongsignSyst; j++) histo_WSUnc[j]->Write();
  outputFile->Write(); outputFile->Close(); delete outputFile; outputFile=nullptr;

  const std::string outputLimitsCard = std::string("datacard_")+anaSel.Data()+"_"+std::to_string(year)+"_bin"+std::to_string(fidAna)+additionalSuffix.Data()+".txt";
  ofstream newcardShape(outputLimitsCard.c_str());
  if (!newcardShape.is_open()) { std::cerr << "ERROR: cannot create datacard " << outputLimitsCard << std::endl; return; }
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
    if     (ic != kPlotEWKSSWW &&
            ic != kPlotEWKWZ   &&
            ic != kPlotWZ      &&
            ic != kPlotSignal0 &&
            ic != kPlotSignal1 &&
            ic != kPlotSignal2 &&
            ic != kPlotSignal3 &&
            ic != kPlotSignal4 &&
            ic != kPlotSignal5
           ) newcardShape << Form("%d  ", ic);
    else if(ic == kPlotEWKSSWW) newcardShape << Form("%d  ",  0);
    else if(ic == kPlotEWKWZ  ) newcardShape << Form("%d  ", -1);
    else if(ic == kPlotWZ     ) newcardShape << Form("%d  ", -2);
    else if(ic == kPlotSignal0) newcardShape << Form("%d  ", -3);
    else if(ic == kPlotSignal1) newcardShape << Form("%d  ", -4);
    else if(ic == kPlotSignal2) newcardShape << Form("%d  ", -5);
    else if(ic == kPlotSignal3) newcardShape << Form("%d  ", -6);
    else if(ic == kPlotSignal4) newcardShape << Form("%d  ", -7);
    else if(ic == kPlotSignal5) newcardShape << Form("%d  ", -8);
  }
  newcardShape << Form("\n");

  newcardShape << Form("rate  ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    newcardShape << Form("%f  ", histo_Baseline[ic]->GetSumOfWeights());
  }
  newcardShape << Form("\n");

  if(isTypeFakeSyst == 1){
    newcardShape << Form("CMS_SMP26030_fake_%s_m      lnN ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("%6.3f ",1.15);
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");

    newcardShape << Form("CMS_SMP26030_fake_%s_e lnN ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("%6.3f ",1.15);
      else		       newcardShape << Form("- ");
    }
    newcardShape << Form("\n");
  } // isTraditionalSyst == true
  else if(isTypeFakeSyst == 2){
    newcardShape << Form("CMS_SMP26030_fake_%s_m0 shape ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");

    newcardShape << Form("CMS_SMP26030_fake_%s_m1 shape ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");

    newcardShape << Form("CMS_SMP26030_fake_%s_m2 shape ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");

    newcardShape << Form("CMS_SMP26030_fake_%s_e0 shape ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");

    newcardShape << Form("CMS_SMP26030_fake_%s_e1 shape ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");

    newcardShape << Form("CMS_SMP26030_fake_%s_e2 shape ",nameFakeSyst.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotNonPrompt) newcardShape << Form("1.0 ");
      else		       newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");
  } // isTraditionalSyst == false

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

  newcardShape << Form("CMS_SMP26030_trigger_%s   lnN     ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("%6.3f ",triggerEffUnc);
  }
  newcardShape << Form("\n");

  if(anaSel.Contains("sswwAnalysis")) {
    newcardShape << Form("CMS_SMP26030_wrongsign_stat_%s shape ",theTagYear.Data());
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotWS) newcardShape << Form("1.0 ");
      else              newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");


    newcardShape << Form("CMS_SMP26030_wrongsign_method shape ");
    for (int ic=0; ic<nPlotCategories; ic++){
      if(!histo_Baseline[ic]) continue;
      if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
      if(ic == kPlotWS) newcardShape << Form("1.0 ");
      else              newcardShape << Form("- "); 
    }
    newcardShape << Form("\n");
  }

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

  newcardShape << Form("CMS_SMP26030_eff_m_tightid_%s shape ",theTagYear.Data());
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if(ic == kPlotNonPrompt) newcardShape << Form("- ");
    else                     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("CMS_SMP26030_eff_e_tightid_%s shape ",theTagYear.Data());
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
    if     (ic == kPlotSignal0 || ic == kPlotSignal1 || ic == kPlotSignal2 || ic == kPlotSignal3 || ic == kPlotSignal4 || ic == kPlotSignal5 || ic == kPlotEWKSSWW) continue;
    newcardShape << Form("QCD_scale_%s_ACCEPT shape ",plotBaseNames[ic].Data());
    for(unsigned ic2=0; ic2<nPlotCategories; ic2++) {
      if(ic2 == kPlotData || histo_Baseline[ic2]->GetSumOfWeights() <= 0) continue;
      if(ic==ic2) newcardShape << Form("1.0  ");
      else        newcardShape << Form("-  ");
      }
      newcardShape << Form("\n");
  } 

  newcardShape << Form("QCD_scale_EWKSSWW_ACCEPT shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if     (ic != kPlotSignal0 &&
            ic != kPlotSignal1 &&
            ic != kPlotSignal2 &&
            ic != kPlotSignal3 &&
            ic != kPlotSignal4 &&
            ic != kPlotSignal5 &&
            ic != kPlotEWKSSWW
            ) newcardShape << Form("- ");
    else      newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  for(unsigned ic=0; ic<nPlotCategories; ic++) {
    if(ic== kPlotData || ic == kPlotNonPrompt || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if     (ic == kPlotSignal0 || ic == kPlotSignal1 || ic == kPlotSignal2 || ic == kPlotSignal3 || ic == kPlotSignal4 || ic == kPlotSignal5 || ic == kPlotEWKSSWW) continue;
    newcardShape << Form("PS_%s_ACCEPT shape ",plotBaseNames[ic].Data());
    for(unsigned ic2=0; ic2<nPlotCategories; ic2++) {
      if(ic2 == kPlotData || histo_Baseline[ic2]->GetSumOfWeights() <= 0) continue;
      if(ic==ic2) newcardShape << Form("1.0  ");
      else        newcardShape << Form("-  ");
      }
      newcardShape << Form("\n");
  } 

  newcardShape << Form("PS_EWKSSWW_ACCEPT shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if     (ic != kPlotSignal0 &&
            ic != kPlotSignal1 &&
            ic != kPlotSignal2 &&
            ic != kPlotSignal3 &&
            ic != kPlotSignal4 &&
            ic != kPlotSignal5 &&
            ic != kPlotEWKSSWW
           ) newcardShape << Form("- ");
    else     newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("WWewkCorr shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if     (ic != kPlotSignal0 &&
            ic != kPlotSignal1 &&
            ic != kPlotSignal2 &&
            ic != kPlotSignal3 &&
            ic != kPlotSignal4 &&
            ic != kPlotSignal5 &&
            ic != kPlotEWKSSWW
            ) newcardShape << Form("- ");
    else      newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

  newcardShape << Form("WZewkCorr shape ");
  for (int ic=0; ic<nPlotCategories; ic++){
    if(!histo_Baseline[ic]) continue;
    if(ic == kPlotData || histo_Baseline[ic]->GetSumOfWeights() <= 0) continue;
    if     (ic != kPlotEWKWZ
            ) newcardShape << Form("- ");
    else      newcardShape << Form("1.0 ");
  }
  newcardShape << Form("\n");

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

  if(anaSel.Contains("sswwAnalysis") || anaSel.Contains("wzAnalysis")){
    if(histo_Baseline[kPlotWZ] && histo_Baseline[kPlotWZ]->GetSumOfWeights() > 0)
    newcardShape << Form("CMS_ssww_%snorm  rateParam * %s 1 [0.1,4.9]\n",plotBaseNames[kPlotWZ].Data(),plotBaseNames[kPlotWZ].Data());
    if(histo_Baseline[kPlotEWKWZ] && histo_Baseline[kPlotEWKWZ]->GetSumOfWeights() > 0)
    newcardShape << Form("CMS_ssww_%snorm  rateParam * %s 1 [0.1,4.9]\n",plotBaseNames[kPlotEWKWZ].Data(),plotBaseNames[kPlotEWKWZ].Data());
    if(histo_Baseline[kPlotTVX] && histo_Baseline[kPlotTVX]->GetSumOfWeights() > 0)
    newcardShape << Form("CMS_ssww_%snorm  rateParam * %s 1 [0.1,4.9]\n",plotBaseNames[kPlotTVX].Data(),plotBaseNames[kPlotTVX].Data());
  }
  if(anaSel.Contains("sswwAnalysis")){
    if(histo_Baseline[kPlotNonPrompt] && histo_Baseline[kPlotNonPrompt]->GetSumOfWeights() > 0)
    newcardShape << Form("CMS_ssww_%snorm  rateParam * %s 1 [0.1,4.9]\n",plotBaseNames[kPlotNonPrompt].Data(),plotBaseNames[kPlotNonPrompt].Data());
  }

  newcardShape << Form("ch%d autoMCStats 0\n",fidAna);

  newcardShape.close();
  if (!newcardShape) { std::cerr << "ERROR writing datacard " << outputLimitsCard << std::endl; return; }
  std::cout << "Created shape file: " << outputLimits << std::endl;
  std::cout << "Created datacard: " << outputLimitsCard << std::endl;

  // Explicit cleanup: this macro is often invoked repeatedly in one ROOT
  // session, so do not leave detached histograms accumulating in memory.
  for (int ic=0; ic<nPlotCategories; ++ic) {
    delete histo_Baseline[ic]; delete histo_QCDScaleUp[ic]; delete histo_QCDScaleDown[ic];
    delete histo_PSUp[ic]; delete histo_PSDown[ic];
    for (int j=0; j<nSystTotal; ++j) delete histo_Syst[j][ic];
    for (int j=0; j<nSystDataCardTotal; ++j) delete histo_SystDataCard[j][ic];
    for (int j=0; j<101; ++j) { delete histo_PDFUp[j][ic]; delete histo_PDFDown[j][ic]; }
  }
  for (int j=0; j<totalNumberFakeSyst; ++j) delete histo_InputNonPromtUnc[j];
  for (int j=0; j<nNonPromptSyst; ++j) delete histo_NonPromtUnc[j];
  for (int j=0; j<totalNumberWSSyst; ++j) delete histo_InputWSUnc[j];
  for (int j=0; j<nwrongsignSyst; ++j) delete histo_WSUnc[j];

}
