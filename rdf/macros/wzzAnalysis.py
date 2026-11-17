"""WZZ analysis for MitAnalysisRunIII: histograms only (one ROOT file per job).

    python3 wzzAnalysis.py --process=516 --year=20240 --whichJob=0   (from rdf/macros/)

Source of truth: the wvz repository (framework/). The selection is the C++ port
wzz_functions.h of the reference Python package (event-by-event closure in
tests/test_cpp_port.py); the BDT is the generated wzz_bdt.h (scripts/train_bdt.py).

Lepton-ID variants V0..V3 (wzz/leptonid.py) are parallel branches of one RDataFrame graph, so
the input is read once. Per variant, and per jet/MET variation ("", JesTotUp, JerUp, UnclUp):
  h_<v><jv>_<proc>        TH1D over the flat fit-bin axis (wzz_fill.h), signal-like events
                          proc = main | conv | vh<prod><decay> (VH samples split at generator level)
  h_<v>_<proc>_<wvar>     the same for weight variations (nominal jets): PU, b tag, lepton SFs,
                          QCD scale, PS, L1 prefiring
  np_<v>                  TH2D fit bin x nonprompt index (wzz_functions.h np_index) of
                          application-region events: data (weight 1) or prompt MC (subtraction)
  fr_<v>_{num,den}        TH1D over the flat fake-rate index: Z+L probes (data; prompt MC)
  h_<v>_data              data, signal-like events in control regions only (SRs stay blind)
  hJobNorm                per-job normalisation (1/weight in bin 1), for the weighted harvest
MC weight: xs*lumi/sum(genWeight of this job's files) * genWeight * PU * L1 prefire (Run 2)
* b-tag SF (medium) * per-variant lepton SF (wzz_sf.h). Data: PD trigger logic, golden JSON,
MET filters. Signal-region data are never filled.
"""
import ROOT
import getopt
import json
import os
import sys

ROOT.ROOT.EnableImplicitMT(4)
from utilsAna import getMClist, getMCnormList, getDATAlist, readRunsSums  # noqa: E402
from utilsAna import SwitchSample, groupFiles, getTriggerFromJson, getLeptomSelFromJson, getLumi  # noqa: E402
from utilsSelection import selectionTrigger2L, selectionElMu, selectionJetMet, selectionTheoryWeigths, getBTagCut  # noqa: E402
from utilsNanoAOD import prepareWZNanoAOD, hasLegacyLeptonMVA, pruneWZTrigger, setTriggerFiles  # noqa: E402

for h in ("wzz_functions.h", "wzz_bdt.h", "wzz_fill.h", "wzz_sf.h"):
    if not ROOT.gInterpreter.Declare('#include "{0}"'.format(h)):
        raise RuntimeError("cannot declare " + h)

VARIANTS = [0, 1, 2, 3]
_keep = []                     # ROOT objects that must outlive analysis()
JETVARS = ["", "JesTotUp", "JerUp", "UnclUp"]
BTAGSEL = 1                    # medium (framework: 0 = T, 1 = M, 2 = L)
FILL_DATA_SR = os.environ.get("WZZ_UNBLIND", "0") == "1"   # never set for the blinded analysis
CR_REGIONS = ("R3_CRWZ", "R3_CRTOP", "R3_CRLOWMET2J", "R3_CRCONV", "R4_CRZZ", "R4_CRTTZ")

with open("config/selection.json" if os.path.exists("config/selection.json") else "selection.json") as f:
    SELJSON = json.load(f)

# b and c working points of the era's tagger (wzz/bdt.py BTAG_WPS / CTAG_M)
BWPS = {20160: (0.0387, 0.1847, 0.5467, 0.6777), 20161: (0.04, 0.1898, 0.5538, 0.6872),
        20170: (0.0331, 0.1776, 0.5755, 0.7274), 20180: (0.0308, 0.161, 0.5405, 0.6992),
        20220: (0.0849, 0.4319, 0.8482, 0.9151), 20221: (0.0897, 0.451, 0.8604, 0.9234),
        20230: (0.0681, 0.3487, 0.7969, 0.8882), 20231: (0.0683, 0.3494, 0.7994, 0.8877),
        20240: (0.0246, 0.1272, 0.4648, 0.6298), 20250: (0.0246, 0.1272, 0.4648, 0.6298),
        20260: (0.0246, 0.1272, 0.4648, 0.6298), 20261: (0.0246, 0.1272, 0.4648, 0.6298)}
