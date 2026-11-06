#include "TROOT.h"
#include "Math/ProbFuncMathCore.h"
#include "TInterpreter.h"
#include "TFile.h"
#include "TCanvas.h"
#include "TH1F.h"
#include "TStyle.h"
#include "TPad.h"
#include "Math/QuantFuncMathCore.h"
#include "TMath.h"
#include "TGraphAsymmErrors.h"
#include "TSystem.h"
#include "CMS_lumi.C"
#include "TRandom.h"
#include "common.h"

// shapeName = shapes_fit_s / shapes_fit_b / shapes_prefit

void producingYields_ssww(int category = -1, TString mlfitResult = "/home/submit/ceballos/cards/ww_smp24001/logs_ana1009/fitDiagnosticsww_fid_normalized1_obs.root", TString shapeName = "shapes_fit_s") {

  TFile *mlfit = TFile::Open(mlfitResult); assert(mlfit);

  int chanAux = 6;

  const int chan = chanAux;
  TString channelName[chan];
  if     (category == 0) { // WW SR
    channelName[0] = Form("ww0b_20220");
    channelName[1] = Form("ww0b_20221");
    channelName[2] = Form("ww0b_20230");
    channelName[3] = Form("ww0b_20231");
    channelName[4] = Form("ww0b_20240");
    channelName[5] = Form("ww0b_20250");
  }
  else if(category == 1) { // WWb CR
    channelName[0] = Form("ww1b_20220");
    channelName[1] = Form("ww1b_20221");
    channelName[2] = Form("ww1b_20230");
    channelName[3] = Form("ww1b_20231");
    channelName[4] = Form("ww1b_20240");
    channelName[5] = Form("ww1b_20250");
  }
  else if(category == 2) { // WZ SR
    channelName[0] = Form("wz0b_20220");
    channelName[1] = Form("wz0b_20221");
    channelName[2] = Form("wz0b_20230");
    channelName[3] = Form("wz0b_20231");
    channelName[4] = Form("wz0b_20240");
    channelName[5] = Form("wz0b_20250");
  }
  else if(category == 3) { // WZb CR
    channelName[0] = Form("wz1b_20220");
    channelName[1] = Form("wz1b_20221");
    channelName[2] = Form("wz1b_20230");
    channelName[3] = Form("wz1b_20231");
    channelName[4] = Form("wz1b_20240");
    channelName[5] = Form("wz1b_20250");
  }

  double yields[nPlotCategories], yieldsE[nPlotCategories];
  bool nonZeroYields[nPlotCategories];
  double total, totalE;
  for(int ic=0; ic<nPlotCategories; ic++){
    nonZeroYields[ic] = false;
    yields[ic] = 0;
    yieldsE[ic] = 0;
  }
  total = 0;
  totalE = 0;

  TH1F* _hist[chan][nPlotCategories+1];
  for(int nc=0; nc<chan; nc++){

    _hist[nc][nPlotCategories] = ((TH1F*)mlfit->Get(Form("%s/%s/%s",shapeName.Data(),channelName[nc].Data(),"total")));
    for(int nb=1; nb<=_hist[nc][nPlotCategories]->GetNbinsX(); nb++) {
      total  += _hist[nc][nPlotCategories]->GetBinContent(nb);
      totalE += _hist[nc][nPlotCategories]->GetBinError(nb);
    } // loop over bins

    for(int ic=0; ic<nPlotCategories; ic++){
      if(ic != kPlotData){
        _hist[nc][ic] = ((TH1F*)mlfit->Get(Form("%s/%s/%s",shapeName.Data(),channelName[nc].Data(),plotBaseNames[ic].Data())));
        if(_hist[nc][ic]){
          for(int nb=1; nb<=_hist[nc][ic]->GetNbinsX(); nb++) {
            int theIC = ic;
            if(ic == kPlotEWKSSWW ||
               ic == kPlotSignal0 || ic == kPlotSignal1 || ic == kPlotSignal2 ||
               ic == kPlotSignal3 || ic == kPlotSignal4 || ic == kPlotSignal5) theIC = kPlotEWKSSWW;
            yields[theIC]  += _hist[nc][ic]->GetBinContent(nb);
            yieldsE[theIC] += _hist[nc][ic]->GetBinError(nb);
            nonZeroYields[theIC] = true;
          } // loop over bins
        }
      }
      else {
        nonZeroYields[kPlotData] = true;
        double x,y;
        TGraphAsymmErrors *gr = ((TGraphAsymmErrors*)mlfit->Get(Form("%s/%s/%s",shapeName.Data(),channelName[nc].Data(),"data")));
        for(int nb=1; nb<=_hist[nc][nPlotCategories]->GetNbinsX(); nb++) {
          int a = gr->GetPoint(nb-1, x, y);
          yields[ic]  += y;
          yieldsE[ic] += y;
        } // loop over bins
      } // data
    } // loop over categories

    // Special for NonPromptWZ
    if((TH1F*)mlfit->Get(Form("%s/%s/%s",shapeName.Data(),channelName[nc].Data(),"NonWZPrompt"))){
      _hist[nc][kPlotNonPrompt] = ((TH1F*)mlfit->Get(Form("%s/%s/%s",shapeName.Data(),channelName[nc].Data(),"NonWZPrompt")));
      for(int nb=1; nb<=_hist[nc][kPlotNonPrompt]->GetNbinsX(); nb++) {
        yields[kPlotNonPrompt]  += _hist[nc][kPlotNonPrompt]->GetBinContent(nb);
        yieldsE[kPlotNonPrompt] += _hist[nc][kPlotNonPrompt]->GetBinError(nb);
        nonZeroYields[kPlotNonPrompt] = true;
      } // loop over bins
    }

  } // loop over categories

  for(int ic=0; ic<nPlotCategories; ic++){
    if(nonZeroYields[ic] == true) {
      printf("%20s & ",plotBaseNames[ic].Data());
      yieldsE[kPlotData] = sqrt(yieldsE[kPlotData]);
      if(ic == kPlotData) printf("	%6d	    ",(int)yields[ic]);
      else		  printf(" %7.1f $\\pm$ %5.1f ",yields[ic],yieldsE[ic]);
      printf("\\\\");
      printf("\n");
    }
  }
  printf("%20s & ","Total");
  printf(" %7.1f $\\pm$ %5.1f ",total,sqrt(total));
  printf("\\\\");
  printf("\n");
}
