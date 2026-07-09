#include "correction.h"
#include <stdio.h>
#include <string.h>
#include <iostream>

#include "muonCrystalBall.h"

//g++ $(correction config --cflags --ldflags) mysf.cpp -shared -fPIC -o mysf.so

class MyCorrections {
  public:
    MyCorrections(int the_input_year);

    double eval_puSF      (double NumTrueInteractions, std::string weights);

    double eval_muonTRKSF (double eta, double pt, double p, const char *valType);
    double eval_muonIDSF  (double eta, double pt, const char *valType);
    double eval_muonISOSF (double eta, double pt, const char *valType);

    double eval_electronTRKSF(const char *the_input_year, const char *valType, const char *workingPoint, double eta, double pt, double phi);
    double eval_electronIDSF (const char *the_input_year, const char *valType, const char *workingPoint, double eta, double pt, double phi);
    double eval_electronMVASF(const char *the_input_year, const char *valType, const char *workingPoint, double eta, double pt, double phi);
    double eval_electronEtDependentScale(const char *valType, const double run, const double eta, const double r9, const double pt, const double gain);
    double eval_electronEtDependentSmearing(const char *valType, const double pt, const double r9, const double eta);
    double eval_photonSF  (const char *the_input_year, const char *valType, const char *workingPoint, double eta, double pt, double phi);

    double eval_tauJETSF  (double pt, int dm, int genmatch, const char *workingPoint, const char *workingPoint_VSe, const char *valType);

    double eval_btvSF     (const char *valType, char *workingPoint, double eta, double pt, int flavor);

    double eval_jetCORR   (double area, double eta, double phi, double pt, double rho, int run, int type);
    double eval_jesUnc    (double eta, double pt, int type);
    double eval_jerScaleFactor(double eta, double pt, int type);
    double eval_jerPtResolution(double eta, double pt, double rho);
    double eval_puJetIDSF (char *valType, char *workingPoint, double eta, double pt);
    double eval_jetVetoMap(double eta, double phi, int type);
    double eval_jetSel    (unsigned int sel, float eta, float chHEF, float neHEF, float chEmEF, float neEmEF, float muEF, int chMultiplicity, int neMultiplicity);

    double eval_muon_pt_resol(double pt, double eta, float nL);
    double eval_muon_pt_resol_var(double pt_woresol, double pt_wresol, double eta, string updn);
    double eval_muon_pt_scale(bool is_data, double pt, double eta, double phi, int charge);
    double eval_muon_pt_scale_var(double pt, double eta, double phi, int charge, string updn);
    double eval_met_corr(const char *pt_phi, const char *met_type, const char *epoch, const char *dtmc, const char *variation, float met_pt, float met_phi, float npvGood);

  private:
    double muon_get_rndm(double eta, float nL);
    double muon_get_std(double pt, double eta, float nL);
    double muon_get_k(double eta, string var);
    correction::Correction::Ref puSF_;
    correction::Correction::Ref muonScale_cb_params_;
    correction::Correction::Ref muonScale_poly_params_;
    correction::Correction::Ref muonScale_k_data_;
    correction::Correction::Ref muonScale_a_data_;
    correction::Correction::Ref muonScale_m_data_;
    correction::Correction::Ref muonScale_k_mc_;
    correction::Correction::Ref muonScale_a_mc_;
    correction::Correction::Ref muonScale_m_mc_;
    correction::Correction::Ref muonTRKSF_;
    correction::Correction::Ref muonIDSF_;
    correction::Correction::Ref muonISOSF_;
    correction::Correction::Ref muonHighPtTRKSF_;
    correction::Correction::Ref muonHighPtIDSF_;
    correction::Correction::Ref muonHighPtISOSF_;
    correction::Correction::Ref electronTRKSF_;
    correction::Correction::Ref electronIDSF_;
    correction::Correction::Ref electronMVASF_;
    correction::CompoundCorrection::Ref electronEtDependentScale_;
    correction::Correction::Ref electronEtDependentSmearing_;
    correction::Correction::Ref photonSF_;
    correction::Correction::Ref tauJETSF_;
    correction::Correction::Ref btvHFSF_;
    correction::Correction::Ref btvLFSF_;
    correction::CompoundCorrection::Ref JECMC_;
    correction::CompoundCorrection::Ref JECDATA_[10];
    correction::Correction::Ref JECL2ResDATA_[10];
    correction::Correction::Ref jetVetoMap_[10];
    correction::Correction::Ref jesSourcesUnc_[28];
    correction::Correction::Ref jerScaleFactor_;
    correction::Correction::Ref jerPtResolution__;
    correction::Correction::Ref puJetIDSF_;
    correction::Correction::Ref jetTightSel_;
    correction::Correction::Ref jetTightLeptonVetoSel_;
    correction::Correction::Ref metCorr_;
    int year;
};

