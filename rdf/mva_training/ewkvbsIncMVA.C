#include <TROOT.h>
#include <TMVA/DataLoader.h>
#include <TMVA/Factory.h>
#include <TMVA/Types.h>
#include <TFile.h>
#include <TCut.h>
#include <TTree.h>
#include <TString.h>
#include <TStyle.h>

void ewkvbsIncMVA(
  int nsel = 0,
  int version = 0,
  bool moreMVAs = false,
  bool dodnn = false
) {

  float ptCut = 50;
  TString extraString = Form("vbfinc_pcut%d_nsel%d_v%d",(int)ptCut,nsel,version);

  gROOT->ProcessLine("TMVA::gConfig().GetVariablePlotting().fMaxNumOfAllowedVariablesForScatterPlots = 50");
  TFile *output_file;
  TMVA::Factory *factory;
  TString trainTreeEventSplitStr="(eventNum % 10)<5";
  TString testTreeEventSplitStr="(eventNum % 10)>=5";
  TCut cutTrainSignal;
  TCut cutTrainBkg;
  TCut cutTestSignal;
  TCut cutTestBkg;
  TChain *mvaTree = new TChain("events");

  if     (nsel == 0){ // EW WZ vs. QCD WZ
    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleWZAna_year2027.root");
    cutTrainSignal = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d)",trainTreeEventSplitStr.Data(),ptCut,ptCut,8);
    cutTrainBkg    = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d)",trainTreeEventSplitStr.Data(),ptCut,ptCut,9);
    cutTestSignal  = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d)",testTreeEventSplitStr.Data(), ptCut,ptCut,8);
    cutTestBkg     = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d)",testTreeEventSplitStr.Data(), ptCut,ptCut,9);
  }
  else if(nsel == 1){ // EW WZ vs. QCD WZ + tZq
    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleWZAna_year2027.root");
    cutTrainSignal = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d)"            ,trainTreeEventSplitStr.Data(),ptCut,ptCut,8);
    cutTrainBkg    = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d||theCat==%d)",trainTreeEventSplitStr.Data(),ptCut,ptCut,9,13);
    cutTestSignal  = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d)"            ,testTreeEventSplitStr.Data(), ptCut,ptCut,8);
    cutTestBkg     = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d||theCat==%d)",testTreeEventSplitStr.Data(), ptCut,ptCut,9,13);
  }
  else if(nsel == 2){ // 15 var / WW + WZ
    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleWWAna_year2027.root");
    cutTrainSignal = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d||theCat==%d)",trainTreeEventSplitStr.Data(),ptCut,ptCut,6,8);
    cutTrainBkg    = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d||theCat==%d)",trainTreeEventSplitStr.Data(),ptCut,ptCut,7,9);
    cutTestSignal  = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d||theCat==%d)",testTreeEventSplitStr.Data(), ptCut,ptCut,6,8);
    cutTestBkg     = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d||theCat==%d)",testTreeEventSplitStr.Data(), ptCut,ptCut,7,9);
  }
  else if(nsel == 3){ // 15 var / WW Signal vs. data
    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleWWAna_year2027.root");
    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleZAna_ltype0_year2027.root");
    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleZAna_ltype1_year2027.root");
    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleZAna_ltype2_year2027.root");
    cutTrainSignal = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && theCat==%d",trainTreeEventSplitStr.Data(),ptCut,ptCut,6);
    cutTrainBkg    = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && theCat==%d",trainTreeEventSplitStr.Data(),ptCut,ptCut,0);
    cutTestSignal  = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && theCat==%d",testTreeEventSplitStr.Data(), ptCut,ptCut,6);
    cutTestBkg     = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && theCat==%d",testTreeEventSplitStr.Data(), ptCut,ptCut,0);
  }

  // Initialize the factory
  output_file=TFile::Open(Form("MVA_%s.root",extraString.Data()), "RECREATE");
  factory = new TMVA::Factory("bdt", output_file, "!V:!Silent:DrawProgressBar:Transformations=I;D;P;G,D:AnalysisType=Multiclass");
  TString factoryOptions="!V:!Silent:DrawProgressBar";
  //TString factoryOptions="!V:!Silent:!DrawProgressBar";
  if(nsel != 2)factoryOptions+=":AnalysisType=Classification";
  factory = new TMVA::Factory("bdt", output_file, factoryOptions);
  TMVA::DataLoader *dataloader=new TMVA::DataLoader("MitEWKVBSAnalysis");

  dataloader->AddTree(mvaTree, "Signal"    , 1.0, cutTrainSignal, "train");
  dataloader->AddTree(mvaTree, "Background", 1.0, cutTrainBkg	, "train");
  dataloader->AddTree(mvaTree, "Signal"    , 1.0, cutTestSignal , "test");
  dataloader->AddTree(mvaTree, "Background", 1.0, cutTestBkg    , "test");
  //dataloader->SetWeightExpression("abs(weight)", "Signal");
  //dataloader->SetWeightExpression("abs(weight)", "Background");
  dataloader->SetWeightExpression("1.0", "Signal");
  dataloader->SetWeightExpression("1.0", "Background");
  
  if(1){
    //dataloader->AddVariable("ngood_jets"    ,"ngood_jets"    ,"",'F');
    //dataloader->AddVariable("vbs_ptjj"      ,"vbs_ptjj"      ,"",'F');
    //dataloader->AddVariable("vbs_sumHT"     ,"vbs_sumHT"     ,"",'F');
    dataloader->AddVariable("vbs_mjj"       ,"vbs_mjj"       ,"",'F');
    dataloader->AddVariable("vbs_detajj"    ,"vbs_detajj"    ,"",'F');
    dataloader->AddVariable("vbs_dphijj"    ,"vbs_dphijj"    ,"",'F');
    dataloader->AddVariable("vbs_ptj1"      ,"vbs_ptj1"      ,"",'F');
    dataloader->AddVariable("vbs_ptj2"      ,"vbs_ptj2"      ,"",'F');
    dataloader->AddVariable("vbs_etaj1"     ,"vbs_etaj1"     ,"",'F');
    dataloader->AddVariable("vbs_etaj2"     ,"vbs_etaj2"     ,"",'F');
    dataloader->AddVariable("vbs_zepvv"     ,"vbs_zepvv"     ,"",'F');
    dataloader->AddVariable("vbs_zepmax"    ,"vbs_zepmax"    ,"",'F');
    dataloader->AddVariable("vbs_ptvv"      ,"vbs_ptvv"      ,"",'F');
    dataloader->AddVariable("vbs_pttot"     ,"vbs_pttot"     ,"",'F');
    dataloader->AddVariable("vbs_detavvj1"  ,"vbs_detavvj1"  ,"",'F');
    dataloader->AddVariable("vbs_detavvj2"  ,"vbs_detavvj2"  ,"",'F');
    dataloader->AddVariable("vbs_ptbalance" ,"vbs_ptbalance" ,"",'F');
  }

  TString prepareOptions="NormMode=None";
    prepareOptions+=":SplitMode=Block"; // use e.g. all events selected by trainTreeEventSplitStr for training
    prepareOptions+=":MixMode=Random";
  dataloader->PrepareTrainingAndTestTree("", prepareOptions);

  TString hyperparameters;

  hyperparameters=
  "!H:!V:NTrees=2000:BoostType=Grad:Shrinkage=0.03:MaxDepth=5:MinNodeSize=1.5%:nCuts=200:UseBaggedBoost:GradBaggingFraction=0.6:SeparationType=GiniIndex:PruneMethod=CostComplexity:PruneStrength=3";
  factory->BookMethod(dataloader, TMVA::Types::kBDT, Form("BDTG_%s",extraString.Data()), hyperparameters);

  TString layoutString ("Layout=RELU|256,RELU|128,RELU|64,LINEAR");

  TString trainingDNN ("LearningRate=5e-4,Momentum=0.9,Repetitions=3,ConvergenceSteps=200,BatchSize=32,TestRepetitions=10,WeightDecay=1e-4,Regularization=L2,DropConfig=0.1+0.3+0.3+0.0,Multithreading=True");
  
  TString trainingStrategyString ("TrainingStrategy=");
  trainingStrategyString += trainingDNN;

  // General Options.
  TString dnnOptions ("!H:V:ErrorStrategy=CROSSENTROPY:VarTransform=N,G:WeightInitialization=XAVIERUNIFORM");
  dnnOptions.Append (":"); dnnOptions.Append (layoutString);
  dnnOptions.Append (":"); dnnOptions.Append (trainingStrategyString);
  
  // Standard implementation, no dependencies.
  TString stdOptions = dnnOptions + ":Architecture=CPU";
  if(dodnn)
    factory->BookMethod(dataloader, TMVA::Types::kDNN, "DNN", stdOptions);

  if(moreMVAs){
  hyperparameters=
  "!H:!V:BoostType=AdaBoost:NTrees=1200:MaxDepth=4:MinNodeSize=2.5%:AdaBoostBeta=0.2:SeparationType=GiniIndex:nCuts=300:UseBaggedBoost:BaggedSampleFraction=0.5:PruneMethod=CostComplexity:PruneStrength=5";
  factory->BookMethod(dataloader, TMVA::Types::kBDT, Form("BDTA_%s",extraString.Data()), hyperparameters);

  hyperparameters=
  "!H:!V:NTrees=1000:BoostType=Grad:MinNodeSize=5%:NegWeightTreatment=IgnoreNegWeightsInTraining:Shrinkage=0.10:UseBaggedBoost:GradBaggingFraction=0.3:nCuts=1000:MaxDepth=3";
  factory->BookMethod(dataloader, TMVA::Types::kBDT, Form("BDTDG_%s",extraString.Data()), hyperparameters);

  hyperparameters=
  "!H:!V:VarTransform=G,P";
  factory->BookMethod(dataloader, TMVA::Types::kHMatrix, Form("HMatrix_%s",extraString.Data()), hyperparameters);

  hyperparameters=
  "!H:!V:VarTransform=G,P:PDFInterpol=Spline2:NSmooth=5:NAvEvtPerBin=30:Nbins=50:VarTransform=PCA";
  factory->BookMethod(dataloader, TMVA::Types::kLikelihood, Form("LikelihoodPCA_%s",extraString.Data()), hyperparameters);

  hyperparameters=
  "!H:!V:VarTransform=G,P:PDFInterpol=Spline2:NSmooth=5:NAvEvtPerBin=30:Nbins=50";
  factory->BookMethod(dataloader, TMVA::Types::kLikelihood, Form("Likelihood_%s",extraString.Data()), hyperparameters);

  hyperparameters=
  "!H:!V:VarTransform=G,P:Fisher:CreateMVAPdfs:NbinsMVAPdf=50:NsmoothMVAPdf=5";
  factory->BookMethod(dataloader, TMVA::Types::kFisher, Form("Fisher_%s",extraString.Data()), hyperparameters);

  hyperparameters=
  "!H:!V:VarTransform=G,P:PDFInterpol=KDE:KDEtype=Gauss:KDEiter=Adaptive:KDEFineFactor=0.5:KDEborder=Mirror";
  factory->BookMethod(dataloader, TMVA::Types::kLikelihood, Form("LikelihoodKDE_%s",extraString.Data()), hyperparameters);

  hyperparameters=
  "!H:!V:VarTransform=Decorrelate:Fisher:CreateMVAPdfs:NbinsMVAPdf=80:NsmoothMVAPdf=3";
  factory->BookMethod(dataloader, TMVA::Types::kFisher, Form("BoostedFisher_%s",extraString.Data()), hyperparameters);

  hyperparameters=
  "!H:!V:NeuronType=tanh:VarTransform=N:NCycles=1000:HiddenLayers=N+3:TestRate=5:!UseRegulator";
  factory->BookMethod(dataloader, TMVA::Types::kMLP, Form("MLP_%s",extraString.Data()), hyperparameters);
  }

  factory->TrainAllMethods();
  factory->TestAllMethods();
  factory->EvaluateAllMethods();
  output_file->Close();
}