CTAG = {20220: (0.117, 0.13), 20221: (0.117, 0.128), 20230: (0.109, 0.153), 20231: (0.11, 0.157)}
ELEYEAR = {20160: "2016preVFP", 20161: "2016postVFP", 20170: "2017", 20180: "2018", 20220: "2022Re-recoBCD",
           20221: "2022Re-recoE+PromptFG", 20230: "2023PromptC", 20231: "2023PromptD", 20240: "2024Prompt",
           20250: "2025Prompt", 20260: "2025Prompt", 20261: "2025Prompt"}


def nano_version(year):
    """12 = NanoAOD v12 (2022-23), 15 = v15 Run 3, 152 = Run 2 UL v15 (framework lepton set 152)."""
    if year <= 20180:
        return 152
    return 12 if year < 20240 else 15


def tagger(year):
    return "RobustParTAK4" if 20220 <= year < 20240 else "UParTAK4"


def met_filters(year):
    y = year // 10 if year > 10000 else year
    for m in SELJSON.get("met_filters", []):
        if m.get("year") == y:
            return m["definition"]
    return None


def define_inputs(df, year, isData):
    """Raw lepton record, jets with the extra tagger outputs, fat jets, jet/MET variations."""
    v = nano_version(year)
    mva = "promptMVA" if v != 12 else "mvaTTH"
    b = tagger(year)
    qg = "QG" if b == "RobustParTAK4" else "QvG"
    gen = "Muon_genPartFlav", "Electron_genPartFlav"
    if isData == "true":
        df = df.Define("wzz_mu_gen", "ROOT::RVec<int>()").Define("wzz_el_gen", "ROOT::RVec<int>()")
    else:
        df = (df.Define("wzz_mu_gen", "ROOT::RVec<int>({0}.begin(), {0}.end())".format(gen[0]))
                .Define("wzz_el_gen", "ROOT::RVec<int>({0}.begin(), {0}.end())".format(gen[1])))
    el_hzz = ("Electron_mvaIso_WPHZZ" if df.HasColumn("Electron_mvaIso_WPHZZ") else
              "wzz_el_hzz_from_score")
    if el_hzz != "Electron_mvaIso_WPHZZ":
        df = df.Define(el_hzz, "ROOT::RVec<bool> r(Electron_pt.size()); for (size_t i = 0; i < r.size(); ++i) "
                               "r[i] = wzz::hzz_wp(Electron_pt[i], Electron_eta[i] + Electron_deltaEtaSC[i], Electron_mvaHZZIso[i]); return r;")
    df = df.Define("wzz_raw", (
        "wzz::merge_leptons(Muon_pt, Muon_eta, Muon_phi, ROOT::RVec<int>(Muon_charge.begin(), Muon_charge.end()), "
        "Muon_dxy, Muon_dz, Muon_sip3d, Muon_jetRelIso, Muon_pfRelIso04_all, Muon_{mva}, "
        "ROOT::RVec<bool>(Muon_looseId.begin(), Muon_looseId.end()), ROOT::RVec<bool>(Muon_mediumPromptId.begin(), Muon_mediumPromptId.end()), "
        "ROOT::RVec<int>(Muon_pfIsoId.begin(), Muon_pfIsoId.end()), wzz_mu_gen, "
        "Electron_pt, Electron_eta, Electron_phi, ROOT::RVec<int>(Electron_charge.begin(), Electron_charge.end()), "
        "Electron_dxy, Electron_dz, Electron_sip3d, Electron_jetRelIso, Electron_pfRelIso03_all, Electron_{mva}, "
        "ROOT::RVec<int>(Electron_cutBased.begin(), Electron_cutBased.end()), "
        "ROOT::RVec<bool>(Electron_mvaIso_WP90.begin(), Electron_mvaIso_WP90.end()), "
        "ROOT::RVec<bool>({hzz}.begin(), {hzz}.end()), ROOT::RVec<int>(Electron_lostHits.begin(), Electron_lostHits.end()), "
        "ROOT::RVec<bool>(Electron_convVeto.begin(), Electron_convVeto.end()), wzz_el_gen)").format(mva=mva, hzz=el_hzz))
    df = df.Filter("wzz_raw.size() >= 3 * wzz::RW_N", ">= 3 leptons (broad loose)")
    # jets: framework-cleaned (jet ID, veto map, fakeable leptons) with corrected pT
    df = (df.Define("wzz_j_cvl", "ROOT::RVec<float>(Jet_btag{0}CvL[clean_jet])".format(b))
            .Define("wzz_j_cvb", "ROOT::RVec<float>(Jet_btag{0}CvB[clean_jet])".format(b))
            .Define("wzz_j_qg", "ROOT::RVec<float>(Jet_btag{0}{1}[clean_jet])".format(b, qg))
            .Define("wzz_j_b", "ROOT::RVec<float>(clean_Jet_btagUnifiedParTB)")
            .Define("wzz_j_eta", "ROOT::RVec<float>(clean_Jet_eta)").Define("wzz_j_phi", "ROOT::RVec<float>(clean_Jet_phi)")
            .Define("wzz_j_mass", "ROOT::RVec<float>(clean_Jet_mass)"))
    fj = ("globalParT3_withMass" if df.HasColumn("FatJet_globalParT3_withMassWvsQCD") else "particleNetWithMass_")
    df = (df.Define("wzz_fj", "FatJet_pt > 170")
            .Define("wzz_fj_pt", "ROOT::RVec<float>(FatJet_pt[wzz_fj])").Define("wzz_fj_eta", "ROOT::RVec<float>(FatJet_eta[wzz_fj])")
            .Define("wzz_fj_phi", "ROOT::RVec<float>(FatJet_phi[wzz_fj])").Define("wzz_fj_msd", "ROOT::RVec<float>(FatJet_msoftdrop[wzz_fj])")
            .Define("wzz_fj_vtag", "wzz::vmax(FatJet_{0}WvsQCD[wzz_fj], FatJet_{0}ZvsQCD[wzz_fj])".format(fj))
            # NanoAOD v12 has no PuppiMET_significance: 0, exactly as in the BDT training inputs
            # (nano.py falls back to 0 too); retrain without this input to drop the asymmetry
            .Define("wzz_metsig", "(float)PuppiMET_significance" if df.HasColumn("PuppiMET_significance") else "0.f"))
    srcs = ", ".join("clean_Jet_ptJes{0:02d}Up".format(k) for k in range(28))
    # MET with the total-JES jets: the framework's propagation (makeJES: reference ptDef -> varied)
    met_unc = ("(float)compute_JSON_MET_Unc(PuppiMET_pt,PuppiMET_phi,RawPuppiMET_pt,RawPuppiMET_phi,clean_Jet_chEmEF,"
               "clean_Jet_neEmEF,clean_Jet_muonSubtrFactor,clean_Jet_rawFactor,clean_Jet_ptDef,wzz_j_ptJesTotUp,"
               "clean_Jet_eta,clean_Jet_phi,clean_Jet_mass,{0})")
    df = (df.Define("wzz_j_pt", "ROOT::RVec<float>(clean_Jet_ptDef)")
            .Define("wzz_j_ptJesTotUp", "wzz::jes_total_up(clean_Jet_ptDef, {{{0}}})".format(srcs))
            .Define("wzz_j_ptJerUp", "ROOT::RVec<float>(clean_Jet_ptJerUp)")
            .Define("wzz_j_ptUnclUp", "wzz_j_pt")
            .Define("wzz_met", "(float)PuppiMET_ptDef").Define("wzz_metphi", "(float)PuppiMET_phiDef")
            .Define("wzz_metJesTotUp", met_unc.format(1)).Define("wzz_metphiJesTotUp", met_unc.format(2))
            .Define("wzz_metJerUp", "(float)PuppiMET_ptJerUp").Define("wzz_metphiJerUp", "(float)PuppiMET_phiJerUp")
            .Define("wzz_metUnclUp", "(float)PuppiMET_ptUnclUp").Define("wzz_metphiUnclUp", "(float)PuppiMET_phiUnclUp"))
    return df