MyCorrections::MyCorrections(int the_input_year) {

  int debug = 0;

  year = the_input_year;

  std::string dirName    = "jsonpog-integration/POG/";

  std::string subDirName = "";
  if     (year == 20160) subDirName = "Run2-2016preVFP-UL-NanoAODv15/"; 
  else if(year == 20161) subDirName = "Run2-2016postVFP-UL-NanoAODv15/"; 
  else if(year == 20170) subDirName = "Run2-2017-UL-NanoAODv15/"; 
  else if(year == 20180) subDirName = "Run2-2018-UL-NanoAODv15/"; 
  else if(year == 20220) subDirName = "Run3-22CDSep23-Summer22-NanoAODv12/"; 
  else if(year == 20221) subDirName = "Run3-22EFGSep23-Summer22EE-NanoAODv12/";
  else if(year == 20230) subDirName = "Run3-23CSep23-Summer23-NanoAODv12/";
  else if(year == 20231) subDirName = "Run3-23DSep23-Summer23BPix-NanoAODv12/";
  else if(year == 20240) subDirName = "Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15/";
  else if(year == 20250 ||
          year == 20260 ||
          year == 20261) subDirName = "Run3-25Prompt-Summer24-NanoAODv15/";
  else return;

  std::cout << "subDirName/year: " << subDirName << " " << year << std::endl;

  std::string fileNameLUM = dirName+"LUM/"+subDirName+"puWeights.json.gz";

  std::string corrNameLUM = "";  
  if     (year == 20160) corrNameLUM = "Collisions2022_355100_357900_eraBCD_GoldenJson";
  else if(year == 20161) corrNameLUM = "Collisions2022_355100_357900_eraBCD_GoldenJson";
  else if(year == 20170) corrNameLUM = "Collisions2022_355100_357900_eraBCD_GoldenJson";
  else if(year == 20180) corrNameLUM = "Collisions2022_355100_357900_eraBCD_GoldenJson";
  else if(year == 20220) corrNameLUM = "Collisions2022_355100_357900_eraBCD_GoldenJson";
  else if(year == 20221) corrNameLUM = "Collisions2022_359022_362760_eraEFG_GoldenJson";
  else if(year == 20230) corrNameLUM = "Collisions2023_366403_369802_eraBC_GoldenJson";
  else if(year == 20231) corrNameLUM = "Collisions2023_369803_370790_eraD_GoldenJson";
  else if(year == 20240 ||
          year == 20250 ||
          year == 20260 ||
          year == 20261) corrNameLUM = "Collisions24_BCDEFGHI_goldenJSON";
  
  auto csetPU = correction::CorrectionSet::from_file(fileNameLUM);
  puSF_ = csetPU->at(corrNameLUM);

  if(debug > 0) std::cout << "pass lum" << std::endl;

  if(year == 20240 || year == 20250 || year == 20260 || year == 20261) {
    std::string fileNameHFBTV = dirName+"BTV/"+subDirName+"btagging.json.gz";
    auto csetHFBTV = correction::CorrectionSet::from_file(fileNameHFBTV);
    btvHFSF_ = csetHFBTV->at("UParTAK4_comb");
    std::string fileNameLFBTV = dirName+"BTV/"+subDirName+"btagging.json.gz";
    auto csetLFBTV = correction::CorrectionSet::from_file(fileNameLFBTV);
    btvLFSF_ = csetLFBTV->at("UParTAK4_light");
  }
  else {
    std::string fileNameHFBTV = dirName+"BTV/"+subDirName+"btagging.json.gz";
    auto csetHFBTV = correction::CorrectionSet::from_file(fileNameHFBTV);
    btvHFSF_ = csetHFBTV->at("robustParticleTransformer_comb");
    std::string fileNameLFBTV = dirName+"BTV/"+subDirName+"btagging.json.gz";
    auto csetLFBTV = correction::CorrectionSet::from_file(fileNameLFBTV);
    btvLFSF_ = csetLFBTV->at("robustParticleTransformer_light");
  }

  if(debug > 0) std::cout << "pass btag" << std::endl;

  std::string fileNameScaleMu = dirName+"MUO/"+subDirName+"muon_scalesmearing.json.gz";
  auto csetScaleMu = correction::CorrectionSet::from_file(fileNameScaleMu);
  muonScale_cb_params_   = csetScaleMu->at("cb_params");
  muonScale_poly_params_ = csetScaleMu->at("poly_params");
  muonScale_k_data_ = csetScaleMu->at("k_data");
  muonScale_a_data_ = csetScaleMu->at("a_data");
  muonScale_m_data_ = csetScaleMu->at("m_data");
  muonScale_k_mc_   = csetScaleMu->at("k_mc");
  muonScale_a_mc_   = csetScaleMu->at("a_mc");
  muonScale_m_mc_   = csetScaleMu->at("m_mc");

  std::string fileNameMu = dirName+"MUO/"+subDirName+"muon_Z.json.gz";
  auto csetMu = correction::CorrectionSet::from_file(fileNameMu);
  //muonTRKSF_ = csetMu->at("NUM_TrackerMuons_DEN_genTracks");
  muonIDSF_ = csetMu->at("NUM_MediumPromptID_DEN_TrackerMuons");
  muonISOSF_ = csetMu->at("NUM_LoosePFIso_DEN_MediumPromptID");

  std::string fileNameHighPtRECOMu       = dirName+"MUO/"+subDirName+"muon_HighPt.json.gz";
  if(year == 20240) fileNameHighPtRECOMu = dirName+"MUO/"+subDirName+"ScaleFactors_Muon_highPt_RECO_2024_schemaV2.json.gz";
  auto csetHighPtRECOMu = correction::CorrectionSet::from_file(fileNameHighPtRECOMu);
  muonHighPtTRKSF_ = csetHighPtRECOMu->at("NUM_GlobalMuons_DEN_TrackerMuonProbes");

  std::string fileNameHighPtIDISOMu       = dirName+"MUO/"+subDirName+"muon_HighPt.json.gz";
  if(year == 20240 || year == 20250 || year == 20260 || year == 20261) fileNameHighPtIDISOMu = dirName+"MUO/"+subDirName+"muon_HighPt.json.gz";
  auto csetHighPtIDISOMu = correction::CorrectionSet::from_file(fileNameHighPtIDISOMu);
  muonHighPtIDSF_ = csetHighPtIDISOMu->at("NUM_MediumID_DEN_GlobalMuonProbes");
  muonHighPtISOSF_ = csetHighPtIDISOMu->at("NUM_probe_TightRelTkIso_DEN_MediumIDProbes");

  if(debug > 0) std::cout << "pass muo" << std::endl;
  
  std::string fileNamePH = dirName+"EGM/"+subDirName+"photon.json.gz";
  auto csetPH = correction::CorrectionSet::from_file(fileNamePH);
  if(year >= 20220) photonSF_ = csetPH->at("Photon-ID-SF");
  else              photonSF_ = csetPH->at("UL-Photon-ID-SF");

  if(debug > 0) std::cout << "pass pho" << std::endl;

  std::string fileNameTRKELE = dirName+"EGM/"+subDirName+"electron.json.gz";
  auto csetTRKELE = correction::CorrectionSet::from_file(fileNameTRKELE);
  if(year >= 20220) electronTRKSF_ = csetTRKELE->at("Electron-ID-SF");
  else              electronTRKSF_ = csetTRKELE->at("UL-Electron-ID-SF");

  std::string fileNameIDELE = dirName+"EGM/"+subDirName+"electron.json.gz";
  auto csetIDELE = correction::CorrectionSet::from_file(fileNameIDELE);
  if(year >= 20220) electronIDSF_ = csetIDELE->at("Electron-ID-SF");
  else              electronIDSF_ = csetIDELE->at("UL-Electron-ID-SF");

  std::string fileNameMVAELE = dirName+"EGM/"+subDirName+"electron_mva.json.gz";
  auto csetMVAELE = correction::CorrectionSet::from_file(fileNameMVAELE);
  electronMVASF_ = csetMVAELE->at("Electron-ID-SF");

  std::string fileNameEnergyEtDependentELE = dirName+"EGM/"+subDirName+"electronSS_EtDependent.json.gz";
  auto csetEnergyEtDependentELE = correction::CorrectionSet::from_file(fileNameEnergyEtDependentELE);
  if     (year == 20160) {electronEtDependentScale_ = csetEnergyEtDependentELE->compound().at("Scale"); electronEtDependentSmearing_ = csetEnergyEtDependentELE->at("SmearAndSyst");}
  else if(year == 20161) {electronEtDependentScale_ = csetEnergyEtDependentELE->compound().at("Scale"); electronEtDependentSmearing_ = csetEnergyEtDependentELE->at("SmearAndSyst");}
  else if(year == 20170) {electronEtDependentScale_ = csetEnergyEtDependentELE->compound().at("Scale"); electronEtDependentSmearing_ = csetEnergyEtDependentELE->at("SmearAndSyst");}
  else if(year == 20180) {electronEtDependentScale_ = csetEnergyEtDependentELE->compound().at("Scale"); electronEtDependentSmearing_ = csetEnergyEtDependentELE->at("SmearAndSyst");}
  else if(year == 20220) {electronEtDependentScale_ = csetEnergyEtDependentELE->compound().at("Scale"); electronEtDependentSmearing_ = csetEnergyEtDependentELE->at("SmearAndSyst");}
  else if(year == 20221) {electronEtDependentScale_ = csetEnergyEtDependentELE->compound().at("Scale"); electronEtDependentSmearing_ = csetEnergyEtDependentELE->at("SmearAndSyst");}
  else if(year == 20230) {electronEtDependentScale_ = csetEnergyEtDependentELE->compound().at("Scale"); electronEtDependentSmearing_ = csetEnergyEtDependentELE->at("SmearAndSyst");}
  else if(year == 20231) {electronEtDependentScale_ = csetEnergyEtDependentELE->compound().at("Scale"); electronEtDependentSmearing_ = csetEnergyEtDependentELE->at("SmearAndSyst");}
  else if(year == 20240 ||
          year == 20250 ||
          year == 20260 ||
          year == 20261) {electronEtDependentScale_ = csetEnergyEtDependentELE->compound().at("Scale"); electronEtDependentSmearing_ = csetEnergyEtDependentELE->at("SmearAndSyst");}

  if(debug > 0) std::cout << "pass egm" << std::endl;

  std::string fileNameTAU = dirName+"TAU/"+subDirName+"tau_DeepTau2018v2p5.json.gz";
  auto csetTAU = correction::CorrectionSet::from_file(fileNameTAU);
  tauJETSF_ = csetTAU->at("DeepTau2018v2p5VSjet");

  if(debug > 0) std::cout << "pass tau" << std::endl;

  std::string fileNameJER = dirName+"JME/"+subDirName+"jet_jerc.json.gz";
  //std::cout << fileNameJER << std::endl;
  auto csetJER = correction::CorrectionSet::from_file(fileNameJER);

  std::string fileNameJEC = dirName+"JME/"+subDirName+"jet_jerc.json.gz";
  //std::cout << fileNameJEC << std::endl;
  auto csetJEC = correction::CorrectionSet::from_file(fileNameJEC);

  std::string algoName = "AK4PFPuppi";

  std::string jecMCName = ""; std::string jerName = "";
  std::string jecDATAName[10]    = {"NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL"};
  std::string jetVetoMapName[10] = {"NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL","NULL"};

  if(year == 20160 || year == 20161)  {
    algoName = "AK4PFchs";
    jecMCName = "Summer19UL16APV_V7_MC"; jerName = "Summer20UL16APV_JRV3_MC";
    jecDATAName[0] = "Summer19UL16APV_RunBCD_V7_DATA";   jetVetoMapName[0] = "Summer19UL16_V1"; // A
    jecDATAName[1] = "Summer19UL16APV_RunBCD_V7_DATA";   jetVetoMapName[1] = "Summer19UL16_V1"; // B
    jecDATAName[2] = "Summer19UL16APV_RunBCD_V7_DATA";   jetVetoMapName[2] = "Summer19UL16_V1"; // C
    jecDATAName[3] = "Summer19UL16APV_RunBCD_V7_DATA";   jetVetoMapName[3] = "Summer19UL16_V1"; // D
    jecDATAName[4] = "Summer19UL16APV_RunEF_V7_DATA";    jetVetoMapName[4] = "Summer19UL16_V1"; // E
    jecDATAName[5] = "Summer19UL16APV_RunEF_V7_DATA";    jetVetoMapName[5] = "Summer19UL16_V1"; // F 20160
    jecDATAName[6] = "Summer19UL16APV_RunEF_V7_DATA";    jetVetoMapName[6] = "Summer19UL16_V1"; // F 20161
    jecDATAName[7] = "Summer19UL16APV_RunEF_V7_DATA";    jetVetoMapName[7] = "Summer19UL16_V1"; // G
    jecDATAName[8] = "Summer19UL16APV_RunEF_V7_DATA";    jetVetoMapName[8] = "Summer19UL16_V1"; // H
  }
  else if(year == 20170)  {
    algoName = "AK4PFchs";
    jecMCName = "Summer19UL17_V5_MC"; jerName = "Summer19UL17_JRV2_MC";
    jecDATAName[1] = "Summer19UL17_RunB_V5_DATA";   jetVetoMapName[1] = "Summer19UL17_V1"; // B
    jecDATAName[2] = "Summer19UL17_RunC_V5_DATA";   jetVetoMapName[2] = "Summer19UL17_V1"; // C
    jecDATAName[3] = "Summer19UL17_RunD_V5_DATA";   jetVetoMapName[3] = "Summer19UL17_V1"; // D
    jecDATAName[4] = "Summer19UL17_RunE_V5_DATA";   jetVetoMapName[4] = "Summer19UL17_V1"; // E
    jecDATAName[5] = "Summer19UL17_RunF_V5_DATA";   jetVetoMapName[5] = "Summer19UL17_V1"; // F
  }
  else if(year == 20180)  {
    algoName = "AK4PFchs";
    jecMCName = "Summer19UL18_V5_MC"; jerName = "Summer19UL18_JRV2_MC";
    jecDATAName[0] = "Summer19UL18_RunA_V5_DATA";   jetVetoMapName[0] = "Summer19UL18_V1"; // A
    jecDATAName[1] = "Summer19UL18_RunB_V5_DATA";   jetVetoMapName[1] = "Summer19UL18_V1"; // B
    jecDATAName[2] = "Summer19UL18_RunC_V5_DATA";   jetVetoMapName[2] = "Summer19UL18_V1"; // C
    jecDATAName[3] = "Summer19UL18_RunD_V5_DATA";   jetVetoMapName[3] = "Summer19UL18_V1"; // D
  }
  else if(year == 20220)  {
    jecMCName = "Summer22_22Sep2023_V3_MC"; jerName = "Summer22_22Sep2023_JRV1_MC";
    jecDATAName[0] = "Summer22_22Sep2023_V3_DATA";   jetVetoMapName[0] = "Summer22_23Sep2023_RunCD_V1"; // A
    jecDATAName[1] = "Summer22_22Sep2023_V3_DATA";   jetVetoMapName[1] = "Summer22_23Sep2023_RunCD_V1"; // B
    jecDATAName[2] = "Summer22_22Sep2023_V3_DATA";   jetVetoMapName[2] = "Summer22_23Sep2023_RunCD_V1"; // C
    jecDATAName[3] = "Summer22_22Sep2023_V3_DATA";   jetVetoMapName[3] = "Summer22_23Sep2023_RunCD_V1"; // D
    jecDATAName[4] = "NULL"; jetVetoMapName[4] = "NULL";  // E
    jecDATAName[5] = "NULL"; jetVetoMapName[5] = "NULL";  // F
    jecDATAName[6] = "NULL"; jetVetoMapName[6] = "NULL";  // G
  }
  else if(year == 20221)  {
    jecMCName = "Summer22EE_22Sep2023_V3_MC"; jerName = "Summer22EE_22Sep2023_JRV1_MC";
    jecDATAName[0] = "NULL";   jetVetoMapName[0] = "NULL"; // A
    jecDATAName[1] = "NULL";   jetVetoMapName[1] = "NULL"; // B
    jecDATAName[2] = "NULL";   jetVetoMapName[2] = "NULL"; // C
    jecDATAName[3] = "NULL";   jetVetoMapName[3] = "NULL"; // D
    jecDATAName[4] = "Summer22EE_22Sep2023_V3_DATA"; jetVetoMapName[4] = "Summer22EE_23Sep2023_RunEFG_V1";  // E
    jecDATAName[5] = "Summer22EE_22Sep2023_V3_DATA"; jetVetoMapName[5] = "Summer22EE_23Sep2023_RunEFG_V1";  // F
    jecDATAName[6] = "Summer22EE_22Sep2023_V3_DATA"; jetVetoMapName[6] = "Summer22EE_23Sep2023_RunEFG_V1";  // G
  }
  else if(year == 20230)  {
    jecMCName = "Summer23Prompt23_V3_MC"; jerName = "Summer23Prompt23_RunCv1234_JRV1_MC";
    jecDATAName[0] = "NULL";   jetVetoMapName[0] = "NULL"; // A
    jecDATAName[1] = "NULL";   jetVetoMapName[1] = "NULL"; // B
    jecDATAName[2] = "Summer23Prompt23_V3_DATA";   jetVetoMapName[2] = "Summer23Prompt23_RunC_V1"; // C
    jecDATAName[3] = "NULL";   jetVetoMapName[3] = "NULL"; // D
    jecDATAName[4] = "NULL";   jetVetoMapName[4] = "NULL"; // E
    jecDATAName[5] = "NULL";   jetVetoMapName[5] = "NULL"; // F
    jecDATAName[6] = "NULL";   jetVetoMapName[6] = "NULL"; // G
  }
  else if(year == 20231)  {
    jecMCName = "Summer23BPixPrompt23_V3_MC"; jerName = "Summer23BPixPrompt23_RunD_JRV1_MC";
    jecDATAName[0] = "NULL";   jetVetoMapName[0] = "NULL"; // A
    jecDATAName[1] = "NULL";   jetVetoMapName[1] = "NULL"; // B
    jecDATAName[2] = "NULL";   jetVetoMapName[2] = "NULL"; // C
    jecDATAName[3] = "Summer23BPixPrompt23_V3_DATA";   jetVetoMapName[3] = "Summer23BPixPrompt23_RunD_V1"; // D
    jecDATAName[4] = "NULL";   jetVetoMapName[4] = "NULL"; // E
    jecDATAName[5] = "NULL";   jetVetoMapName[5] = "NULL"; // F
    jecDATAName[6] = "NULL";   jetVetoMapName[6] = "NULL"; // G
  }
  else if(year == 20240)  {
    jecMCName = "Summer24Prompt24_V2_MC"; jerName = "Summer23BPixPrompt23_RunD_JRV1_MC";
    jecDATAName[0] = "NULL";                     jetVetoMapName[0] = "Summer24Prompt24_RunBCDEFGHI_V1"; // A
    jecDATAName[1] = "Summer24Prompt24_V2_DATA"; jetVetoMapName[1] = "Summer24Prompt24_RunBCDEFGHI_V1"; // B
    jecDATAName[2] = "Summer24Prompt24_V2_DATA"; jetVetoMapName[2] = "Summer24Prompt24_RunBCDEFGHI_V1"; // C
    jecDATAName[3] = "Summer24Prompt24_V2_DATA"; jetVetoMapName[3] = "Summer24Prompt24_RunBCDEFGHI_V1"; // D
    jecDATAName[4] = "Summer24Prompt24_V2_DATA"; jetVetoMapName[4] = "Summer24Prompt24_RunBCDEFGHI_V1"; // E
    jecDATAName[5] = "Summer24Prompt24_V2_DATA"; jetVetoMapName[5] = "Summer24Prompt24_RunBCDEFGHI_V1"; // F
    jecDATAName[6] = "Summer24Prompt24_V2_DATA"; jetVetoMapName[6] = "Summer24Prompt24_RunBCDEFGHI_V1"; // G
    jecDATAName[7] = "Summer24Prompt24_V2_DATA"; jetVetoMapName[7] = "Summer24Prompt24_RunBCDEFGHI_V1"; // H
    jecDATAName[8] = "Summer24Prompt24_V2_DATA"; jetVetoMapName[8] = "Summer24Prompt24_RunBCDEFGHI_V1"; // I
    jecDATAName[9] = "NULL";                     jetVetoMapName[9] = "Summer24Prompt24_RunBCDEFGHI_V1"; // J
  }
  else if(year == 20250 || year == 20260 || year == 20261)  {
    jecMCName = "Winter25Prompt25_V3_MC"; jerName = "Summer23BPixPrompt23_RunD_JRV1_MC";
    jecDATAName[0] = "NULL";                     jetVetoMapName[0] = "Winter25Prompt25_RunCDEFG_V1"; // A
    jecDATAName[1] = "Winter25Prompt25_V3_DATA"; jetVetoMapName[1] = "Winter25Prompt25_RunCDEFG_V1"; // B
    jecDATAName[2] = "Winter25Prompt25_V3_DATA"; jetVetoMapName[2] = "Winter25Prompt25_RunCDEFG_V1"; // C
    jecDATAName[3] = "Winter25Prompt25_V3_DATA"; jetVetoMapName[3] = "Winter25Prompt25_RunCDEFG_V1"; // D
    jecDATAName[4] = "Winter25Prompt25_V3_DATA"; jetVetoMapName[4] = "Winter25Prompt25_RunCDEFG_V1"; // E
    jecDATAName[5] = "Winter25Prompt25_V3_DATA"; jetVetoMapName[5] = "Winter25Prompt25_RunCDEFG_V1"; // F
    jecDATAName[6] = "Winter25Prompt25_V3_DATA"; jetVetoMapName[6] = "Winter25Prompt25_RunCDEFG_V1"; // G
    jecDATAName[7] = "Winter25Prompt25_V3_DATA"; jetVetoMapName[7] = "Winter25Prompt25_RunCDEFG_V1"; // H
    jecDATAName[8] = "Winter25Prompt25_V3_DATA"; jetVetoMapName[8] = "Winter25Prompt25_RunCDEFG_V1"; // I
    jecDATAName[9] = "NULL";                     jetVetoMapName[9] = "Winter25Prompt25_RunCDEFG_V1"; // J
  }

  std::string tagName = jecMCName + "_" + "L1L2L3Res" + "_" + algoName;
  JECMC_ = csetJEC->compound().at(tagName);

  tagName = jecMCName + "_" + "Total" + "_" + algoName;
  jesSourcesUnc_[0] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "AbsoluteMPFBias" + "_" + algoName;
  jesSourcesUnc_[ 1] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "AbsoluteScale" + "_" + algoName;
  jesSourcesUnc_[ 2] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "AbsoluteStat" + "_" + algoName;
  jesSourcesUnc_[ 3] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "FlavorQCD" + "_" + algoName;
  jesSourcesUnc_[ 4] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "Fragmentation" + "_" + algoName;
  jesSourcesUnc_[ 5] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "PileUpDataMC" + "_" + algoName;
  jesSourcesUnc_[ 6] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "PileUpPtBB" + "_" + algoName;
  jesSourcesUnc_[ 7] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "PileUpPtEC1" + "_" + algoName;
  jesSourcesUnc_[ 8] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "PileUpPtEC2" + "_" + algoName;
  jesSourcesUnc_[ 9] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "PileUpPtHF" + "_" + algoName;
  jesSourcesUnc_[10] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "PileUpPtRef" + "_" + algoName;
  jesSourcesUnc_[11] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativeFSR" + "_" + algoName;
  jesSourcesUnc_[12] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativeJEREC1" + "_" + algoName;
  jesSourcesUnc_[13] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativeJEREC2" + "_" + algoName;
  jesSourcesUnc_[14] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativeJERHF" + "_" + algoName;
  jesSourcesUnc_[15] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativePtBB" + "_" + algoName;
  jesSourcesUnc_[16] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativePtEC1" + "_" + algoName;
  jesSourcesUnc_[17] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativePtEC2" + "_" + algoName;
  jesSourcesUnc_[18] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativePtHF" + "_" + algoName;
  jesSourcesUnc_[19] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativeBal" + "_" + algoName;
  jesSourcesUnc_[20] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativeSample" + "_" + algoName;
  jesSourcesUnc_[21] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativeStatEC" + "_" + algoName;
  jesSourcesUnc_[22] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativeStatFSR" + "_" + algoName;
  jesSourcesUnc_[23] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "RelativeStatHF" + "_" + algoName;
  jesSourcesUnc_[24] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "SinglePionECAL" + "_" + algoName;
  jesSourcesUnc_[25] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "SinglePionHCAL" + "_" + algoName;
  jesSourcesUnc_[26] = csetJEC->at(tagName);

  tagName = jecMCName + "_" + "TimePtEta" + "_" + algoName;
  jesSourcesUnc_[27] = csetJEC->at(tagName);

  for(int i=0; i<10; i++){
    if(jecDATAName[i].compare("NULL") == 0) continue;
    tagName = jecDATAName[i] + "_" + "L1L2L3Res" + "_" + algoName;
    JECDATA_[i] = csetJEC->compound().at(tagName);
    tagName = jecDATAName[i] + "_" + "L2Relative" + "_" + algoName;
    JECL2ResDATA_[i] = csetJEC->at(tagName);
  }

  tagName = jerName + "_" + "ScaleFactor" + "_" + algoName;
  //std::cout << tagName << std::endl;
  jerScaleFactor_ = csetJER->at(tagName);

  tagName = jerName + "_" + "PtResolution" + "_" + algoName;
  jerPtResolution__ = csetJER->at(tagName);

  //std::string fileNamePUJetID = dirName+"JME/"+subDirName+"jmar.json.gz";
  //auto csetPUJetID = correction::CorrectionSet::from_file(fileNamePUJetID);
  //puJetIDSF_ = csetPUJetID->at("PUJetID_eff");

  //std::cout << fileNameJEC << std::endl;
  std::string fileNamejetVetoMap = dirName+"JME/"+subDirName+"jetvetomaps.json.gz";
  auto csetJetVetoMap = correction::CorrectionSet::from_file(fileNamejetVetoMap);

  for(int i=0; i<10; i++){
    if(jetVetoMapName[i].compare("NULL") == 0) continue;
    jetVetoMap_[i] = csetJetVetoMap->at(jetVetoMapName[i]);
  }

  std::string fileNameJetSel = dirName+"JME/"+subDirName+"jetid.json.gz";
  //std::cout << fileNameJetSel << std::endl;
  auto csetJetSel = correction::CorrectionSet::from_file(fileNameJetSel);
  jetTightSel_           = csetJetSel->at("AK4PUPPI_Tight");
  jetTightLeptonVetoSel_ = csetJetSel->at("AK4PUPPI_TightLeptonVeto");

  std::string fileNameMetCorr = dirName+"JME/"+subDirName+"met_xyCorrections.json.gz";
  auto csetMetCorr = correction::CorrectionSet::from_file(fileNameMetCorr);
  metCorr_ = csetMetCorr->at("met_xy_corrections");

  if(debug > 0) std::cout << "pass jme" << std::endl;

};

