// Per-variant lepton scale factors for wzzAnalysis (needs the framework: functions.h / mysf.h
// with corrSFs = MyCorrections(year) initialised by initJSONSFs(year)).
//
//   muons      V0, V2, V3: POG MediumPromptID x LoosePFIso (DEN MediumPrompt) = corrSFs
//              V1:         POG MediumPromptID x TightPFIso (loaded here from the same muon_Z.json)
//              V0 is the framework's promptMVA WP: the POG ID x LooseIso product is only an
//              approximation (group T&P maps not wired in yet).
//   electrons  reco SF x ID SF of the WP: V1 wp90iso; V2/V3 HZZ ID has no POG SF -> wp90iso as
//              placeholder (flagged; HZZ group or own T&P needed); V0 wp80iso (approximation)
//   type: 0 nominal, +1 / -1: up / down (syst and stat in quadrature, as compute_JSON_*_SFs)
#pragma once
#include <memory>
#include <string>
#include "wzz_functions.h"
#include "correction.h"

namespace wzz {

inline std::string pog_subdir(int year) {
  switch (year) {
    case 20160: return "Run2-2016preVFP-UL-NanoAODv15/";
    case 20161: return "Run2-2016postVFP-UL-NanoAODv15/";
    case 20170: return "Run2-2017-UL-NanoAODv15/";
    case 20180: return "Run2-2018-UL-NanoAODv15/";
    case 20220: return "Run3-22CDSep23-Summer22-NanoAODv12/";
    case 20221: return "Run3-22EFGSep23-Summer22EE-NanoAODv12/";
    case 20230: return "Run3-23CSep23-Summer23-NanoAODv12/";
    case 20231: return "Run3-23DSep23-Summer23BPix-NanoAODv12/";
    case 20240: return "Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15/";
    case 20250: return "Run3-25Prompt-Summer24-NanoAODv15/";
    default: return "Run3-26Prompt-Summer24-NanoAODv15/";
  }
}

struct TightIso {
  correction::Correction::Ref ref;
  bool ok = false;
};
inline TightIso& tight_iso() { static TightIso t; return t; }

inline void init_wzz_sf(int year) {
  const std::string name = year <= 20180 ? "NUM_TightRelIso_DEN_MediumPromptID" : "NUM_TightPFIso_DEN_MediumPromptID";
  try {
    auto cset = correction::CorrectionSet::from_file("jsonpog-integration/POG/MUO/" + pog_subdir(year) + "muon_Z.json.gz");
    tight_iso().ref = cset->at(name);
    tight_iso().ok = true;
  } catch (std::exception& e) {
    std::cout << "wzz_sf: no " << name << " for " << year << " (" << e.what() << "): V1 uses LooseIso SFs" << std::endl;
  }
}

inline double vary(double nom, double syst, double stat, int type) {
  return type == 0 ? nom : nom + type * std::sqrt(syst * syst + stat * stat);
}

// product over the variant's selected leptons (packed LEP_N); which = 0 both, 1 muons only,
// 2 electrons only (for the separate muon / electron SF nuisances)
inline float lepton_sf(int v, const RVec<float>& lep, int year, std::string ele_year, int type, int which) {
  double sf = 1.0;
  const int n = lep.size() / LEP_N;
  for (int i = 0; i < n; ++i) {
    const double pt = lep[i * LEP_N + L_PT], eta = lep[i * LEP_N + L_ETA], phi = lep[i * LEP_N + L_PHI];
    const bool mu = std::lround(lep[i * LEP_N + L_PDG]) == 13;
    const int t = ((mu && which != 2) || (!mu && which != 1)) ? type : 0;
    if (mu) {
      const double p = std::max(pt, 10.001);
      const double id = vary(corrSFs.eval_muonIDSF(eta, p, "nominal"), corrSFs.eval_muonIDSF(eta, p, "syst"),
                             corrSFs.eval_muonIDSF(eta, p, "stat"), t);
      double iso;
      if (v == 1 && tight_iso().ok) {
        // the framework's clamping (mysf.h eval_muonISOSF): pT >= 15.001 (Z-based SFs start at 15 GeV
        // before 2024), |eta| < 2.399, signed eta; above 200 GeV the high-pT SFs are not loaded here
        const double ec = std::max(std::min(eta, 2.399), -2.399);
        const double pc = std::min(std::max(pt, 15.001), 199.9);
        iso = vary(tight_iso().ref->evaluate({ec, pc, std::string("nominal")}), tight_iso().ref->evaluate({ec, pc, std::string("syst")}),
                   tight_iso().ref->evaluate({ec, pc, std::string("stat")}), t);
      } else {
        iso = vary(corrSFs.eval_muonISOSF(eta, p, "nominal"), corrSFs.eval_muonISOSF(eta, p, "syst"),
                   corrSFs.eval_muonISOSF(eta, p, "stat"), t);
      }
      sf *= id * iso;
    } else {
      const char* wp = v == 0 ? "wp80iso" : "wp90iso";
      double p = std::max(pt, 10.001);
      const char* reco = p < 20 ? "RecoBelow20" : (p < 75 ? "Reco20to75" : "RecoAbove75");
      if (year < 20210 && p >= 20) reco = "RecoAbove20";
      else if (year >= 20250 && p < 20) { reco = "Reco20to75"; p = 20.001; }
      const char* y = ele_year.c_str();
      const double rc = corrSFs.eval_electronTRKSF(y, t == 0 ? "sf" : (t > 0 ? "sfup" : "sfdown"), reco, eta, p, phi);
      const double id = corrSFs.eval_electronIDSF(y, t == 0 ? "sf" : (t > 0 ? "sfup" : "sfdown"), wp, eta, p, phi);
      sf *= rc * id;
    }
  }
  return sf;
}

}  // namespace wzz