def define_weights(df, year, isData, weight, nTheoryReplicas, lheRenorm, psRenorm):
    if isData == "true":
        return df.Define("weight", "1.0")
    hasPrefire = year <= 20180 and df.HasColumn("L1PreFiringWeight_Nom")
    cut = getBTagCut(BTAGSEL, year)
    btv = ("compute_JSON_BTV_SF(goodbtag_Jet_pt,goodbtag_Jet_eta,goodbtag_Jet_btagUnifiedParTB,"
           "goodbtag_Jet_hadronFlavour,\"{0}\",{1},{2},{3})")
    df = (df.Define("goodbtag_Jet_hadronFlavour", "Jet_hadronFlavour[clean_jet][goodbtag_jet]")
            .Define("wzz_pu", "compute_JSON_PU_SF(Pileup_nTrueInt,\"nominal\")")
            .Define("wzz_prefire", "L1PreFiringWeight_Nom" if hasPrefire else "1.0f")
            .Define("wzz_btag", btv.format("central", 0, BTAGSEL, cut))
            .Define("weight", "{0}*genWeight*wzz_pu*wzz_prefire*wzz_btag".format(weight))
            .Define("weightRaw", "{0}*genWeight".format(weight))      # validation: no PU / b tag / SF
            .Define("weightPUUp", "weight/wzz_pu*compute_JSON_PU_SF(Pileup_nTrueInt,\"up\")")
            .Define("weightPUDown", "weight/wzz_pu*compute_JSON_PU_SF(Pileup_nTrueInt,\"down\")")
            .Define("weightBtagBCUp", "weight/wzz_btag*" + btv.format("up_correlated", 1, BTAGSEL, cut))
            .Define("weightBtagBCDown", "weight/wzz_btag*" + btv.format("down_correlated", 1, BTAGSEL, cut))
            .Define("weightBtagLFUp", "weight/wzz_btag*" + btv.format("up_correlated", -1, BTAGSEL, cut))
            .Define("weightBtagLFDown", "weight/wzz_btag*" + btv.format("down_correlated", -1, BTAGSEL, cut))
            .Define("weightPrefireUp", "weight/wzz_prefire*L1PreFiringWeight_Up" if hasPrefire else "weight"))
    df = selectionTheoryWeigths(df, weight, nTheoryReplicas, lheRenorm, psRenorm)
    return df