double MyCorrections::eval_puSF(double int1, std::string str1) {
  return puSF_->evaluate({int1, str1});
};

double MyCorrections::eval_muonTRKSF(double eta, double pt, double p, const char *valType) {
  eta = std::max(std::min(eta,2.399),-2.399);
  pt = std::max(pt,15.001);
  if(pt > 200)                            return muonHighPtTRKSF_->evaluate({fabs(eta), p, valType});
  else if(strcmp(valType,"nominal") == 0) return 1.0;
  else                                    return 0.0;
  return 1.0;
};

double MyCorrections::eval_muonIDSF(double eta, double pt, const char *valType) {
  eta = std::max(std::min(eta,2.399),-2.399);
  pt = std::max(pt,15.001);
  if(pt > 200) return muonHighPtIDSF_->evaluate({fabs(eta), pt, valType});
  else         return muonIDSF_->evaluate({eta, pt, valType});
  return 1.0;
};

double MyCorrections::eval_muonISOSF(double eta, double pt, const char *valType) {
  eta = std::max(std::min(eta,2.399),-2.399);
  pt = std::max(pt,15.001);
  if(pt > 200) return muonHighPtISOSF_->evaluate({fabs(eta), pt, valType});
  else         return muonISOSF_->evaluate({eta, pt, valType});
  return 1.0;
};

