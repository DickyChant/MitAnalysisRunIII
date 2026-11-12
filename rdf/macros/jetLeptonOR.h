#ifndef JETLEPTONOR_H
#define JETLEPTONOR_H

// Jet-lepton overlap variants for the ssWW nonprompt study (see utilsSelection.JET_LEPTON_OR).

#include <cmath>
#include <ROOT/RVec.hxx>

// ATLAS-style overlap removal (ATLAS ssWW, arXiv:2312.00420): a jet within dR < 0.2 of the lepton,
// or the lepton's own PF jet, is dropped as the lepton itself unless it is b-tagged (pT > 20) or carries
// >= 3 non-lepton constituents and > 20 GeV beyond the lepton; any other jet with pT > 20 GeV counts.
// A b tag only counts with > minHad GeV beyond the lepton: lepton-dominated jets often pass the b tag.
// The lepton is removed (0) if a surviving jet lies within dR < 0.4, kept (1) otherwise.
template <typename L, typename I, typename J, typename N>
ROOT::RVec<int> atlasLeptonJetOR(const L& lpt, const L& leta, const L& lphi, const I& ljetIdx,
                                 const J& jpt, const J& jeta, const J& jphi, const J& jrawFactor, const J& jbtag,
                                 const N& jnConst, const N& jnMu, const N& jnEl, float btagCut, float minHad) {
  ROOT::RVec<int> keep(lpt.size(), 1);
  for (unsigned int i = 0; i < lpt.size(); i++) {
    for (unsigned int j = 0; j < jpt.size(); j++) {
      float dPhi = std::fabs(lphi[i] - jphi[j]);
      if (dPhi > M_PI) dPhi = 2 * M_PI - dPhi;
      float dR = std::sqrt((leta[i] - jeta[j]) * (leta[i] - jeta[j]) + dPhi * dPhi);
      if (dR >= 0.4) continue;
      bool own = (int)ljetIdx[i] == (int)j;
      if (own || dR < 0.2) {
        float hadPt = jpt[j] - (own ? lpt[i] / std::max(1.0f - (float)jrawFactor[j], 0.1f) : 0.0f);
        int nHad = (int)jnConst[j] - (int)jnMu[j] - (int)jnEl[j];
        bool isB = std::fabs(jeta[j]) < 2.5 && jbtag[j] > btagCut && jpt[j] > 20 && hadPt > minHad;
        if (!isB && !(nHad >= 3 && hadPt > 20)) continue;
      } else if (jpt[j] <= 20) {
        continue;
      }
      keep[i] = 0;
      break;
    }
  }
  return keep;
}

// Number of b-tagged jets linked to fakeable leptons (removed by the jet cleaning) with > minHad GeV
// of hadronic pT beyond the linked lepton(s); jsel = pT > 20, |eta| < 2.5, jet ID and veto map.
template <typename L, typename I, typename J, typename M>
float lepJetBTags(const L& mpt, const I& midx, const L& ept, const I& eidx, const J& jpt, const J& jrawFactor,
                  const J& jbtag, const M& jsel, float btagCut, float minHad) {
  ROOT::RVec<float> lepPt(jpt.size(), 0.f);
  for (unsigned int i = 0; i < mpt.size(); i++) if (midx[i] >= 0 && midx[i] < (int)jpt.size()) lepPt[midx[i]] += mpt[i];
  for (unsigned int i = 0; i < ept.size(); i++) if (eidx[i] >= 0 && eidx[i] < (int)jpt.size()) lepPt[eidx[i]] += ept[i];
  float n = 0;
  for (unsigned int j = 0; j < jpt.size(); j++) {
    if (lepPt[j] <= 0 || !jsel[j] || jbtag[j] <= btagCut) continue;
    if (jpt[j] - lepPt[j] / std::max(1.0f - (float)jrawFactor[j], 0.1f) > minHad) n++;
  }
  return n;
}

#endif