WVARS = (["PUUp", "PUDown", "BtagBCUp", "BtagBCDown", "BtagLFUp", "BtagLFDown", "PrefireUp"]
         + ["QCDScale{0}".format(i) for i in range(6)] + ["PS{0}".format(i) for i in range(4)])


def analysis(df, sample, weight, year, PDType, isData, whichJob, nTheoryReplicas, lheRenorm, psRenorm):
    print("wzzAnalysis: sample {0} year {1} job {2} data {3}".format(sample, year, whichJob, isData))
    ROOT.initJSONSFs(year)
    ROOT.wzz.init_wzz_sf(year)
    if isData == "false":       # b-tag efficiencies for compute_JSON_BTV_SF (histo2D slots 20-22)
        fb = ROOT.TFile("data/histoBtagEffSelEtaPt_{0}.root".format(year))
        for slot, k in ((20, 0), (21, 1), (22, 2)):
            hb = fb.Get("histoBtagEffSelEtaPt_{0}".format(k + 3 * BTAGSEL))
            hb.SetDirectory(0)
            ROOT.initHisto2D(hb, slot)
            _keep.append(hb)
        fb.Close()
    df = prepareWZNanoAOD(df, year)
    trig = SELJSON["triggers"]
    T = {k: pruneWZTrigger(df, getTriggerFromJson(trig, k, year)) for k in ("TRIGGERMUEG", "TRIGGERDMU", "TRIGGERSMU", "TRIGGERDEL", "TRIGGERSEL")}
    df = selectionTrigger2L(df, year, PDType, SELJSON["JSON"], isData, T["TRIGGERSEL"], T["TRIGGERDEL"],
                            T["TRIGGERSMU"], T["TRIGGERDMU"], T["TRIGGERMUEG"])
    mf = met_filters(year)
    if mf:
        df = df.Filter(mf, "MET filters")
    # framework lepton collections: only for the jet cleaning of selectionJetMet
    lsel = SELJSON["leptonSel"]
    lv = 12 if year < 20200 and hasLegacyLeptonMVA(df) else None
    df = selectionElMu(df, year, getLeptomSelFromJson(lsel, "FAKE_MU", year, version=lv),
                       getLeptomSelFromJson(lsel, "TIGHT_MU8", year, 1, version=lv),
                       getLeptomSelFromJson(lsel, "FAKE_EL", year, version=lv),
                       getLeptomSelFromJson(lsel, "TIGHT_EL8", year, 1, version=lv))
    df = selectionJetMet(df, year, BTAGSEL, isData, sample, 4.7)
    df = define_inputs(df, year, isData)
    df = define_weights(df, year, isData, weight, nTheoryReplicas, lheRenorm, psRenorm)
    if isData == "false" and df.HasColumn("GenPart_pdgId"):
        df = df.Define("wzz_vh", "wzz::gen_vh(GenPart_pdgId, GenPart_genPartIdxMother, GenPart_statusFlags)")
    else:
        df = df.Define("wzz_vh", "ROOT::RVec<int>{0, 0}")
    bw, ct = BWPS[year], CTAG.get(year, (0.291, 0.457))
    ng, npi = ROOT.wzz.fit_total(), ROOT.wzz.np_nbins()
    nfr = ROOT.wzz.fr_nbins()
    nver = nano_version(year)
    h = []
    for v in VARIANTS:
        dv = df.Define("leps{0}".format(v), "wzz::build_leptons({0}, {1}, wzz_raw)".format(v, nver))
        if isData == "false":
            dv = dv.Define("sf{0}".format(v), "wzz::lepton_sf({0}, leps{0}, {1}, \"{2}\", 0, 0)".format(v, year, ELEYEAR[year]))
            for name, t, which in (("MuSFUp", 1, 1), ("MuSFDown", -1, 1), ("ElSFUp", 1, 2), ("ElSFDown", -1, 2)):
                dv = dv.Define("sf{0}{1}".format(v, name), "wzz::lepton_sf({0}, leps{0}, {1}, \"{2}\", {3}, {4})".format(v, year, ELEYEAR[year], t, which))
        else:
            dv = dv.Define("sf{0}".format(v), "1.0f")
        cfg = "wzz::config_for({0}, {1}f)".format(v, BWPS[year][1])
        for jv in (JETVARS if isData == "false" else [""]):
            tag = "{0}{1}".format(v, jv)
            jets = "wzz_j_pt{0}".format(jv) if jv else "wzz_j_pt"
            met = ("wzz_met{0}".format(jv), "wzz_metphi{0}".format(jv)) if jv else ("wzz_met", "wzz_metphi")
            dv = (dv.Define("cat" + tag, "wzz::categorize(leps{0}, {1}, wzz_j_eta, wzz_j_phi, wzz_j_mass, wzz_j_b, wzz_j_cvl, wzz_j_cvb, wzz_j_qg, "
                                         "wzz_fj_pt, wzz_fj_eta, wzz_fj_phi, wzz_fj_msd, wzz_fj_vtag, {2}, {3}, wzz_metsig, {4})".format(v, jets, met[0], met[1], cfg))
                    .Define("bdt" + tag, "wzz::bdt_scores(cat{0}, event, {{{1}f, {2}f, {3}f, {4}f}}, {{{5}f, {6}f}})".format(tag, *bw, *ct))
                    .Define("gb" + tag, "wzz::global_bin(cat{0}, bdt{0})".format(tag))
                    .Define("st" + tag, "(int)std::lround(cat{0}[wzz::O_STATUS])".format(tag))
                    .Define("tr" + tag, "(int)std::lround(cat{0}[wzz::O_TRUTH])".format(tag)))
            if isData == "false":
                dv = dv.Define("w" + tag, "weight*sf{0}".format(v))
                sig = dv.Filter("gb{0} >= 0 && st{0} == wzz::ST_SIGNAL".format(tag))
                for proc, cond in (("main", "tr{0} == 0 && wzz_vh[0] == 0"), ("conv", "tr{0} == 1")):
                    h.append(sig.Filter(cond.format(tag)).Histo1D(("h_{0}_{1}".format(tag, proc), "", ng, 0, ng), "gb" + tag, "w" + tag))
                for prod in (1, 2):
                    for dec in (1, 2, 3, 4):
                        h.append(sig.Filter("tr{0} == 0 && wzz_vh[0] == {1} && wzz_vh[1] == {2}".format(tag, prod, dec))
                                 .Histo1D(("h_{0}_vh{1}{2}".format(tag, prod, dec), "", ng, 0, ng), "gb" + tag, "w" + tag))
            else:
                cr = " || ".join("(int)std::lround(cat{0}[wzz::O_REGION]) == wzz::{1}".format(tag, r) for r in CR_REGIONS)
                blind = "true" if FILL_DATA_SR else "({0})".format(cr)
                h.append(dv.Filter("gb{0} >= 0 && st{0} == wzz::ST_SIGNAL && {1}".format(tag, blind))
                         .Histo1D(("h_{0}_data".format(tag), "", ng, 0, ng), "gb" + tag))
        tag = "{0}".format(v)
        # weight variations (nominal jets), prompt signal-like MC
        if isData == "false":
            sig = dv.Filter("gb{0} >= 0 && st{0} == wzz::ST_SIGNAL && tr{0} == 0 && wzz_vh[0] == 0".format(tag))
            for wv in WVARS:
                sig = sig.Define("w{0}_{1}".format(tag, wv), "weight{0}*sf{1}".format(wv, v))
                h.append(sig.Histo1D(("h_{0}_main_{1}".format(tag, wv), "", ng, 0, ng), "gb" + tag, "w{0}_{1}".format(tag, wv)))
            h.append(sig.Histo1D(("h_{0}_main_raw".format(tag), "", ng, 0, ng), "gb" + tag, "weightRaw"))
            for sfv in ("MuSFUp", "MuSFDown", "ElSFUp", "ElSFDown"):
                sig = sig.Define("w{0}_{1}".format(tag, sfv), "weight*sf{0}{1}".format(v, sfv))
                h.append(sig.Histo1D(("h_{0}_main_{1}".format(tag, sfv), "", ng, 0, ng), "gb" + tag, "w{0}_{1}".format(tag, sfv)))
        # application region -> nonprompt (data) / prompt-MC subtraction, indexed by FR bin
        ap = dv.Define("npi" + tag, "wzz::np_index(cat{0})".format(tag)).Filter("gb{0} >= 0 && npi{0} >= 0".format(tag))
        if isData == "false":
            ap = ap.Filter("tr{0} == 0".format(tag))
            h.append(ap.Histo2D(("np_{0}".format(tag), "", ng, 0, ng, npi, 0, npi), "gb" + tag, "npi" + tag, "w" + tag))
        else:
            h.append(ap.Histo2D(("np_{0}".format(tag), "", ng, 0, ng, npi, 0, npi), "gb" + tag, "npi" + tag))
        # Z+L fake-rate probes: num/den per flat FR index of both maps (T: tight vs fakeable, F: fakeable vs loose)
        zl = (dv.Define("zl" + tag, "wzz::zl_probe(leps{0}, cat{0}, wzz_metphi)".format(tag)).Filter("zl{0}.size() == 4".format(tag))
                .Define("zlT" + tag, "wzz::fr_index(wzz::TIGHT, (int)zl{0}[0], zl{0}[1], zl{0}[2])".format(tag))
                .Define("zlF" + tag, "wzz::fr_index(wzz::FAKEABLE, (int)zl{0}[0], zl{0}[1], zl{0}[2])".format(tag))
                .Define("zlL" + tag, "(int)zl{0}[3]".format(tag)))
        if isData == "false":
            zl = zl.Filter("tr{0} == 0".format(tag))   # prompt probes (with a prompt Z pair) for the subtraction
        wcol = ("w" + tag) if isData == "false" else None
        for mp, lvl_num, lvl_den in (("T", "wzz::TIGHT", "wzz::FAKEABLE"), ("F", "wzz::FAKEABLE", "wzz::LOOSE")):
            idx = "zl{0}{1}".format(mp, tag)
            num = zl.Filter("{0} >= 0 && zlL{1} >= {2}".format(idx, tag, lvl_num))
            den = zl.Filter("{0} >= 0 && zlL{1} >= {2}".format(idx, tag, lvl_den))
            args = (idx, wcol) if wcol else (idx,)
            h.append(num.Histo1D(("fr_{0}_num{1}".format(tag, mp), "", nfr, 0, nfr), *args))
            h.append(den.Histo1D(("fr_{0}_den{1}".format(tag, mp), "", nfr, 0, nfr), *args))
    out = ROOT.TFile("fillhisto_wzzAnalysis_sample{0}_year{1}_job{2}.root".format(sample, year, whichJob), "RECREATE")
    for x in h:
        o = x.GetValue()
        if o.GetEntries() > 0 or o.GetName().startswith(("h_0_main", "fr_")):
            o.Write()
    hj = ROOT.TH1D("hJobNorm", "hJobNorm", 2, 0, 2)
    hj.SetBinContent(1, 1.0 / weight if weight != 0 else 0.0)
    hj.SetBinContent(2, weight)
    hj.Write()
    out.Close()