double MyCorrections::eval_electronTRKSF(const char *the_input_year, const char *valType, const char *workingPoint, double eta, double pt, double phi) {
  pt = std::min(std::max(pt,10.001),999.9);
  if(year <= 20221 || year >= 20240) return electronTRKSF_->evaluate({the_input_year, valType, workingPoint, eta, pt});
  return electronTRKSF_->evaluate({the_input_year, valType, workingPoint, eta, pt, phi});
};

double MyCorrections::eval_electronIDSF(const char *the_input_year, const char *valType, const char *workingPoint, double eta, double pt, double phi) {
  pt = std::min(std::max(pt,10.001),999.9);
  if(year <= 20221 || year >= 20240) return electronIDSF_->evaluate({the_input_year, valType, workingPoint, eta, pt});
  return electronIDSF_->evaluate({the_input_year, valType, workingPoint, eta, pt, phi});
};

double MyCorrections::eval_electronMVASF(const char *the_input_year, const char *valType, const char *workingPoint, double eta, double pt, double phi) {
  pt = std::min(std::max(pt,10.001),999.9);
  return electronMVASF_->evaluate({the_input_year, valType, workingPoint, eta, pt});
};

double MyCorrections::eval_electronEtDependentScale(const char *valType, const double run, const double eta, const double r9, const double pt, const double gain) {
  return electronEtDependentScale_->evaluate({valType, run, eta, r9, pt, gain});
};

