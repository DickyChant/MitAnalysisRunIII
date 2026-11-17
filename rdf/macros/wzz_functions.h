// WZZ analysis selection for the MitAnalysisRunIII framework (wzzAnalysis.py).
//
// C++ port of the reference Python implementation in the `wzz` package (leptonid.py,
// leptons.py, jets.py, regions.py, mode "opt"); tests/test_cpp_port.py checks event-by-
// event closure on cached NanoAOD events. Keep the two in sync: any selection change goes
// into both, and the closure test must pass.
//
//   merge_leptons(...)      Muon_* and Electron_* -> one flat "raw lepton" record
//   build_leptons(v, ...)   variant v (0..3 = V0..V3): loose leptons with level / cone pT,
//                           pT ordered, packed LEP_N floats per lepton
//   categorize(...)         channel, status, region, BDT features, failing leptons
//                           (packed into an RVec<float>, indices in enum Out)
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <numeric>
#include <vector>

#include "ROOT/RVec.hxx"

namespace wzz {
using ROOT::VecOps::RVec;
constexpr double MZ = 91.1876;
constexpr double INF = std::numeric_limits<double>::infinity();
enum Level { LOOSE = 0, FAKEABLE = 1, TIGHT = 2 };
enum Status { ST_NONE = 0, ST_SIGNAL = 1, ST_APPL = 2 };
enum Region {
  R3_INV = 0, R3_OUTV, R3_1J, R3_BOOST, R3_ZNUNU, R3_BB, R3_CRWZ, R3_CRTOP, R3_CRLOWMET2J, R3_CRCONV,
  R4_ZZJJ, R4_BOOST, R4_DF, R4_SFOFFZ, R4_CRZZ, R4_CRTTZ, R5_SR, N_REGIONS
};

// ------------------------------------------------------------------ kinematics
struct P4 { double px = 0, py = 0, pz = 0, e = 0; };
inline P4 p4(double pt, double eta, double phi, double m = 0.0) {
  P4 v; v.px = pt * std::cos(phi); v.py = pt * std::sin(phi); v.pz = pt * std::sinh(eta);
  v.e = std::sqrt(v.px * v.px + v.py * v.py + v.pz * v.pz + m * m); return v;
}
inline P4 operator+(const P4& a, const P4& b) { return {a.px + b.px, a.py + b.py, a.pz + b.pz, a.e + b.e}; }
inline double mass(const P4& v) { return std::sqrt(std::max(v.e * v.e - v.px * v.px - v.py * v.py - v.pz * v.pz, 0.0)); }
inline double ptof(const P4& v) { return std::hypot(v.px, v.py); }
inline double dphi(double a, double b) {
  double d = std::fmod(a - b + M_PI, 2 * M_PI); if (d < 0) d += 2 * M_PI; return d - M_PI;
}
inline double dr(double e1, double p1, double e2, double p2) { return std::hypot(e1 - e2, dphi(p1, p2)); }
inline double mt(double pt, double phi, double met, double metphi) {
  return std::sqrt(std::max(2.0 * pt * met * (1.0 - std::cos(dphi(phi, metphi))), 0.0));
}

// ------------------------------------------------------------------ leptons
// raw lepton record (one entry per muon/electron), same fields as nano.py broad=True
enum Raw { RW_PT, RW_ETA, RW_PHI, RW_PDG, RW_Q, RW_DXY, RW_DZ, RW_SIP, RW_JRI, RW_PFISO, RW_PMVA,
           RW_MULOOSE, RW_MUMEDPROMPT, RW_MUPFISOID, RW_ELCB, RW_ELWP90, RW_ELHZZ, RW_ELLOST, RW_ELCONV,
           RW_GEN, RW_N };
// packed variant lepton: pt, eta, phi, pdg, charge, level, cone pT, genPartFlav
enum Lep { L_PT, L_ETA, L_PHI, L_PDG, L_Q, L_LEVEL, L_CONE, L_GEN, LEP_N };

// HZZ electron ID (mvaEleID-Winter22-HZZ-V1) on the raw score, for v12 where NanoAOD has no WPHZZ
inline bool hzz_wp(double pt, double sceta, double score) {
  const double a = std::fabs(sceta);
  const int bin = a < 0.8 ? 0 : (a < 1.479 ? 1 : 2);
  static const double lo[3] = {1.633973689084034, 1.5499076306249353, 2.0629564440753247};
  static const double hi[3] = {0.3685228146685872, 0.2662407818935475, -0.5444837363886459};
  return score > (pt < 10 ? lo[bin] : hi[bin]);
}

// Muon_* / Electron_* -> flat raw record (RW_N floats per lepton; muons first). The
// acceptance of nano.py broad=True is applied here: |dxy| < 0.5, |dz| < 1, muons |eta| < 2.4,
// pT > 5 and looseId; electrons |eta| < 2.5, pT > 7.
template <typename B, typename U>
RVec<float> merge_leptons(
    const RVec<float>& mu_pt, const RVec<float>& mu_eta, const RVec<float>& mu_phi, const RVec<int>& mu_q,
    const RVec<float>& mu_dxy, const RVec<float>& mu_dz, const RVec<float>& mu_sip, const RVec<float>& mu_jri,
    const RVec<float>& mu_iso, const RVec<float>& mu_pmva, const RVec<B>& mu_loose, const RVec<B>& mu_medprompt,
    const RVec<U>& mu_pfisoid, const RVec<int>& mu_gen,
    const RVec<float>& el_pt, const RVec<float>& el_eta, const RVec<float>& el_phi, const RVec<int>& el_q,
    const RVec<float>& el_dxy, const RVec<float>& el_dz, const RVec<float>& el_sip, const RVec<float>& el_jri,
    const RVec<float>& el_iso, const RVec<float>& el_pmva, const RVec<U>& el_cb, const RVec<B>& el_wp90,
    const RVec<B>& el_hzz, const RVec<U>& el_lost, const RVec<B>& el_conv, const RVec<int>& el_gen) {
  RVec<float> out;
  out.reserve((mu_pt.size() + el_pt.size()) * RW_N);
  for (size_t i = 0; i < mu_pt.size(); ++i) {
    if (!(std::fabs(mu_eta[i]) < 2.4 && mu_pt[i] > 5 && mu_loose[i] && std::fabs(mu_dxy[i]) < 0.5 && std::fabs(mu_dz[i]) < 1.0)) continue;
    const float r[RW_N] = {mu_pt[i], mu_eta[i], mu_phi[i], 13.f, (float)mu_q[i], mu_dxy[i], mu_dz[i], mu_sip[i], mu_jri[i],
                           mu_iso[i], mu_pmva[i], 1.f, (float)mu_medprompt[i], (float)mu_pfisoid[i], -1.f, 0.f, 0.f, 0.f, 1.f,
                           (float)(mu_gen.empty() ? 0 : mu_gen[i])};
    out.insert(out.end(), r, r + RW_N);
  }
  for (size_t i = 0; i < el_pt.size(); ++i) {
    if (!(std::fabs(el_eta[i]) < 2.5 && el_pt[i] > 7 && std::fabs(el_dxy[i]) < 0.5 && std::fabs(el_dz[i]) < 1.0)) continue;
    const float r[RW_N] = {el_pt[i], el_eta[i], el_phi[i], 11.f, (float)el_q[i], el_dxy[i], el_dz[i], el_sip[i], el_jri[i],
                           el_iso[i], el_pmva[i], 0.f, 0.f, 0.f, (float)el_cb[i], (float)el_wp90[i], (float)el_hzz[i],
                           (float)el_lost[i], (float)el_conv[i], (float)(el_gen.empty() ? 0 : el_gen[i])};
    out.insert(out.end(), r, r + RW_N);
  }
  return out;
}

struct VariantDef { float floor_mu, floor_el, iso_tight_mu; };
inline VariantDef variant_def(int v) {
  switch (v) {
    case 0: return {10.f, 10.f, 0.f};
    case 1: return {10.f, 10.f, 0.15f};
    case 2: return {10.f, 10.f, 0.25f};
    default: return {5.f, 7.f, 0.25f};
  }
}

// variant v: 0 framework (promptMVA), 1 POG (MediumPrompt+PF iso / MVA wp90iso), 2 HZZ-like,
// 3 HZZ-like with 5/7 GeV floors; nano_version 12, 15 or 152 (Run 2 UL v15): V0 thresholds
inline RVec<float> build_leptons(int v, int nano_version, const RVec<float>& raw) {
  const size_t n = raw.size() / RW_N;
  const VariantDef d = variant_def(v);
  std::vector<std::array<float, LEP_N>> leps;
  for (size_t k = 0; k < n; ++k) {
    const float* r = &raw[k * RW_N];
    const bool mu = std::lround(r[RW_PDG]) == 13, el = !mu;
    const float pt = r[RW_PT];
    const bool ip_tight = std::fabs(r[RW_DXY]) < 0.05 && std::fabs(r[RW_DZ]) < 0.1;
    const bool ip_loose = std::fabs(r[RW_DXY]) < 0.5 && std::fabs(r[RW_DZ]) < 1.0;
    bool loose = false, fake = false, tight = false;
    float cone = pt;
    if (v == 0) {
      loose = ip_loose && ((mu && r[RW_MULOOSE] > 0) || (el && r[RW_ELCB] >= 1));
      if (mu) fake = ip_tight && r[RW_MUMEDPROMPT] > 0 && r[RW_MUPFISOID] >= 1 && r[RW_JRI] < 0.5 && pt > 10;
      else fake = ip_tight && r[RW_ELCB] >= 2 && r[RW_JRI] < 0.5 && pt > 10;
      // framework TIGHT_MU8 / TIGHT_EL8: v12 (2022-23) 0.7 / 0.0 (mvaTTH), v15 Run 3 0.7 / 0.8,
      // Run 2 UL v15 (lepton set 152, nano_version = 152) 0.0 / 0.05
      const float tmu = nano_version == 152 ? 0.0f : 0.7f;
      const float tel = nano_version == 152 ? 0.05f : (nano_version == 12 ? 0.0f : 0.8f);
      tight = fake && (mu ? r[RW_PMVA] > tmu : r[RW_PMVA] > tel);
      cone = tight ? pt : 0.9f * pt * (1.0f + r[RW_JRI]);
    } else {
      if (v == 1) {
        loose = ip_loose && ((mu && r[RW_MULOOSE] > 0) || (el && r[RW_ELCB] >= 1));
        if (mu) fake = r[RW_MUMEDPROMPT] > 0 && ip_tight && r[RW_PFISO] < 0.4;
        else fake = r[RW_ELCB] >= 1 && ip_tight && r[RW_PFISO] < 0.4 && r[RW_ELLOST] <= 1 && r[RW_ELCONV] > 0;
        tight = fake && (mu ? r[RW_PFISO] < d.iso_tight_mu : r[RW_ELWP90] > 0);
      } else {
        loose = ip_loose && ((mu && r[RW_MULOOSE] > 0) || el);
        fake = loose && r[RW_SIP] < 4;
        tight = fake && (mu ? (r[RW_MUMEDPROMPT] > 0 && r[RW_PFISO] < d.iso_tight_mu) : r[RW_ELHZZ] > 0);
      }
      const float excess = mu ? std::max(r[RW_PFISO] - d.iso_tight_mu, 0.0f) : 0.0f;
      cone = tight ? pt : pt * (1.0f + excess);
    }
    loose = loose && pt > (mu ? d.floor_mu : d.floor_el);
    if (!loose) continue;
    fake = fake && loose;
    tight = tight && fake;
    const int level = tight ? TIGHT : (fake ? FAKEABLE : LOOSE);
    leps.push_back({pt, r[RW_ETA], r[RW_PHI], r[RW_PDG], r[RW_Q], (float)level, cone, r[RW_GEN]});
  }
  std::stable_sort(leps.begin(), leps.end(), [](const auto& a, const auto& b) { return a[L_PT] > b[L_PT]; });
  RVec<float> out;
  out.reserve(leps.size() * LEP_N);
  for (auto& l : leps) out.insert(out.end(), l.begin(), l.end());
  return out;
}

// ------------------------------------------------------------------ configuration
struct Config {
  float floor_mu = 10, floor_el = 10;
  std::vector<float> pt3{25, 15, 10}, pt4{25, 15, 10, 10}, pt5{25, 15, 10, 10, 10};
  float mll_low = 12, z_window = 15, z5_window = 20;   // z5_window < 0: no window
  float met_cut = 30, met_znunu = 150, mbb_lo = 60, mbb_hi = 110, pair_target = 85;
  float inv_lo = 60, inv_hi = 110, boost_ptmin = 200, boost_msd_lo = 65, boost_msd_hi = 120, boost_score = 0.9f;
  float met_4l_wwz = 10, conv_m3l_window = 15, conv_met_max = 30, met_5l = 20;   // met_5l < 0: no cut
  int z_wp = TIGHT, w_wp = TIGHT, w5_wp = TIGHT, z5_wp = TIGHT;
  float btag_medium = 0.1272f;
};
// variant 3 lowers the 4th/5th lepton thresholds and the floors (leptonid.config_changes)
inline Config config_for(int v, float btag_medium) {
  Config c; const VariantDef d = variant_def(v);
  c.floor_mu = d.floor_mu; c.floor_el = d.floor_el; c.btag_medium = btag_medium;
  if (v == 3) { c.pt4 = {25, 15, 10, 7}; c.pt5 = {25, 15, 10, 7, 7}; }
  return c;
}

// ------------------------------------------------------------------ output layout
enum Out {
  O_CHANNEL, O_STATUS, O_REGION, O_NFAIL, O_TRUTH,
  O_MJJ, O_PTJJ, O_DRJJ, O_NJETS, O_NB, O_HT, O_MBB, O_MET, O_METSIG, O_VTAG, O_BOOSTED,
  O_MZ1, O_MZ2, O_M3L, O_M4L, O_LPT1, O_LPT2, O_LPT3, O_MTW, O_PTZ, O_QW, O_PTLW, O_PT4L, O_DF,
  O_J1B, O_J1CVL, O_J1CVB, O_J1QG, O_J2B, O_J2CVL, O_J2CVB, O_J2QG,
  O_F1PDG, O_F1CONE, O_F1ETA, O_F1REQ, O_F2PDG, O_F2CONE, O_F2ETA, O_F2REQ,   // first two failing leptons
  O_N
};

// jets: preselected by the caller (pT > 20, |eta| < 4.7, jet ID / veto map); tagger scores
// of the era's tagger. fatjets: pT > 170, vtag = max(W, Z vs QCD).
inline RVec<float> categorize(const RVec<float>& lep, const RVec<float>& j_pt, const RVec<float>& j_eta,
                              const RVec<float>& j_phi, const RVec<float>& j_mass, const RVec<float>& j_b,
                              const RVec<float>& j_cvl, const RVec<float>& j_cvb, const RVec<float>& j_qg,
                              const RVec<float>& fj_pt, const RVec<float>& fj_eta, const RVec<float>& fj_phi,
                              const RVec<float>& fj_msd, const RVec<float>& fj_vtag,
                              float met, float metphi, float metsig, const Config& cfg) {
  RVec<float> o(O_N, -1.f);
  o[O_CHANNEL] = 0; o[O_STATUS] = ST_NONE; o[O_NFAIL] = 0; o[O_BOOSTED] = 0;
  const int n = lep.size() / LEP_N;
  if (n < 3 || n > 5) return o;
  auto L = [&](int i, int f) { return lep[i * LEP_N + f]; };
  std::vector<P4> v(n);
  for (int i = 0; i < n; ++i) v[i] = p4(L(i, L_PT), L(i, L_ETA), L(i, L_PHI));
  auto pm = [&](int i, int j) { return mass(v[i] + v[j]); };
  auto ossf = [&](int i, int j) {
    return std::lround(L(i, L_PDG)) == std::lround(L(j, L_PDG)) && std::lround(L(i, L_Q)) != std::lround(L(j, L_Q));
  };

  // --- common: jets, tags, lepton-level cuts
  std::vector<int> jidx;
  for (size_t k = 0; k < j_pt.size(); ++k) {
    bool clean = true;
    for (int i = 0; i < n; ++i) if (!(dr(j_eta[k], j_phi[k], L(i, L_ETA), L(i, L_PHI)) > 0.4)) { clean = false; break; }
    if (clean) jidx.push_back(k);
  }
  std::stable_sort(jidx.begin(), jidx.end(), [&](int a, int b) { return j_pt[a] > j_pt[b]; });
  auto fwd = [&](int k, double ptmin) {
    const double a = std::fabs(j_eta[k]);
    return j_pt[k] > ptmin && a < 4.7 && !(a > 2.5 && a < 3.0 && j_pt[k] < 50.0);
  };
  std::vector<int> j30, j20;
  for (int k : jidx) { if (fwd(k, 30)) j30.push_back(k); if (fwd(k, 20)) j20.push_back(k); }
  int nb = 0; double ht = 0;
  for (int k : j20) if (std::fabs(j_eta[k]) < 2.5 && j_b[k] > cfg.btag_medium) ++nb;
  for (int k : j30) ht += j_pt[k];
  double mbb = -1;
  {
    std::vector<int> c;
    for (int k : j20) if (std::fabs(j_eta[k]) < 2.5) c.push_back(k);
    std::stable_sort(c.begin(), c.end(), [&](int a, int b) { return j_b[a] > j_b[b]; });
    if (c.size() >= 2) mbb = mass(p4(j_pt[c[0]], j_eta[c[0]], j_phi[c[0]], j_mass[c[0]]) + p4(j_pt[c[1]], j_eta[c[1]], j_phi[c[1]], j_mass[c[1]]));
  }
  // hadronic V candidate: pair of the leading <= 6 central Jet30 with mass closest to target
  std::vector<int> cj;
  for (int k : j30) if (std::fabs(j_eta[k]) < 2.5 && cj.size() < 6) cj.push_back(k);
  const bool has_pair = cj.size() >= 2;
  if (has_pair) {
    double best = INF; int ba = -1, bb = -1;
    for (size_t a = 0; a < cj.size(); ++a)
      for (size_t b = a + 1; b < cj.size(); ++b) {
        const double m = mass(p4(j_pt[cj[a]], j_eta[cj[a]], j_phi[cj[a]], j_mass[cj[a]]) + p4(j_pt[cj[b]], j_eta[cj[b]], j_phi[cj[b]], j_mass[cj[b]]));
        if (std::fabs(m - cfg.pair_target) < best) { best = std::fabs(m - cfg.pair_target); ba = cj[a]; bb = cj[b]; }
      }
    const P4 s = p4(j_pt[ba], j_eta[ba], j_phi[ba], j_mass[ba]) + p4(j_pt[bb], j_eta[bb], j_phi[bb], j_mass[bb]);
    o[O_MJJ] = mass(s); o[O_PTJJ] = ptof(s); o[O_DRJJ] = dr(j_eta[ba], j_phi[ba], j_eta[bb], j_phi[bb]);
    o[O_J1B] = j_b[ba]; o[O_J1CVL] = j_cvl[ba]; o[O_J1CVB] = j_cvb[ba]; o[O_J1QG] = j_qg.empty() ? -1 : j_qg[ba];
    o[O_J2B] = j_b[bb]; o[O_J2CVL] = j_cvl[bb]; o[O_J2CVB] = j_cvb[bb]; o[O_J2QG] = j_qg.empty() ? -1 : j_qg[bb];
  }
  // boosted V: leading AK8 (pT > ptmin, |eta| < 2.4, dR > 0.8 from all leptons)
  bool boosted = false; double vtag = -1;
  {
    int lead = -1;
    for (size_t k = 0; k < fj_pt.size(); ++k) {
      if (!(fj_pt[k] > cfg.boost_ptmin && std::fabs(fj_eta[k]) < 2.4)) continue;
      bool clean = true;
      for (int i = 0; i < n; ++i) if (!(dr(fj_eta[k], fj_phi[k], L(i, L_ETA), L(i, L_PHI)) > 0.8)) { clean = false; break; }
      if (clean && (lead < 0 || fj_pt[k] > fj_pt[lead])) lead = k;
    }
    if (lead >= 0) {
      vtag = fj_vtag[lead];
      boosted = fj_msd[lead] > cfg.boost_msd_lo && fj_msd[lead] < cfg.boost_msd_hi && fj_vtag[lead] > cfg.boost_score;
    }
  }
  const std::vector<float>& cuts = n == 3 ? cfg.pt3 : (n == 4 ? cfg.pt4 : cfg.pt5);
  bool ptok = true;
  for (int k = 0; k < n; ++k) ptok = ptok && L(k, L_PT) > cuts[std::min<size_t>(k, cuts.size() - 1)];
  bool lowm = false;
  for (int i = 0; i < n; ++i) for (int j = i + 1; j < n; ++j) if (ossf(i, j) && pm(i, j) < cfg.mll_low) lowm = true;
  const bool lep_ok = ptok && !lowm;
  int q = 0;
  for (int i = 0; i < n; ++i) q += std::lround(L(i, L_Q));
  P4 all; for (auto& x : v) all = all + x;
  const double mall = mass(all);
  const int njets = j30.size();

  o[O_CHANNEL] = n; o[O_NJETS] = njets; o[O_NB] = nb; o[O_HT] = ht; o[O_MBB] = mbb; o[O_MET] = met;
  o[O_METSIG] = metsig; o[O_VTAG] = vtag; o[O_BOOSTED] = boosted;
  o[O_LPT1] = L(0, L_PT); o[O_LPT2] = L(1, L_PT); o[O_LPT3] = L(2, L_PT);

  // best single OSSF pair closest to MZ (first minimum in (i<j) order)
  auto single = [&](int& bi, int& bj, double& bm, bool& valid) {
    double best = INF; bi = 0; bj = 1; valid = false;
    for (int i = 0; i < n; ++i) for (int j = i + 1; j < n; ++j) {
      const double d = ossf(i, j) ? std::fabs(pm(i, j) - MZ) : INF;
      if (d < best) { best = d; bi = i; bj = j; valid = true; }
    }
    bm = pm(bi, bj);
  };
  // two disjoint OSSF pairs, lexicographic (smaller |m - MZ| first, then the larger)
  auto two = [&](int& z1a, int& z1b, int& z2a, int& z2b, int& w, double& m1, double& m2, bool& valid) {
    std::vector<std::array<int, 5>> cands;
    if (n == 4) cands = {{0, 1, 2, 3, -1}, {0, 2, 1, 3, -1}, {0, 3, 1, 2, -1}};
    else for (int ww = 0; ww < 5; ++ww) {
      int r[4], t = 0; for (int x = 0; x < 5; ++x) if (x != ww) r[t++] = x;
      cands.push_back({r[0], r[1], r[2], r[3], ww}); cands.push_back({r[0], r[2], r[1], r[3], ww});
      cands.push_back({r[0], r[3], r[1], r[2], ww});
    }
    double bp = INF, bs = INF; int bk = 0;
    for (size_t k = 0; k < cands.size(); ++k) {
      const auto& c = cands[k];
      const bool ok = ossf(c[0], c[1]) && ossf(c[2], c[3]);
      const double da = std::fabs(pm(c[0], c[1]) - MZ), db = std::fabs(pm(c[2], c[3]) - MZ);
      const double p = ok ? std::min(da, db) : INF, s = ok ? std::max(da, db) : INF;
      if (p < bp || (p == bp && s < bs)) { bp = p; bs = s; bk = k; }
    }
    const auto& c = cands[bk];
    const double ma = pm(c[0], c[1]), mb = pm(c[2], c[3]);
    const bool afirst = std::fabs(ma - MZ) <= std::fabs(mb - MZ);
    z1a = afirst ? c[0] : c[2]; z1b = afirst ? c[1] : c[3]; z2a = afirst ? c[2] : c[0]; z2b = afirst ? c[3] : c[1];
    w = c[4]; m1 = afirst ? ma : mb; m2 = afirst ? mb : ma; valid = std::isfinite(bp);
  };

  int reg = -1;
  std::vector<int> req(n, cfg.w_wp);
  if (n == 3) {
    int zi, zj; double zm; bool zv; single(zi, zj, zm, zv);
    const int w = 3 - zi - zj;
    const bool onz = zv && std::fabs(zm - MZ) < cfg.z_window;
    const bool base = lep_ok && std::abs(q) == 1, mainz = base && onz;
    const bool bbr = nb >= 2 && mbb > cfg.mbb_lo && mbb < cfg.mbb_hi;
    const bool btag = mainz && nb >= 1 && met > cfg.met_cut;
    const bool veto = mainz && nb == 0, hi = veto && met > cfg.met_cut, lo = veto && met <= cfg.met_cut;
    const bool znunu = njets < 2 && met > cfg.met_znunu;
    const bool conv = base && zv && !onz && nb == 0 && met < cfg.conv_met_max && std::fabs(mall - MZ) < cfg.conv_m3l_window;
    const bool inv = o[O_MJJ] > cfg.inv_lo && o[O_MJJ] < cfg.inv_hi;
    if (btag && bbr) reg = R3_BB; else if (btag) reg = R3_CRTOP;
    else if (hi && boosted) reg = R3_BOOST; else if (hi && has_pair && inv) reg = R3_INV;
    else if (hi && has_pair) reg = R3_OUTV; else if (hi && znunu) reg = R3_ZNUNU;
    else if (hi && njets == 1) reg = R3_1J; else if (hi) reg = R3_CRWZ;
    else if (lo && has_pair) reg = R3_CRLOWMET2J; else if (conv) reg = R3_CRCONV;
    req[zi] = cfg.z_wp; req[zj] = cfg.z_wp;
    o[O_MZ1] = zv ? zm : -1; o[O_M3L] = mall;
    o[O_MTW] = mt(L(w, L_PT), L(w, L_PHI), met, metphi); o[O_PTZ] = ptof(v[zi] + v[zj]);
    o[O_QW] = L(w, L_Q); o[O_PTLW] = L(w, L_PT);
  } else if (n == 4) {
    int a1, a2, b1, b2, ww; double m1, m2; bool tv; two(a1, a2, b1, b2, ww, m1, m2, tv);
    const bool base = lep_ok && q == 0;
    const int non = tv ? (std::fabs(m1 - MZ) < cfg.z_window) + (std::fabs(m2 - MZ) < cfg.z_window) : -1;
    const bool zz = base && tv && non == 2;
    int si, sj; double sm; bool sv; single(si, sj, sm, sv);
    int r0 = -1, r1 = -1;
    for (int x = 0; x < 4; ++x) if (x != si && x != sj) { if (r0 < 0) r0 = x; else r1 = x; }
    const bool z1 = base && !zz && sv && std::fabs(sm - MZ) < cfg.z_window;
    const bool df = std::lround(L(r0, L_PDG)) != std::lround(L(r1, L_PDG));
    const double mr = pm(r0, r1);
    const bool sf_off = !df && std::fabs(mr - MZ) >= cfg.z_window;
    if (zz && nb >= 1) reg = R4_CRTTZ; else if (zz && boosted) reg = R4_BOOST;
    else if (zz && has_pair) reg = R4_ZZJJ; else if (zz) reg = R4_CRZZ;
    else if (z1 && nb >= 1) reg = R4_CRTTZ; else if (z1 && met > cfg.met_4l_wwz && df) reg = R4_DF;
    else if (z1 && met > cfg.met_4l_wwz && sf_off) reg = R4_SFOFFZ;
    if (zz) std::fill(req.begin(), req.end(), cfg.z_wp);
    else { req[si] = cfg.z_wp; req[sj] = cfg.z_wp; }
    o[O_MZ1] = zz ? m1 : (sv ? sm : -1); o[O_MZ2] = zz ? m2 : (sv ? mr : -1);
    o[O_M4L] = mall; o[O_PT4L] = ptof(all); o[O_DF] = df;
  } else {
    int a1, a2, b1, b2, w; double m1, m2; bool tv; two(a1, a2, b1, b2, w, m1, m2, tv);
    bool ok = lep_ok && std::abs(q) == 1 && tv;
    if (cfg.z5_window >= 0) ok = ok && std::fabs(m1 - MZ) < cfg.z5_window && std::fabs(m2 - MZ) < cfg.z5_window;
    if (cfg.met_5l >= 0) ok = ok && met > cfg.met_5l;
    reg = ok ? R5_SR : -1;
    std::fill(req.begin(), req.end(), cfg.z5_wp);
    req[w] = cfg.w5_wp;
    o[O_MZ1] = m1; o[O_MZ2] = m2;
    o[O_MTW] = mt(L(w, L_PT), L(w, L_PHI), met, metphi); o[O_PTLW] = L(w, L_PT); o[O_QW] = L(w, L_Q);
  }
  // status and failing leptons
  bool sig = true, appl_ok = true, anyfail = false;
  int nf = 0;
  for (int i = 0; i < n; ++i) {
    const int lvl = std::lround(L(i, L_LEVEL));
    sig = sig && lvl >= req[i];
    appl_ok = appl_ok && lvl >= req[i] - 1;
    if (lvl < req[i]) {
      anyfail = true;
      if (nf < 2) {
        const int b = nf == 0 ? O_F1PDG : O_F2PDG;
        o[b] = L(i, L_PDG); o[b + 1] = L(i, L_CONE); o[b + 2] = std::fabs(L(i, L_ETA)); o[b + 3] = req[i];
      }
      ++nf;
    }
  }
  const int st = sig ? ST_SIGNAL : ((appl_ok && anyfail) ? ST_APPL : ST_NONE);
  o[O_STATUS] = st; o[O_REGION] = st != ST_NONE ? reg : -1; o[O_NFAIL] = nf;
  bool all_prompt = true, all_pc = true;
  for (int i = 0; i < n; ++i) {
    const int g = std::lround(L(i, L_GEN));
    const bool pr = g == 1 || g == 15;
    all_prompt = all_prompt && pr; all_pc = all_pc && (pr || g == 22);
  }
  o[O_TRUTH] = all_prompt ? 0 : (all_pc ? 1 : 2);
  return o;
}

// ------------------------------------------------------------------ fake rates
// Fake-rate bins (frmeasure.BINS): map T = tight vs fakeable, F = fakeable vs loose; per
// flavour cone-pT x |eta| edges. fr_index -> one flat index (45 bins) for the nonprompt
// histograms, which are filled per failing-lepton bin and weighted by f/(1-f) at harvest.
struct FRBins { int map, pdg; std::vector<double> pt, eta; };
inline const std::vector<FRBins>& fr_bins() {
  static const std::vector<FRBins> b = {
    {TIGHT, 11, {10, 15, 20, 30, 45, 200}, {0, 0.8, 1.479, 2.5}},
    {TIGHT, 13, {10, 15, 20, 30, 45, 200}, {0, 1.2, 2.4}},
    {FAKEABLE, 11, {7, 10, 15, 20, 30, 200}, {0, 1.479, 2.5}},
    {FAKEABLE, 13, {5, 10, 15, 20, 30, 200}, {0, 1.2, 2.4}}};
  return b;
}
inline int fr_nbins() { int n = 0; for (auto& b : fr_bins()) n += (b.pt.size() - 1) * (b.eta.size() - 1); return n; }
// required level -> map (T if the lepton had to be tight, F if fakeable); below the first pT
// edge -> -1 (cannot pass, frmeasure drops those probes); above the last -> last bin
inline int fr_index(int req, int pdg, double conept, double abseta) {
  int off = 0;
  for (auto& b : fr_bins()) {
    const int npt = b.pt.size() - 1, neta = b.eta.size() - 1;
    if (b.map == req && b.pdg == std::abs(pdg)) {
      if (conept < b.pt[0]) return -1;
      int ip = npt - 1; for (int i = 0; i < npt; ++i) if (conept < b.pt[i + 1]) { ip = i; break; }
      int ie = neta - 1; for (int i = 0; i < neta; ++i) if (abseta < b.eta[i + 1]) { ie = i; break; }
      return off + ip * neta + ie;
    }
    off += npt * neta;
  }
  return -1;
}
// nonprompt index of an application-region event: single failing lepton -> its bin k
// (0..N-1); two -> N + upper-triangle index of (min(k1,k2), max(k1,k2)), i.e.
// N + k1*N - k1*(k1-1)/2 + (k2-k1); total np_nbins() = N + N(N+1)/2; otherwise -> -1
inline int np_index(const RVec<float>& o) {
  const int nf = std::lround(o[O_NFAIL]), N = fr_nbins();
  if (std::lround(o[O_STATUS]) != ST_APPL || nf < 1 || nf > 2) return -1;
  const int k1 = fr_index(std::lround(o[O_F1REQ]), std::lround(o[O_F1PDG]), o[O_F1CONE], o[O_F1ETA]);
  if (k1 < 0) return -1;
  if (nf == 1) return k1;
  const int k2 = fr_index(std::lround(o[O_F2REQ]), std::lround(o[O_F2PDG]), o[O_F2CONE], o[O_F2ETA]);
  if (k2 < 0) return -1;
  const int a = std::min(k1, k2), b = std::max(k1, k2);
  return N + a * N - a * (a - 1) / 2 + (b - a);
}
inline int np_nbins() { const int N = fr_nbins(); return N + N * (N + 1) / 2; }

// Z+L probe (frmeasure.zl_probes): exactly 3 leptons, two TIGHT forming the OSSF pair
// closest to MZ within z_window, MET < met_max, m_T(probe) < mt_max, no b tag (nb from
// categorize). Returns {pdg, cone pT, |eta|, level} or empty.
inline RVec<float> zl_probe(const RVec<float>& lep, const RVec<float>& o, float metphi,
                            float z_window = 15, float met_max = 30, float mt_max = 30) {
  if (lep.size() / LEP_N != 3 || std::lround(o[O_CHANNEL]) != 3) return {};
  auto L = [&](int i, int f) { return lep[i * LEP_N + f]; };
  double best = INF; int probe = -1;
  const int pairs[3][3] = {{0, 1, 2}, {0, 2, 1}, {1, 2, 0}};
  for (auto& p : pairs) {
    const int i = p[0], j = p[1];
    const bool ok = std::lround(L(i, L_PDG)) == std::lround(L(j, L_PDG)) && std::lround(L(i, L_Q)) != std::lround(L(j, L_Q))
                    && std::lround(L(i, L_LEVEL)) == TIGHT && std::lround(L(j, L_LEVEL)) == TIGHT;
    if (!ok) continue;
    const double d = std::fabs(mass(p4(L(i, L_PT), L(i, L_ETA), L(i, L_PHI)) + p4(L(j, L_PT), L(j, L_ETA), L(j, L_PHI))) - MZ);
    if (d < best) { best = d; probe = p[2]; }
  }
  if (probe < 0 || !(best < z_window)) return {};
  const float met = o[O_MET];
  if (!(met < met_max) || !(mt(L(probe, L_PT), L(probe, L_PHI), met, metphi) < mt_max) || o[O_NB] != 0) return {};
  return {L(probe, L_PDG), L(probe, L_CONE), std::fabs(L(probe, L_ETA)), L(probe, L_LEVEL)};
}

// ------------------------------------------------------------------ generator-level VH
// (production, H decay) codes as config.processes VH_PROD / H_DECAY: prod 0 none, 1 WH, 2 ZH;
// decay 0 none, 1 WW, 2 ZZ, 3 tautau, 4 other. Last-copy H (statusFlags bit 13); associated
// hard-process (bit 7) W/Z not from the H.
template <typename P, typename M, typename F>
RVec<int> gen_vh(const RVec<P>& pdg, const RVec<M>& mom, const RVec<F>& flags) {
  int h = -1;
  for (size_t i = 0; i < pdg.size(); ++i) if (pdg[i] == 25 && ((flags[i] >> 13) & 1)) { h = i; break; }
  if (h < 0) return {0, 0};
  int decay = 4; bool w = false, z = false, tau = false;
  for (size_t i = 0; i < pdg.size(); ++i) if (mom[i] == h) {
    const int a = std::abs(pdg[i]);
    if (a == 24) w = true; else if (a == 23) z = true; else if (a == 15) tau = true;
  }
  decay = w ? 1 : (z ? 2 : (tau ? 3 : 4));
  bool wa = false, za = false;
  for (size_t i = 0; i < pdg.size(); ++i) {
    if (!((flags[i] >> 7) & 1)) continue;
    const int mp = mom[i] >= 0 ? pdg[mom[i]] : 0;
    if (std::abs(mp) == 25 || mp == pdg[i]) continue;
    if (std::abs(pdg[i]) == 24) wa = true;
    if (pdg[i] == 23) za = true;
  }
  return {wa ? 1 : (za ? 2 : 0), decay};
}

// element-wise max (fat-jet V tag = max(W, Z vs QCD)); a helper because an RDF Define string
// containing "return" (e.g. a lambda) is taken as a whole function body
template <typename T>
RVec<float> vmax(const RVec<T>& a, const RVec<T>& b) {
  RVec<float> r(a.size());
  for (size_t i = 0; i < a.size(); ++i) r[i] = a[i] > b[i] ? a[i] : b[i];
  return r;
}

// ------------------------------------------------------------------ BDT inputs
// working-point categories (bdt.py): number of b WPs passed (L, M, T, XT), c-tag medium
inline int bcat(float s, const std::array<float, 4>& wps) {
  if (s < 0) return -1;
  int c = 0; for (float w : wps) c += s > w; return c;
}
// inputs in the order of bdt.FEATURES[3] / [4]; ctag = (CvL, CvB) medium cuts
inline RVec<float> bdt_inputs(const RVec<float>& o, int channel, const std::array<float, 4>& bwps,
                              const std::array<float, 2>& ctag, bool with_qg = true) {
  const bool has = o[O_J1B] >= 0;
  const float nct = has ? (float)((o[O_J1CVL] > ctag[0] && o[O_J1CVB] > ctag[1]) + (o[O_J2CVL] > ctag[0] && o[O_J2CVB] > ctag[1])) : -1.f;
  const float qmin = has ? std::min(o[O_J1QG], o[O_J2QG]) : -1.f, qmax = has ? std::max(o[O_J1QG], o[O_J2QG]) : -1.f;
  RVec<float> x;
  if (channel == 3)
    x = {o[O_MJJ], o[O_PTJJ], o[O_DRJJ], o[O_NJETS], o[O_HT], o[O_MET], o[O_METSIG], o[O_MTW], o[O_PTLW], o[O_QW], o[O_PTZ],
         o[O_M3L], o[O_LPT1], o[O_LPT2], o[O_LPT3], o[O_VTAG], o[O_NB], (float)bcat(o[O_J1B], bwps), (float)bcat(o[O_J2B], bwps), nct};
  else
    x = {o[O_MJJ], o[O_PTJJ], o[O_DRJJ], o[O_NJETS], o[O_HT], o[O_MET], o[O_MZ1], o[O_MZ2], o[O_M4L], o[O_PT4L],
         o[O_LPT1], o[O_LPT2], o[O_LPT3], o[O_VTAG], o[O_NB], (float)bcat(o[O_J1B], bwps), (float)bcat(o[O_J2B], bwps), nct};
  if (with_qg) { x.push_back(qmin); x.push_back(qmax); }
  return x;
}

}  // namespace wzz