def run_mc(sample, year, whichJob, group):
    files = getMClist(sample, "3l")
    # per-job normalisation: split first, then normalise to THIS job's files (getMCnormList returns
    # its argument unless NORM_FILELIST is set); the harvest combines jobs by their sum(genWeight)
    if whichJob != -1:
        files = groupFiles(files, group)[whichJob]
        if len(files) == 0:
            print("no files in job/group: {0} / {1}".format(whichJob, group))
            return
    nTheoryReplicas = [103, 9, 4]
    sumw, sumnow, lhe, ps, nruns = readRunsSums(getMCnormList(files), nTheoryReplicas)
    lheRenorm = [1] * 6
    psRenorm = [1] * 4
    if lhe[4] != 0:
        lheRenorm = [lhe[i] / lhe[4] for i in (0, 1, 3, 5, 7, 8)]
    if ps[4] != 0:
        psRenorm = [ps[i] / ps[4] for i in range(4)]
    if os.environ.get("NORM_FILELIST"):
        raise RuntimeError("NORM_FILELIST set: wzzAnalysis uses per-job normalisation only (harvest)")
    weight = SwitchSample(sample, "3l")[1] / sumw * getLumi(year)
    setTriggerFiles(files)
    df = ROOT.RDataFrame("Events", files)
    PDType = os.path.basename(SwitchSample(sample, "3l")[0]).split('+')[0]
    analysis(df, sample, weight, year, PDType, "false", whichJob, nTheoryReplicas, lheRenorm, psRenorm)