double MyCorrections::eval_electronEtDependentSmearing(const char *valType, const double pt, const double r9, const double eta) {
  double eta_bounds = std::max(std::min(eta,2.399),-2.399);
  return electronEtDependentSmearing_->evaluate({valType, pt, r9, eta_bounds});
};


double MyCorrections::eval_photonSF(const char *the_input_year, const char *valType, const char *workingPoint, double eta, double pt, double phi) {
  pt = std::max(pt,20.001);
  if(year <= 20221 || year >= 20240) return photonSF_->evaluate({the_input_year, valType, workingPoint, eta, pt});
  return photonSF_->evaluate({the_input_year, valType, workingPoint, eta, pt, phi});
};

double MyCorrections::eval_tauJETSF(double pt, int dm, int genmatch, const char *workingPoint, const char *workingPoint_VSe, const char *valType) {
  pt = std::min(std::max(pt,20.001),1999.999);
  if(dm == 5 || dm == 6) dm = 0;
  return tauJETSF_->evaluate({pt, dm, genmatch, workingPoint, workingPoint_VSe, valType, "dm"});
};

double MyCorrections::eval_btvSF(const char *valType, char *workingPoint, double eta, double pt, int flavor) {
  if(eta <= -2.5 || eta >= 2.5) return 0.0;
  eta = std::min(std::abs(eta),2.399);
  pt = std::min(pt,999.999);
  if(flavor != 0) {
    if(year == 20240 || year == 20250 || year == 20260 || year == 20261) return btvHFSF_->evaluate({valType, workingPoint, flavor, eta, pt});
    else                                                                 return btvHFSF_->evaluate({valType, workingPoint, flavor, eta, pt});
  }
  else {
    return btvLFSF_->evaluate({valType, workingPoint, flavor, eta, pt});
  }
};

