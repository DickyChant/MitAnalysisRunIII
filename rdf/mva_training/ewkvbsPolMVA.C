#include <TROOT.h>
#include <TMVA/DataLoader.h>
#include <TMVA/Factory.h>
#include <TMVA/Types.h>
#include <TFile.h>
#include <TCut.h>
#include <TTree.h>
#include <TString.h>
#include <TStyle.h>

void ewkvbsPolMVA(
  int nsel = 0,
  int version = 0,
  bool moreMVAs = false,
  bool dodnn = false
) {

  float ptCut = 50;
  TString extraString = Form("vbfpolwwcm_pcut%d_nsel%d_v%d",(int)ptCut,nsel,version);

  gROOT->ProcessLine("TMVA::gConfig().GetVariablePlotting().fMaxNumOfAllowedVariablesForScatterPlots = 50");
  TFile *output_file;
  TMVA::Factory *factory;
  TString trainTreeEventSplitStr="(eventNum % 10)<5";
  TString testTreeEventSplitStr="(eventNum % 10)>=5";

  TChain *mvaTree = new TChain("events");
  mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleWWPolWWCMAna_year2027.root");

  // Initialize the factory
  output_file=TFile::Open(Form("MVA_%s.root",extraString.Data()), "RECREATE");
  factory = new TMVA::Factory("bdt", output_file, "!V:!Silent:DrawProgressBar:Transformations=I;D;P;G,D:AnalysisType=Multiclass");
  TString factoryOptions="!V:!Silent:DrawProgressBar";
  if(nsel != 0) factoryOptions+=":AnalysisType=Classification";
  factory = new TMVA::Factory("bdt", output_file, factoryOptions);
  TMVA::DataLoader *dataloader=new TMVA::DataLoader("MitEWKVBSAnalysis");

  if(nsel == 0){ // LL vs. LT vs. TT
    TCut cutTrainWWLL = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d)",trainTreeEventSplitStr.Data(),ptCut,ptCut,20);
    TCut cutTrainWWLT = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d)",trainTreeEventSplitStr.Data(),ptCut,ptCut,21);
    TCut cutTrainWWTT = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d)",trainTreeEventSplitStr.Data(),ptCut,ptCut,22);
    TCut cutTestWWLL  = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d)", testTreeEventSplitStr.Data(),ptCut,ptCut,20);
    TCut cutTestWWLT  = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d)", testTreeEventSplitStr.Data(),ptCut,ptCut,21);
    TCut cutTestWWTT  = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==%d)", testTreeEventSplitStr.Data(),ptCut,ptCut,22);

    dataloader->AddTree(mvaTree, "WWLL", 1.0, cutTrainWWLL, "train");
    dataloader->AddTree(mvaTree, "WWLT", 1.0, cutTrainWWLT, "train");
    dataloader->AddTree(mvaTree, "WWTT", 1.0, cutTrainWWTT, "train");
    dataloader->AddTree(mvaTree, "WWLL", 1.0, cutTestWWLL , "test");
    dataloader->AddTree(mvaTree, "WWLT", 1.0, cutTestWWLT , "test");
    dataloader->AddTree(mvaTree, "WWTT", 1.0, cutTestWWTT , "test");
    dataloader->SetWeightExpression("1.0", "WWLL");
    dataloader->SetWeightExpression("1.0", "WWLT");
    dataloader->SetWeightExpression("1.0", "WWTT");
  }
  else if(nsel == 1){ // LX vs. TT
    TCut cutTrainWWLX = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==20||theCat==21)",trainTreeEventSplitStr.Data(),ptCut,ptCut);
    TCut cutTrainWWTT = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==22||theCat== 0)",trainTreeEventSplitStr.Data(),ptCut,ptCut);
    TCut cutTestWWLX  = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==20||theCat==21)",testTreeEventSplitStr.Data(),ptCut,ptCut);
    TCut cutTestWWTT  = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==22||theCat== 0)",testTreeEventSplitStr.Data(),ptCut,ptCut);

    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleZAna_ltype0_year2027.root");
    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleZAna_ltype1_year2027.root");
    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleZAna_ltype2_year2027.root");

    dataloader->AddTree(mvaTree, "Signal"    , 1.0, cutTrainWWLX, "train");
    dataloader->AddTree(mvaTree, "Background", 1.0, cutTrainWWTT, "train");
    dataloader->AddTree(mvaTree, "Signal"    , 1.0, cutTestWWLX , "test");
    dataloader->AddTree(mvaTree, "Background", 1.0, cutTestWWTT , "test");
    if(version == 6){
      dataloader->SetWeightExpression("abs(weight)", "Signal"    );
      dataloader->SetWeightExpression("abs(weight)", "Background");
    } else {
      dataloader->SetWeightExpression("1.0", "Signal"    );
      dataloader->SetWeightExpression("1.0", "Background");
    }
  }
  else if(nsel == 2){ // LL vs. TX
    TCut cutTrainWWLL = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==20)",trainTreeEventSplitStr.Data(),ptCut,ptCut);
    TCut cutTrainWWTX = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==21||theCat==22||theCat==0)",trainTreeEventSplitStr.Data(),ptCut,ptCut);
    TCut cutTestWWLL  = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==20)",testTreeEventSplitStr.Data(),ptCut,ptCut);
    TCut cutTestWWTX  = Form("%s && vbs_ptj1 > %.0f && vbs_ptj2 > %.0f && (theCat==21||theCat==22||theCat==0)",testTreeEventSplitStr.Data(),ptCut,ptCut);

    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleZAna_ltype0_year2027.root");
    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleZAna_ltype1_year2027.root");
    mvaTree->Add("/work/submit/ceballos/mva_samples/ntupleZAna_ltype2_year2027.root");

    dataloader->AddTree(mvaTree, "Signal"    , 1.0, cutTrainWWLL, "train");
    dataloader->AddTree(mvaTree, "Background", 1.0, cutTrainWWTX, "train");
    dataloader->AddTree(mvaTree, "Signal"    , 1.0, cutTestWWLL , "test");
    dataloader->AddTree(mvaTree, "Background", 1.0, cutTestWWTX , "test");
    if(version == 6){
      dataloader->SetWeightExpression("abs(weight)", "Signal"    );
      dataloader->SetWeightExpression("abs(weight)", "Background");
    } else {
      dataloader->SetWeightExpression("1.0", "Signal"    );
      dataloader->SetWeightExpression("1.0", "Background");
    }
  }

  if(nsel == 0 || nsel == 1 || nsel == 2){
    if(version != 99) dataloader->AddVariable("vbs_dphijj"    ,"vbs_dphijj"    ,"",'F');
    if(version != 99) dataloader->AddVariable("vbs_ptj1"      ,"vbs_ptj1"      ,"",'F');
    if(version != 99) dataloader->AddVariable("vbs_ptj2"      ,"vbs_ptj2"      ,"",'F');
    if(version != 99) dataloader->AddVariable("ptl1Def"       ,"ptl1Def"       ,"",'F');
    if(version != 99) dataloader->AddVariable("ptl2Def"       ,"ptl2Def"       ,"",'F');
    if(version != 99) dataloader->AddVariable("mllDef"        ,"mllDef"        ,"",'F');
    if(version != 99) dataloader->AddVariable("dphillDef"     ,"dphillDef"     ,"",'F');
    if(version != 99) dataloader->AddVariable("vbs_zepmax"    ,"vbs_zepmax"    ,"",'F');
    if(version != 99) dataloader->AddVariable("vbs_detavvj2"  ,"vbs_detavvj2"  ,"",'F');
    if(version != 99) dataloader->AddVariable("vbs_rpt"       ,"vbs_rpt"       ,"",'F');
    if(version != 99) dataloader->AddVariable("mcollDef"      ,"mcollDef"      ,"",'F');
    if(version != 99) dataloader->AddVariable("PuppiMET_ptDef","PuppiMET_ptDef","",'F');

    if(version != 99) dataloader->AddVariable("vbs_etaj2"     ,"vbs_etaj2"     ,"",'F');
    if(version != 99) dataloader->AddVariable("mtwmaxDef"     ,"mtwmaxDef"     ,"",'F');
    if(version != 99) dataloader->AddVariable("mtwminDef"     ,"mtwminDef"     ,"",'F');

    if(version >=  8) dataloader->AddVariable("vbs_zepvv"     ,"vbs_zepvv"     ,"",'F');
    if(version >=  8) dataloader->AddVariable("ptllDef"       ,"ptllDef"       ,"",'F');
    if(version >=  8) dataloader->AddVariable("vbs_detavvj1"  ,"vbs_detavvj1"  ,"",'F');

    if(version >=  9) dataloader->AddVariable("drllDef"       ,"drllDef"       ,"",'F');
    if(version >=  9) dataloader->AddVariable("dPhilMETMinDef","dPhilMETMinDef","",'F');
    if(version >=  9) dataloader->AddVariable("vbs_etaj1"     ,"vbs_etaj1"     ,"",'F');
    if(version >=  9) dataloader->AddVariable("vbs_ptvv"      ,"vbs_ptvv"      ,"",'F');
    if(version >=  9) dataloader->AddVariable("vbs_mjj"       ,"vbs_mjj"       ,"",'F');
    if(version >=  9) dataloader->AddVariable("vbs_detajj"    ,"vbs_detajj"    ,"",'F');

    if(version >= 10) dataloader->AddVariable("minPMETDef"    ,"minPMETDef"    ,"",'F');
    if(version >= 10) dataloader->AddVariable("vbs_dphijjll"  ,"vbs_dphijjll"  ,"",'F');
    if(version >= 10) dataloader->AddVariable("vbs_pttot"     ,"vbs_pttot"     ,"",'F');
    if(version >= 10) dataloader->AddVariable("vbs_sumHT"     ,"vbs_sumHT"     ,"",'F');
    if(version >= 10) dataloader->AddVariable("ptwwDef"       ,"ptwwDef"       ,"",'F');
    if(version >= 10) dataloader->AddVariable("vbs_ptjj"      ,"vbs_ptjj"      ,"",'F');
    if(version >= 10) dataloader->AddVariable("vbs_ptbalance" ,"vbs_ptbalance" ,"",'F');
    if(version >= 10) dataloader->AddVariable("ngood_jets"    ,"ngood_jets"    ,"",'F');
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

