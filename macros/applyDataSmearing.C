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

void theApplyDataSmearing(TString inputName, double factor){
  TFile* file = new TFile(inputName, "read");
  const int nPlotCategories = 26;
  TH1F* _hist[nPlotCategories];
  
  for(int ic=0; ic<nPlotCategories; ic++){
    _hist[ic] = (TH1F*)file->Get(Form("histo%d",ic));
  }
  TH1F* hBck = (TH1F*)_hist[0]->Clone(Form("hBck"));
  hBck->Scale(0);
  for(int ic=1; ic<nPlotCategories; ic++){
    hBck->Add(_hist[ic]);
  }

  for(int nb=1; nb<=_hist[0]->GetNbinsX(); nb++){
    double systValue = 1.0;
    if(hBck->GetBinContent(nb) > 0 && _hist[0]->GetBinContent(nb) > 0){
      systValue = 1.0+(_hist[0]->GetBinContent(nb)/hBck->GetBinContent(nb)-1.0)/factor;
    }
    hBck->SetBinContent(nb,hBck->GetBinContent(nb)+systValue);
    printf("DA/MC = %d %f\n",nb, systValue);
    for(int ic=1; ic<nPlotCategories; ic++){
      _hist[ic]->SetBinContent(nb,_hist[ic]->GetBinContent(nb)*systValue);
    }
  }

  //while(_hist[0]->GetSumOfWeights() < hBck->GetSumOfWeights()){
  //  _hist[0]->Fill(hBck->GetRandom());
  //}

  double sumBck = 0;
  TString outputName = inputName.ReplaceAll(".root","_alt.root");
  TFile output(outputName,"RECREATE");
  for(int ic=0; ic<nPlotCategories; ic++){
    _hist[ic]->Write();
    if(ic!=0) sumBck = sumBck + _hist[ic]->GetSumOfWeights();
  }
  output.Close();
  //printf("DA/MC = %f/%f\n", _hist[0]->GetSumOfWeights(),sumBck);
}

void applyDataSmearing(int nsel = -1, int condorJob = 1001){
  double factor = 2.5;
  TString inputFolder = "anaZ/";
  vector<TString> infileName_;
  if      (nsel == 0){
    factor = 1.45;
    infileName_.push_back(Form("%sfillhisto_zAnalysis%d_2027_256",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_zAnalysis%d_2027_390",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_zAnalysis%d_2027_391",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_zAnalysis%d_2027_392",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_zAnalysis%d_2027_393",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_zAnalysis%d_2027_394",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_zAnalysis%d_2027_395",inputFolder.Data(),condorJob));
  }
  else if(nsel == 1){
    factor = 2.5;
    infileName_.push_back(Form("%sfillhisto_wzAnalysis%d_2028_110",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_wzAnalysis%d_2028_111",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_wzAnalysis%d_2028_112",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_wzAnalysis%d_2028_113",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_wzAnalysis%d_2028_114",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_wzAnalysis%d_2028_115",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_wzAnalysis%d_2028_116",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_wzAnalysis%d_2028_117",inputFolder.Data(),condorJob));
  }
  else if(nsel == 3){
    factor = 2.5;
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_32",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_33",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_34",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_35",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_36",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_37",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_38",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_39",inputFolder.Data(),condorJob));

    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_46",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_47",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_48",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_49",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_50",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_51",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_52",inputFolder.Data(),condorJob));
    infileName_.push_back(Form("%sfillhisto_sswwAnalysis%d_2028_53",inputFolder.Data(),condorJob));
  }
  else {
    return;
  }

  for(UInt_t ifile=0; ifile<infileName_.size(); ifile++) {
    printf("%s\n",infileName_[ifile].Data());

    // true == file does not exist!
    if(gSystem->AccessPathName(Form("%s_bak.root",infileName_[ifile].Data())))
      gSystem->Exec(Form("cp %s.root %s_bak.root",infileName_[ifile].Data(),infileName_[ifile].Data()));
    else
      gSystem->Exec(Form("cp %s_bak.root %s.root",infileName_[ifile].Data(),infileName_[ifile].Data()));

    theApplyDataSmearing(Form("%s.root",infileName_[ifile].Data()),factor);

    gSystem->Exec(Form("mv %s_alt.root %s.root",infileName_[ifile].Data(),infileName_[ifile].Data()));
  }
}