double MyCorrections::eval_jetCORR(double area, double eta, double phi, double pt, double rho, int run, int type) {
  int theRun = run;
  if(year == 20250 && theRun < 392159) theRun = 392159;
  // data
  if(type >= 0 && (year == 20260 || year == 20261))                       return 1.0;
  else if(type >= 0 && (year == 20231 || year == 20240 || year == 20250)) return JECDATA_[type]->evaluate({area, eta, pt, rho, phi, (float)theRun});
  else if(type >= 0 && (year == 20220 || year == 20221 || year == 20230)) return JECDATA_[type]->evaluate({area, eta, pt, rho,      (float)theRun});
  else if(type >= 0)                                                      return JECDATA_[type]->evaluate({area, eta, pt, rho});
  // MC
  if     (year == 20231 || year == 20240 || year == 20250 || year == 20260 || year == 20261) return JECMC_->evaluate({area, eta, pt, rho, phi});
  else                                                                                       return JECMC_->evaluate({area, eta, pt, rho});
  printf("ERROR in eval_jetCORR!\n");
  return 1.0;
};

double MyCorrections::eval_jesUnc(double eta, double pt, int type) {
  return std::abs(jesSourcesUnc_[type]->evaluate({eta, pt}));
};

double MyCorrections::eval_jerScaleFactor(double eta, double pt, int type) {
  if(year < 20210){
    if     (type ==  0) return jerScaleFactor_->evaluate({eta,"nom"});
    else if(type == +1) return jerScaleFactor_->evaluate({eta,"up"});
    else if(type == -1) return jerScaleFactor_->evaluate({eta,"down"});
  } else {
    if     (type ==  0) return jerScaleFactor_->evaluate({eta,pt,"nom"});
    else if(type == +1) return jerScaleFactor_->evaluate({eta,pt,"up"});
    else if(type == -1) return jerScaleFactor_->evaluate({eta,pt,"down"});
  }
  std::cout << "0 JER correction!" << std::endl;
  return 0.0;
};

