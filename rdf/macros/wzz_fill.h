// Fit-variable layout and BDT evaluation for wzzAnalysis (include after wzz_functions.h and
// the generated wzz_bdt.h). One flat "global bin" axis holds every region:
//   3l SRs (inV, outV, 1j, BOOST, ZNUNU, BB): 4 argmax classes x 5 P(WZZ) bins = 20 bins
//                                              (edges 0/0.15/0.25/0.35/0.45/1, score_bin)
//   4l SR ZZjj / BOOST:                        10 P(WZZ) bins
//   every other region (CRs, WWZ candle SRs, 5l): 1 bin
// The harvest (wvz: wzz/harvest.py) unpacks it with the same layout (FIT_LAYOUT there).
#pragma once
#include "wzz_functions.h"

namespace wzz {

inline int fit_nbins(int r) {
  if (r >= R3_INV && r <= R3_BB) return 20;
  if (r == R4_ZZJJ || r == R4_BOOST) return 10;
  return 1;
}
inline int fit_offset(int r) { int o = 0; for (int k = 0; k < r; ++k) o += fit_nbins(k); return o; }
inline int fit_total() { return fit_offset(N_REGIONS); }

// {P(WZZ), argmax class} for events in a BDT region, {-1, -1} otherwise. fold = event % 2:
// the model of fold k was trained on the other parity (bdt.py), so MC is out-of-fold.
inline RVec<float> bdt_scores(const RVec<float>& o, unsigned long long event,
                              const std::array<float, 4>& bwps, const std::array<float, 2>& ctag) {
  const int r = std::lround(o[O_REGION]);
  const int fold = event % 2;
  if (r >= R3_INV && r <= R3_BB) {
    RVec<float> x = bdt_inputs(o, 3, bwps, ctag);
    float p[4];
    wzz_bdt3l(fold, x.data(), p);
    int am = 0; for (int c = 1; c < 4; ++c) if (p[c] > p[am]) am = c;
    return {p[0], (float)am};
  }
  if (r == R4_ZZJJ || r == R4_BOOST) {
    RVec<float> x = bdt_inputs(o, 4, bwps, ctag);
    float p[1];
    wzz_bdt4l(fold, x.data(), p);
    return {p[0], 0.f};
  }
  return {-1.f, -1.f};
}

// P(WZZ) bin edges: 3l (class-balanced multiclass: WZZ peaks at 0.2-0.4) and 4l (binary)
inline int score_bin(float p, bool three) {
  static const float e3[6] = {0.f, 0.15f, 0.25f, 0.35f, 0.45f, 1.f};
  if (!three) return std::min(std::max((int)(p * 10), 0), 9);
  int b = 0; while (b < 4 && p >= e3[b + 1]) ++b; return b;
}
inline int global_bin(const RVec<float>& o, const RVec<float>& s) {
  const int r = std::lround(o[O_REGION]);
  if (r < 0) return -1;
  const int nb = fit_nbins(r);
  if (nb == 1) return fit_offset(r);
  const int sb = score_bin(s[0], nb == 20);
  return fit_offset(r) + (nb == 20 ? (int)std::lround(s[1]) * 5 + sb : sb);
}

// total JES shift: per jet, ptDef + sqrt(sum_k (ptJes_k - ptDef)^2) over the 28 sources (Up only,
// as the framework; symmetrised downstream)
inline RVec<float> jes_total_up(const RVec<float>& def, const std::vector<RVec<float>>& srcs) {
  RVec<float> out(def.size());
  for (size_t j = 0; j < def.size(); ++j) {
    double s2 = 0; for (auto& s : srcs) { const double d = s[j] - def[j]; s2 += d * d; }
    out[j] = def[j] + std::sqrt(s2);
  }
  return out;
}

}  // namespace wzz
