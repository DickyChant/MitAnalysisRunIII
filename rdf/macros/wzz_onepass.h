// One RDataFrame event loop for several years of the same MC files (wzzAnalysis --also): helpers.
//
// The framework draws its MC smearing from gRandom (JER of unmatched jets compute_JSON_JER_Unc, muon
// compute_MUOPT_Unc, electron compute_ELEPT_Unc). With two years' branches in one loop the draws would
// interleave, so the result would depend on the other branch (and, as before, on the job split).
// wzzAnalysis' branches therefore reseed gRandom before each such expression from (run, lumi, event,
// column): the smearing is a function of the event alone, identical in one-year and two-year runs and
// independent of the job split.
#pragma once
#include <cstdint>
#include "TRandom.h"

namespace wzz {

inline std::uint64_t splitmix64(std::uint64_t x) {
  x += 0x9E3779B97F4A7C15ULL;
  x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
  x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
  return x ^ (x >> 31);
}

// returns 0 so that it can open an RDataFrame expression
inline int reseed(unsigned int run, unsigned int lumi, unsigned long long event, unsigned int salt) {
  std::uint64_t h = splitmix64((static_cast<std::uint64_t>(run) << 32) ^ lumi);
  h = splitmix64(h ^ event);
  h = splitmix64(h ^ salt);
  gRandom->SetSeed(static_cast<ULong_t>(h % 4294967291ULL) + 1);   // TRandom3: 0 would mean a time seed
  return 0;
}

}  // namespace wzz