double MyCorrections::eval_jerPtResolution(double eta, double pt, double rho) {
  return jerPtResolution__->evaluate({eta,pt,rho});
};

double MyCorrections::eval_puJetIDSF(char *valType, char *workingPoint, double eta, double pt) {
  return puJetIDSF_->evaluate({eta, pt, valType, workingPoint});
};

double MyCorrections::eval_jetVetoMap(double eta, double phi, int type) {
  eta = std::min(std::max(eta,-5.18),5.18);
  phi = std::min(std::max(phi,-3.1415),3.1415);
  if(type >= 0) return jetVetoMap_[type]->evaluate({"jetvetomap", eta, phi});
  return 0;
};

double MyCorrections::eval_jetSel(unsigned int sel, float eta, float chHEF, float neHEF, float chEmEF, float neEmEF, float muEF, int chMultiplicity, int neMultiplicity) {
  eta = fabs(eta);
  float result = 0;
  int multiplicity = chMultiplicity + neMultiplicity;
  if(sel == 0) {
    result = jetTightSel_          ->evaluate({eta, chHEF, neHEF, chEmEF, neEmEF, muEF, chMultiplicity, neMultiplicity, multiplicity});
  }
  else if(sel == 1) {
    result = jetTightLeptonVetoSel_->evaluate({eta, chHEF, neHEF, chEmEF, neEmEF, muEF, chMultiplicity, neMultiplicity, multiplicity});
  }
  return result;
};