def run_data(sample, year, whichJob, group):
    PDType = "0"
    if 1000 <= sample <= 1009: PDType = "SingleMuon"
    elif 1010 <= sample <= 1019: PDType = "DoubleMuon"
    elif 1020 <= sample <= 1029: PDType = "MuonEG"
    elif 1030 <= sample <= 1039: PDType = "DoubleEG" if year // 10 in (2016, 2017) else "EGamma"
    elif 1040 <= sample <= 1049: PDType = "SingleElectron" if year // 10 in (2016, 2017) else "Muon"
    files = getDATAlist(sample, year, "3l")
    if whichJob != -1:
        files = groupFiles(files, group)[whichJob]
        if len(files) == 0:
            print("no files in job/group: {0} / {1}".format(whichJob, group))
            return
    setTriggerFiles(files)
    df = ROOT.RDataFrame("Events", files)
    analysis(df, sample, 1.0, year, PDType, "true", whichJob, [0, 0, 0], [1] * 6, [1] * 4)


if __name__ == "__main__":
    group, year, process, whichJob = 2, 2024, -1, -1
    opts, _ = getopt.getopt(sys.argv[1:], "", ["year=", "process=", "whichJob=", "group="])
    for o, a in opts:
        if o == "--year": year = int(a)
        elif o == "--process": process = int(a)
        elif o == "--whichJob": whichJob = int(a)
        elif o == "--group": group = int(a)
    try:
        if 0 <= process < 1000:
            run_mc(process, year, whichJob, group)
        elif process >= 1000:
            run_data(process, year, whichJob, group)
    except Exception as e:
        print("FAILED {0}".format(e))
        raise
