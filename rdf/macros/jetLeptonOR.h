#ifndef JETLEPTONOR_H
#define JETLEPTONOR_H

// Jet-lepton overlap variants for the ssWW nonprompt study (see utilsSelection.JET_LEPTON_OR).

#include <cmath>
#include <ROOT/RVec.hxx>

// ATLAS-style overlap removal (ATLAS ssWW, arXiv:2312.00420): a jet within dR < 0.2 of the lepton,
// or the lepton's own PF jet, is dropped as the lepton itself unless it is b-tagged (pT > 20) or carries
// >= 3 non-lepton constituents and > 20 GeV beyond the lepton; any other jet with pT > 20 GeV counts.
// The lepton is removed (0) if a surviving jet lies within dR < 0.4, kept (1) otherwise.
template <typename L, typename I, typename J, typename N>
ROOT::RVec<int> atlasLeptonJetOR(const L& lpt, const L& leta, const L& lphi, const I& ljetIdx,
                                 const J& jpt, const J& jeta, const J& jphi, const J& jrawFactor, const J& jbtag,
                                 const N& jnConst, const N& jnMu, const N& jnEl, float btagCut) {
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
        bool isB = std::fabs(jeta[j]) < 2.5 && jbtag[j] > btagCut && jpt[j] > 20;
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

#endif