double MyCorrections::eval_met_corr(const char *pt_phi, const char *met_type, const char *epoch, const char *dtmc, const char *variation, float met_pt, float met_phi, float npvGood) {

  float result = metCorr_->evaluate({pt_phi, met_type, epoch, dtmc, variation, met_pt, met_phi, npvGood});
  return result;

};

// Muon momentum scale and resolution
double MyCorrections::muon_get_rndm(double eta, float nL) {

    // obtain parameters from correctionlib
    double mean = muonScale_cb_params_->evaluate({abs(eta), nL, 0});
    double sigma = muonScale_cb_params_->evaluate({abs(eta), nL, 1});
    double n = muonScale_cb_params_->evaluate({abs(eta), nL, 2});
    double alpha = muonScale_cb_params_->evaluate({abs(eta), nL, 3});
    
    // instantiate CB and get random number following the CB
    CrystalBall cb(mean, sigma, alpha, n);
    TRandom3 rnd(time(0));
    double rndm = gRandom->Rndm();
    return cb.invcdf(rndm);
}

double MyCorrections::muon_get_std(double pt, double eta, float nL) {

    // obtain paramters from correctionlib
    double param_0 = muonScale_poly_params_->evaluate({abs(eta), nL, 0});
    double param_1 = muonScale_poly_params_->evaluate({abs(eta), nL, 1});
    double param_2 = muonScale_poly_params_->evaluate({abs(eta), nL, 2});

    // calculate value and return max(0, val)
    double sigma = param_0 + param_1 * pt + param_2 * pt*pt;
    if (sigma < 0) sigma = 0;
    return sigma; 
}

double MyCorrections::muon_get_k(double eta, string var) {

    // obtain parameters from correctionlib
    double k_data = muonScale_k_data_->evaluate({abs(eta), var});
    double k_mc = muonScale_k_mc_->evaluate({abs(eta), var});

    // calculate residual smearing factor
    // return 0 if smearing in MC already larger than in data
    double k = 0;
    if (k_mc < k_data) k = sqrt(k_data*k_data - k_mc*k_mc);
    return k;
}

double MyCorrections::eval_muon_pt_resol(double pt, double eta, float nL) {

    // load correction values
    double rndm = (double) muon_get_rndm(eta, nL);
    double std = (double) muon_get_std(pt, eta, nL);
    double k = (double) muon_get_k(eta, "nom");

    // calculate corrected value and return original value if a parameter is nan
    double ptc = pt * ( 1 + k * std * rndm);
    if (isnan(ptc)) ptc = pt;
    return ptc;
}

double MyCorrections::eval_muon_pt_resol_var(double pt_woresol, double pt_wresol, double eta, string updn){
    
    double k = (double) muon_get_k(eta, "nom");

    if (k==0) return pt_wresol;

    double k_unc = muonScale_k_mc_->evaluate({abs(eta), "stat"});

    double std_x_rndm = (pt_wresol / pt_woresol - 1) / k;

    double pt_var = pt_wresol;

    if (updn=="up"){
        pt_var = pt_woresol * (1 + (k+k_unc) * std_x_rndm);
    }
    else if (updn=="dn"){
        pt_var = pt_woresol * (1 + (k-k_unc) * std_x_rndm);
    }
    else {
        cout << "ERROR: updn must be 'up' or 'dn'" << endl;
    }

    return pt_var;
}

double MyCorrections::eval_muon_pt_scale(bool is_data, double pt, double eta, double phi, int charge) {
        
    double a = 0.0;
    double m = 1.0;

    if (is_data) {
      a = muonScale_a_data_->evaluate({eta, phi, "nom"});
      m = muonScale_m_data_->evaluate({eta, phi, "nom"});
    }
    else {
      a = muonScale_a_mc_->evaluate({eta, phi, "nom"});
      m = muonScale_m_mc_->evaluate({eta, phi, "nom"});
    }
    return 1. / (m/pt + charge * a);
}

double MyCorrections::eval_muon_pt_scale_var(double pt, double eta, double phi, int charge, string updn) {
        
    double stat_a = muonScale_a_mc_->evaluate({eta, phi, "stat"});
    double stat_m = muonScale_m_mc_->evaluate({eta, phi, "stat"});
    double stat_rho = muonScale_m_mc_->evaluate({eta, phi, "rho_stat"});

    double unc = pt*pt*sqrt(stat_m*stat_m / (pt*pt) + stat_a*stat_a + 2*charge*stat_rho*stat_m/pt*stat_a);

    double pt_var = pt;
    
    if (updn=="up"){
        pt_var = pt + unc;
    }
    else if (updn=="dn"){
        pt_var = pt - unc;
    }

    return pt_var;
}
