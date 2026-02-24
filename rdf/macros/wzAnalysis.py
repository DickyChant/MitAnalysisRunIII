import ROOT
import os, sys, getopt, json
from array import array

ROOT.ROOT.EnableImplicitMT(4)
from utilsCategory import plotCategory
from utilsAna import getMClist, getDATAlist
from utilsAna import SwitchSample, groupFiles, getTriggerFromJson, getLeptomSelFromJson, getLumi
from utilsSelection import selectionTauVeto, selectionPhoton, selectionJetMet, selection3LVar, selectionTrigger2L, selectionElMu, selectionWeigths, selectionGenLepJet, makeFinalVariableVar, makeFinalVariable2DVar
from utilsMVA import redefineMVAVariables
import tmva_helper_xml

makeDataCards = 4 # 1 (njets), 2-1006 (lepton flavor), 3-1002 (3D), 4-1001 (BDT 2D), 5-1003 (BDT 1D), 6-1004 (mjj), 7-1005 (mjj diff)
genVBSSel = 1
correctionString = "_correction"

versionMVA = 0
doNtuples = False
# 0 = T, 1 = M, 2 = L
bTagSel = 0
useBTaggingWeights = 1

useFR = 1
whichAna = 2

altMass = "Def"
jetEtaCut = 2.5
if(makeDataCards >= 3): jetEtaCut = 4.9
metCut = 30.0

selectionJsonPath = "config/selection.json"
if(not os.path.exists(selectionJsonPath)):
    selectionJsonPath = "selection.json"

with open(selectionJsonPath) as jsonFile:
    jsonObject = json.load(jsonFile)
    jsonFile.close()

JSON = jsonObject['JSON']

BARRELphotons = jsonObject['BARRELphotons']
ENDCAPphotons = jsonObject['ENDCAPphotons']

VBSSEL = jsonObject['VBSSEL']
VBSQCDSEL = jsonObject['VBSQCDSEL']

muSelChoice = 8
MUOWP = "Medium"

elSelChoice = 8
ELEWP = "DUMMY"
if(elSelChoice == 0):
    ELEWP = "Medium"
elif(elSelChoice == 1):
    ELEWP = "Tight"
elif(elSelChoice == 2):
    ELEWP = "wp80noiso"
elif(elSelChoice == 3):
    ELEWP = "wp80iso"
elif(elSelChoice == 4):
    ELEWP = "wp80iso"
elif(elSelChoice == 5):
    ELEWP = "wp90iso"
elif(elSelChoice == 6):
    ELEWP = "wp80iso"
elif(elSelChoice == 7):
    ELEWP = "wp80iso"
elif(elSelChoice == 8):
    ELEWP = "wp80iso"
elif(elSelChoice == 9):
    ELEWP = "Veto"

def selectionLL(df,year,PDType,isData,count):

    overallTriggers = jsonObject['triggers']
    TRIGGERMUEG = getTriggerFromJson(overallTriggers, "TRIGGERMUEG", year)
    TRIGGERDMU  = getTriggerFromJson(overallTriggers, "TRIGGERDMU", year)
    TRIGGERSMU  = getTriggerFromJson(overallTriggers, "TRIGGERSMU", year)
    TRIGGERDEL  = getTriggerFromJson(overallTriggers, "TRIGGERDEL", year)
    TRIGGERSEL  = getTriggerFromJson(overallTriggers, "TRIGGERSEL", year)

    dftag = selectionTrigger2L(df,year,PDType,JSON,isData,TRIGGERSEL,TRIGGERDEL,TRIGGERSMU,TRIGGERDMU,TRIGGERMUEG)

    overallLeptonSel = jsonObject['leptonSel']
    FAKE_MU   = getLeptomSelFromJson(overallLeptonSel, "FAKE_MU",   year)
    TIGHT_MU  = getLeptomSelFromJson(overallLeptonSel, "TIGHT_MU{0}".format(muSelChoice),  year, 1)

    FAKE_EL   = getLeptomSelFromJson(overallLeptonSel, "FAKE_EL",   year)
    TIGHT_EL  = getLeptomSelFromJson(overallLeptonSel, "TIGHT_EL{0}".format(elSelChoice),  year, 1)

    dftag = selectionElMu(dftag,year,FAKE_MU,TIGHT_MU,FAKE_EL,TIGHT_EL)

    dftag =(dftag.Filter("nLoose == 3","Only three loose leptons")
                 .Filter("nFake == 3","Three fake leptons")
                 .Define("eventNum", "event")
                 .Filter("(Sum(fake_mu) > 0 and Max(fake_Muon_pt) > 25) or (Sum(fake_el) > 0 and Max(fake_Electron_pt) > 25)","At least one high pt lepton")
                 )

    if(useFR == 0):
        dftag = dftag.Filter("nTight == 3","Three tight leptons")

    dftag = selectionTauVeto(dftag,year,isData)
    dftag = selectionPhoton (dftag,year,BARRELphotons,ENDCAPphotons)
    dftag = selectionJetMet (dftag,year,bTagSel,isData,count,jetEtaCut)
    dftag = selection3LVar  (dftag,year,isData)

    return dftag


def analysis(df,count,category,weight,year,PDType,isData,whichJob,nTheoryReplicas,genEventSumLHEScaleRenorm,genEventSumPSRenorm,ewkCorrWeights,wsWeights,puWeights,histoBTVEffEtaPtLF,histoBTVEffEtaPtCJ,histoBTVEffEtaPtBJ,histoFakeEtaPt_mu,histoFakeEtaPt_el,histoLepSFEtaPt_mu,histoLepSFEtaPt_el,histoTriggerSFEtaPt_0_0,histoTriggerSFEtaPt_0_1,histoTriggerSFEtaPt_0_2,histoTriggerSFEtaPt_0_3,histoTriggerSFEtaPt_1_0,histoTriggerSFEtaPt_1_1,histoTriggerSFEtaPt_1_2,histoTriggerSFEtaPt_1_3,histoTriggerSFEtaPt_2_0,histoTriggerSFEtaPt_2_1,histoTriggerSFEtaPt_2_2,histoTriggerSFEtaPt_2_3,histoTriggerSFEtaPt_3_0,histoTriggerSFEtaPt_3_1,histoTriggerSFEtaPt_3_2,histoTriggerSFEtaPt_3_3):

    print("starting {0} / {1} / {2} / {3} / {4} / {5} / {6}".format(count,category,weight,year,PDType,isData,whichJob))

    theCat = category
    if(theCat > 100): theCat = plotCategory("kPlotData")

    xPtTrgBins = array('d', [10,15,20,25,30,35,40,50,60,70,80,90,105,120,150,200])

    nCat, nHisto, nhistoNonPrompt, nHistoMVA = plotCategory("kPlotCategories"), 700, 50, 700
    histo    = [[0 for y in range(nCat)] for x in range(nHisto)]
    histoNonPrompt = [0 for y in range(nhistoNonPrompt)]
    histo2D = [[0 for y in range(nCat)] for x in range(nHistoMVA)]

    ROOT.initHisto2D(histoFakeEtaPt_mu[0],0)
    ROOT.initHisto2D(histoFakeEtaPt_el[0],1)
    ROOT.initHisto2D(histoLepSFEtaPt_mu,2)
    ROOT.initHisto2D(histoLepSFEtaPt_el,3)
    ROOT.initHisto2D(histoTriggerSFEtaPt_0_0, 4)
    ROOT.initHisto2D(histoTriggerSFEtaPt_0_1, 5)
    ROOT.initHisto2D(histoTriggerSFEtaPt_0_2, 6)
    ROOT.initHisto2D(histoTriggerSFEtaPt_0_3, 7)
    ROOT.initHisto2D(histoTriggerSFEtaPt_1_0, 8)
    ROOT.initHisto2D(histoTriggerSFEtaPt_1_1, 9)
    ROOT.initHisto2D(histoTriggerSFEtaPt_1_2,10)
    ROOT.initHisto2D(histoTriggerSFEtaPt_1_3,11)
    ROOT.initHisto2D(histoTriggerSFEtaPt_2_0,12)
    ROOT.initHisto2D(histoTriggerSFEtaPt_2_1,13)
    ROOT.initHisto2D(histoTriggerSFEtaPt_2_2,14)
    ROOT.initHisto2D(histoTriggerSFEtaPt_2_3,15)
    ROOT.initHisto2D(histoTriggerSFEtaPt_3_0,16)
    ROOT.initHisto2D(histoTriggerSFEtaPt_3_1,17)
    ROOT.initHisto2D(histoTriggerSFEtaPt_3_2,18)
    ROOT.initHisto2D(histoTriggerSFEtaPt_3_3,19)
    ROOT.initHisto2D(histoBTVEffEtaPtLF,20)
    ROOT.initHisto2D(histoBTVEffEtaPtCJ,21)
    ROOT.initHisto2D(histoBTVEffEtaPtBJ,22)
    ROOT.initHisto2D(histoFakeEtaPt_mu[1],23)
    ROOT.initHisto2D(histoFakeEtaPt_mu[2],24)
    ROOT.initHisto2D(histoFakeEtaPt_mu[3],25)
    ROOT.initHisto2D(histoFakeEtaPt_mu[4],26)
    ROOT.initHisto2D(histoFakeEtaPt_mu[5],27)
    ROOT.initHisto2D(histoFakeEtaPt_mu[6],28)
    ROOT.initHisto2D(histoFakeEtaPt_mu[7],29)
    ROOT.initHisto2D(histoFakeEtaPt_mu[8],30)
    ROOT.initHisto2D(histoFakeEtaPt_el[1],31)
    ROOT.initHisto2D(histoFakeEtaPt_el[2],32)
    ROOT.initHisto2D(histoFakeEtaPt_el[3],33)
    ROOT.initHisto2D(histoFakeEtaPt_el[4],34)
    ROOT.initHisto2D(histoFakeEtaPt_el[5],35)
    ROOT.initHisto2D(histoFakeEtaPt_el[6],36)
    ROOT.initHisto2D(histoFakeEtaPt_el[7],37)
    ROOT.initHisto2D(histoFakeEtaPt_el[8],38)
    ROOT.initHisto2D(wsWeights[2],39)
    ROOT.initHisto1D(puWeights[0],0)
    ROOT.initHisto1D(puWeights[1],1)
    ROOT.initHisto1D(puWeights[2],2)
    ROOT.initHisto1D(wsWeights[0],8)
    ROOT.initHisto1D(wsWeights[1],9)
    ROOT.initHisto1D(ewkCorrWeights[0],10)
    ROOT.initHisto1D(ewkCorrWeights[1],11)
    ROOT.initHisto1D(ewkCorrWeights[2],12)
    ROOT.initHisto1D(ewkCorrWeights[3],13)

    ROOT.initJSONSFs(year)

    branchList = ROOT.vector('string')()
    for branchName in [
            "eventNum",
            "weight",
            "theCat",
            "ngood_jets",
            # VBS kinematic variables
            "vbs_mjj",
            "vbs_ptjj",
            "vbs_detajj",
            "vbs_dphijj",
            "vbs_ptj1",
            "vbs_ptj2",
            "vbs_etaj1",
            "vbs_etaj2",
            "vbs_phij1",
            "vbs_phij2",
            "vbs_massj1",
            "vbs_massj2",
            "vbs_btagj1",
            "vbs_btagj2",
            "vbs_zepvv",
            "vbs_zepmax",
            "vbs_sumHT",
            "vbs_ptvv",
            "vbs_pttot",
            "vbs_detavvj1",
            "vbs_detavvj2",
            "vbs_ptbalance",
            # Z lepton p4 and flavor (0=mu, 1=el)
            "ptl1Z",
            "etal1Z",
            "phil1Z",
            "massl1Z",
            "flavorl1Z",
            "ptl2Z",
            "etal2Z",
            "phil2Z",
            "massl2Z",
            "flavorl2Z",
            # W lepton p4 and flavor
            "ptlW",
            "etalW_signed",
            "philW",
            "masslW",
            "flavorlW",
            # MET
            "PuppiMET_ptDef",
            "PuppiMET_phiDef",
            # Additional lepton/mass variables
            "mll",
            "m3l",
            "mtW",
            "TriLepton_flavor",
    ]:
        branchList.push_back(branchName)

    MVAweights = "weights_mva/bdt_BDTG_vbfinc_v{0}.weights.xml".format(versionMVA)
    tmva_helper = None
    if(os.path.exists(MVAweights) and doNtuples == False):
        tmva_helper = tmva_helper_xml.TMVAHelperXML(MVAweights)
        print(tmva_helper.variables)
    else:
        print("MVA weights not found or doNtuples mode — skipping BDT inference")

    dftag = selectionLL(df,year,PDType,isData,count)

    if(isData == "false"):
        dftag = selectionGenLepJet(dftag,15,30,5.0)
        dftag = (dftag.Define("mjjGen", "compute_vbs_gen_variables(0,ngood_GenJets,good_GenJet_pt,good_GenJet_eta,good_GenJet_phi,good_GenJet_mass,ngood_GenDressedLeptons,good_GenDressedLepton_pdgId,good_GenDressedLepton_hasTauAnc,good_GenDressedLepton_pt,good_GenDressedLepton_eta,good_GenDressedLepton_phi,good_GenDressedLepton_mass)")
                      )
    else:
        dftag = (dftag.Define("mjjGen", "{0}".format(0))
                      )

    dfbase = selectionWeigths(dftag,isData,year,PDType,weight,useFR,bTagSel,useBTaggingWeights,nTheoryReplicas,genEventSumLHEScaleRenorm,genEventSumPSRenorm,MUOWP,ELEWP,correctionString,whichAna)

    dfbase = (dfbase.Define("kPlotNonPrompt", "{0}".format(plotCategory("kPlotNonPrompt")))
                    .Define("kPlotWS", "{0}".format(plotCategory("kPlotWS")))
                    .Define("kPlotEWKWZ", "{0}".format(plotCategory("kPlotEWKWZ")))
                    .Filter("{0} != kPlotEWKWZ || nGenJet_bParton == 0".format(theCat), "EWKWZ requirement")
                    .Define("theCat","compute_category({0},kPlotNonPrompt,kPlotWS,nFake,nTight,0)".format(theCat))
                    )

    if(tmva_helper is not None):
        dfbase = tmva_helper.run_inference(dfbase,"bdt_vbfinc",0)
    else:
        dfbase = dfbase.Define("bdt_vbfinc", "0.0f")

    dfwzcatMuonMomUp        = []
    dfwzcatElectronMomUp    = []
    dfwzcatJERUp            = []
    dfwzcatJESUp            = []
    dfwzcatUnclusteredUp    = []
    dfwzbcatMuonMomUp       = []
    dfwzbcatElectronMomUp   = []
    dfwzbcatJERUp           = []
    dfwzbcatJESUp           = []
    dfwzbcatUnclusteredUp   = []
    dfwzcat = []
    dfwzbcat = []
    dfwzjjcat = []
    dfwzbjjcat = []
    dfwzvbscat = []
    dfwzbvbscat = []
    dfzgcat = []
    dfwhcat = []
    dfsscat = []
    dfwzvbsBDTcat = []
    dfEMMcat = []
    dfMEEcat = []

    dfwzvbscatMuonMomUp       = []
    dfwzvbscatElectronMomUp   = []
    dfwzvbscatJes00Up         = []
    dfwzvbscatJes01Up         = []
    dfwzvbscatJes02Up         = []
    dfwzvbscatJes03Up         = []
    dfwzvbscatJes04Up         = []
    dfwzvbscatJes05Up         = []
    dfwzvbscatJes06Up         = []
    dfwzvbscatJes07Up         = []
    dfwzvbscatJes08Up         = []
    dfwzvbscatJes09Up         = []
    dfwzvbscatJes10Up         = []
    dfwzvbscatJes11Up         = []
    dfwzvbscatJes12Up         = []
    dfwzvbscatJes13Up         = []
    dfwzvbscatJes14Up         = []
    dfwzvbscatJes15Up         = []
    dfwzvbscatJes16Up         = []
    dfwzvbscatJes17Up         = []
    dfwzvbscatJes18Up         = []
    dfwzvbscatJes19Up         = []
    dfwzvbscatJes20Up         = []
    dfwzvbscatJes21Up         = []
    dfwzvbscatJes22Up         = []
    dfwzvbscatJes23Up         = []
    dfwzvbscatJes24Up         = []
    dfwzvbscatJes25Up         = []
    dfwzvbscatJes26Up         = []
    dfwzvbscatJes27Up         = []
    dfwzvbscatJerUp           = []
    dfwzvbscatJERUp           = []
    dfwzvbscatJESUp           = []
    dfwzvbscatUnclusteredUp   = []

    dfwzbvbscatMuonMomUp      = []
    dfwzbvbscatElectronMomUp  = []
    dfwzbvbscatJes00Up        = []
    dfwzbvbscatJes01Up        = []
    dfwzbvbscatJes02Up        = []
    dfwzbvbscatJes03Up        = []
    dfwzbvbscatJes04Up        = []
    dfwzbvbscatJes05Up        = []
    dfwzbvbscatJes06Up        = []
    dfwzbvbscatJes07Up        = []
    dfwzbvbscatJes08Up        = []
    dfwzbvbscatJes09Up        = []
    dfwzbvbscatJes10Up        = []
    dfwzbvbscatJes11Up        = []
    dfwzbvbscatJes12Up        = []
    dfwzbvbscatJes13Up        = []
    dfwzbvbscatJes14Up        = []
    dfwzbvbscatJes15Up        = []
    dfwzbvbscatJes16Up        = []
    dfwzbvbscatJes17Up        = []
    dfwzbvbscatJes18Up        = []
    dfwzbvbscatJes19Up        = []
    dfwzbvbscatJes20Up        = []
    dfwzbvbscatJes21Up        = []
    dfwzbvbscatJes22Up        = []
    dfwzbvbscatJes23Up        = []
    dfwzbvbscatJes24Up        = []
    dfwzbvbscatJes25Up        = []
    dfwzbvbscatJes26Up        = []
    dfwzbvbscatJes27Up        = []
    dfwzbvbscatJerUp          = []
    dfwzbvbscatJERUp          = []
    dfwzbvbscatJESUp          = []
    dfwzbvbscatUnclusteredUp  = []
    for x in range(nCat):
        dfwzcat.append(dfbase.Filter("theCat=={0}".format(x), "correct category ({0})".format(x)))

        dfsscat.append(dfwzcat[x].Filter("abs(Sum(fake_Muon_charge)+Sum(fake_Electron_charge)) == 3", "+/- 3 net charge"))

        dfwzcat[x] = dfwzcat[x].Filter("abs(Sum(fake_Muon_charge)+Sum(fake_Electron_charge)) == 1", "+/- 1 net charge")

        if((x == plotCategory("kPlotEWKWZ")) and isData == "false"):
            dfwzcat[x] = (dfwzcat[x].Define("theGenCat",   "compute_vbs_gen_category({0},ngood_GenJets,good_GenJet_pt,good_GenJet_eta,good_GenJet_phi,good_GenJet_mass,ngood_GenDressedLeptons,good_GenDressedLepton_pdgId,good_GenDressedLepton_hasTauAnc,good_GenDressedLepton_pt,good_GenDressedLepton_eta,good_GenDressedLepton_phi,good_GenDressedLepton_mass,11)".format(genVBSSel))
                                    )
        else:
            dfwzcat[x] = (dfwzcat[x].Define("theGenCat","{0}".format(0))
                                    )

        dfwzvbscatMuonMomUp    .append(dfwzcat[x])
        dfwzvbscatElectronMomUp.append(dfwzcat[x])
        dfwzvbscatJes00Up      .append(dfwzcat[x])
        dfwzvbscatJes01Up      .append(dfwzcat[x])
        dfwzvbscatJes02Up      .append(dfwzcat[x])
        dfwzvbscatJes03Up      .append(dfwzcat[x])
        dfwzvbscatJes04Up      .append(dfwzcat[x])
        dfwzvbscatJes05Up      .append(dfwzcat[x])
        dfwzvbscatJes06Up      .append(dfwzcat[x])
        dfwzvbscatJes07Up      .append(dfwzcat[x])
        dfwzvbscatJes08Up      .append(dfwzcat[x])
        dfwzvbscatJes09Up      .append(dfwzcat[x])
        dfwzvbscatJes10Up      .append(dfwzcat[x])
        dfwzvbscatJes11Up      .append(dfwzcat[x])
        dfwzvbscatJes12Up      .append(dfwzcat[x])
        dfwzvbscatJes13Up      .append(dfwzcat[x])
        dfwzvbscatJes14Up      .append(dfwzcat[x])
        dfwzvbscatJes15Up      .append(dfwzcat[x])
        dfwzvbscatJes16Up      .append(dfwzcat[x])
        dfwzvbscatJes17Up      .append(dfwzcat[x])
        dfwzvbscatJes18Up      .append(dfwzcat[x])
        dfwzvbscatJes19Up      .append(dfwzcat[x])
        dfwzvbscatJes20Up      .append(dfwzcat[x])
        dfwzvbscatJes21Up      .append(dfwzcat[x])
        dfwzvbscatJes22Up      .append(dfwzcat[x])
        dfwzvbscatJes23Up      .append(dfwzcat[x])
        dfwzvbscatJes24Up      .append(dfwzcat[x])
        dfwzvbscatJes25Up      .append(dfwzcat[x])
        dfwzvbscatJes26Up      .append(dfwzcat[x])
        dfwzvbscatJes27Up      .append(dfwzcat[x])
        dfwzvbscatJerUp        .append(dfwzcat[x])
        dfwzvbscatJERUp        .append(dfwzcat[x])
        dfwzvbscatJESUp        .append(dfwzcat[x])
        dfwzvbscatUnclusteredUp.append(dfwzcat[x])

        dfwzbvbscatMuonMomUp    .append(dfwzcat[x])
        dfwzbvbscatElectronMomUp.append(dfwzcat[x])
        dfwzbvbscatJes00Up      .append(dfwzcat[x])
        dfwzbvbscatJes01Up      .append(dfwzcat[x])
        dfwzbvbscatJes02Up      .append(dfwzcat[x])
        dfwzbvbscatJes03Up      .append(dfwzcat[x])
        dfwzbvbscatJes04Up      .append(dfwzcat[x])
        dfwzbvbscatJes05Up      .append(dfwzcat[x])
        dfwzbvbscatJes06Up      .append(dfwzcat[x])
        dfwzbvbscatJes07Up      .append(dfwzcat[x])
        dfwzbvbscatJes08Up      .append(dfwzcat[x])
        dfwzbvbscatJes09Up      .append(dfwzcat[x])
        dfwzbvbscatJes10Up      .append(dfwzcat[x])
        dfwzbvbscatJes11Up      .append(dfwzcat[x])
        dfwzbvbscatJes12Up      .append(dfwzcat[x])
        dfwzbvbscatJes13Up      .append(dfwzcat[x])
        dfwzbvbscatJes14Up      .append(dfwzcat[x])
        dfwzbvbscatJes15Up      .append(dfwzcat[x])
        dfwzbvbscatJes16Up      .append(dfwzcat[x])
        dfwzbvbscatJes17Up      .append(dfwzcat[x])
        dfwzbvbscatJes18Up      .append(dfwzcat[x])
        dfwzbvbscatJes19Up      .append(dfwzcat[x])
        dfwzbvbscatJes20Up      .append(dfwzcat[x])
        dfwzbvbscatJes21Up      .append(dfwzcat[x])
        dfwzbvbscatJes22Up      .append(dfwzcat[x])
        dfwzbvbscatJes23Up      .append(dfwzcat[x])
        dfwzbvbscatJes24Up      .append(dfwzcat[x])
        dfwzbvbscatJes25Up      .append(dfwzcat[x])
        dfwzbvbscatJes26Up      .append(dfwzcat[x])
        dfwzbvbscatJes27Up      .append(dfwzcat[x])
        dfwzbvbscatJerUp        .append(dfwzcat[x])
        dfwzbvbscatJERUp        .append(dfwzcat[x])
        dfwzbvbscatJESUp        .append(dfwzcat[x])
        dfwzbvbscatUnclusteredUp.append(dfwzcat[x])

        dfwzvbscatMuonMomUp     [x] = dfwzvbscatMuonMomUp     [x].Filter("mllZMuonMomUp     < 15 && m3lMuonMomUp     > 100 && ptlWMuonMomUp     > 20 && nbtag_goodbtag_Jet_bjet        == 0 && nvbs_jets	>= 2 && vbs_mjj        > 500 && vbs_detajj	  > 2.5 && vbs_zepvv	    < 1.0 && PuppiMET_ptDef	> {0}".format(metCut))
        dfwzvbscatElectronMomUp [x] = dfwzvbscatElectronMomUp [x].Filter("mllZElectronMomUp < 15 && m3lElectronMomUp > 100 && ptlWElectronMomUp > 20 && nbtag_goodbtag_Jet_bjet        == 0 && nvbs_jets	>= 2 && vbs_mjj        > 500 && vbs_detajj	  > 2.5 && vbs_zepvv	    < 1.0 && PuppiMET_ptDef	> {0}".format(metCut))
        dfwzvbscatJes00Up       [x] = dfwzvbscatJes00Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes00Up == 0 && nvbs_jetsJes00Up >= 2 && vbs_mjjJes00Up > 500 && vbs_detajjJes00Up > 2.5 && vbs_zepvvJes00Up < 1.0 && PuppiMET_ptJes00Up > {1}".format(altMass,metCut))
        dfwzvbscatJes01Up       [x] = dfwzvbscatJes01Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes01Up == 0 && nvbs_jetsJes01Up >= 2 && vbs_mjjJes01Up > 500 && vbs_detajjJes01Up > 2.5 && vbs_zepvvJes01Up < 1.0 && PuppiMET_ptJes01Up > {1}".format(altMass,metCut))
        dfwzvbscatJes02Up       [x] = dfwzvbscatJes02Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes02Up == 0 && nvbs_jetsJes02Up >= 2 && vbs_mjjJes02Up > 500 && vbs_detajjJes02Up > 2.5 && vbs_zepvvJes02Up < 1.0 && PuppiMET_ptJes02Up > {1}".format(altMass,metCut))
        dfwzvbscatJes03Up       [x] = dfwzvbscatJes03Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes03Up == 0 && nvbs_jetsJes03Up >= 2 && vbs_mjjJes03Up > 500 && vbs_detajjJes03Up > 2.5 && vbs_zepvvJes03Up < 1.0 && PuppiMET_ptJes03Up > {1}".format(altMass,metCut))
        dfwzvbscatJes04Up       [x] = dfwzvbscatJes04Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes04Up == 0 && nvbs_jetsJes04Up >= 2 && vbs_mjjJes04Up > 500 && vbs_detajjJes04Up > 2.5 && vbs_zepvvJes04Up < 1.0 && PuppiMET_ptJes04Up > {1}".format(altMass,metCut))
        dfwzvbscatJes05Up       [x] = dfwzvbscatJes05Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes05Up == 0 && nvbs_jetsJes05Up >= 2 && vbs_mjjJes05Up > 500 && vbs_detajjJes05Up > 2.5 && vbs_zepvvJes05Up < 1.0 && PuppiMET_ptJes05Up > {1}".format(altMass,metCut))
        dfwzvbscatJes06Up       [x] = dfwzvbscatJes06Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes06Up == 0 && nvbs_jetsJes06Up >= 2 && vbs_mjjJes06Up > 500 && vbs_detajjJes06Up > 2.5 && vbs_zepvvJes06Up < 1.0 && PuppiMET_ptJes06Up > {1}".format(altMass,metCut))
        dfwzvbscatJes07Up       [x] = dfwzvbscatJes07Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes07Up == 0 && nvbs_jetsJes07Up >= 2 && vbs_mjjJes07Up > 500 && vbs_detajjJes07Up > 2.5 && vbs_zepvvJes07Up < 1.0 && PuppiMET_ptJes07Up > {1}".format(altMass,metCut))
        dfwzvbscatJes08Up       [x] = dfwzvbscatJes08Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes08Up == 0 && nvbs_jetsJes08Up >= 2 && vbs_mjjJes08Up > 500 && vbs_detajjJes08Up > 2.5 && vbs_zepvvJes08Up < 1.0 && PuppiMET_ptJes08Up > {1}".format(altMass,metCut))
        dfwzvbscatJes09Up       [x] = dfwzvbscatJes09Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes09Up == 0 && nvbs_jetsJes09Up >= 2 && vbs_mjjJes09Up > 500 && vbs_detajjJes09Up > 2.5 && vbs_zepvvJes09Up < 1.0 && PuppiMET_ptJes09Up > {1}".format(altMass,metCut))
        dfwzvbscatJes10Up       [x] = dfwzvbscatJes10Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes10Up == 0 && nvbs_jetsJes10Up >= 2 && vbs_mjjJes10Up > 500 && vbs_detajjJes10Up > 2.5 && vbs_zepvvJes10Up < 1.0 && PuppiMET_ptJes10Up > {1}".format(altMass,metCut))
        dfwzvbscatJes11Up       [x] = dfwzvbscatJes11Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes11Up == 0 && nvbs_jetsJes11Up >= 2 && vbs_mjjJes11Up > 500 && vbs_detajjJes11Up > 2.5 && vbs_zepvvJes11Up < 1.0 && PuppiMET_ptJes11Up > {1}".format(altMass,metCut))
        dfwzvbscatJes12Up       [x] = dfwzvbscatJes12Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes12Up == 0 && nvbs_jetsJes12Up >= 2 && vbs_mjjJes12Up > 500 && vbs_detajjJes12Up > 2.5 && vbs_zepvvJes12Up < 1.0 && PuppiMET_ptJes12Up > {1}".format(altMass,metCut))
        dfwzvbscatJes13Up       [x] = dfwzvbscatJes13Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes13Up == 0 && nvbs_jetsJes13Up >= 2 && vbs_mjjJes13Up > 500 && vbs_detajjJes13Up > 2.5 && vbs_zepvvJes13Up < 1.0 && PuppiMET_ptJes13Up > {1}".format(altMass,metCut))
        dfwzvbscatJes14Up       [x] = dfwzvbscatJes14Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes14Up == 0 && nvbs_jetsJes14Up >= 2 && vbs_mjjJes14Up > 500 && vbs_detajjJes14Up > 2.5 && vbs_zepvvJes14Up < 1.0 && PuppiMET_ptJes14Up > {1}".format(altMass,metCut))
        dfwzvbscatJes15Up       [x] = dfwzvbscatJes15Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes15Up == 0 && nvbs_jetsJes15Up >= 2 && vbs_mjjJes15Up > 500 && vbs_detajjJes15Up > 2.5 && vbs_zepvvJes15Up < 1.0 && PuppiMET_ptJes15Up > {1}".format(altMass,metCut))
        dfwzvbscatJes16Up       [x] = dfwzvbscatJes16Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes16Up == 0 && nvbs_jetsJes16Up >= 2 && vbs_mjjJes16Up > 500 && vbs_detajjJes16Up > 2.5 && vbs_zepvvJes16Up < 1.0 && PuppiMET_ptJes16Up > {1}".format(altMass,metCut))
        dfwzvbscatJes17Up       [x] = dfwzvbscatJes17Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes17Up == 0 && nvbs_jetsJes17Up >= 2 && vbs_mjjJes17Up > 500 && vbs_detajjJes17Up > 2.5 && vbs_zepvvJes17Up < 1.0 && PuppiMET_ptJes17Up > {1}".format(altMass,metCut))
        dfwzvbscatJes18Up       [x] = dfwzvbscatJes18Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes18Up == 0 && nvbs_jetsJes18Up >= 2 && vbs_mjjJes18Up > 500 && vbs_detajjJes18Up > 2.5 && vbs_zepvvJes18Up < 1.0 && PuppiMET_ptJes18Up > {1}".format(altMass,metCut))
        dfwzvbscatJes19Up       [x] = dfwzvbscatJes19Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes19Up == 0 && nvbs_jetsJes19Up >= 2 && vbs_mjjJes19Up > 500 && vbs_detajjJes19Up > 2.5 && vbs_zepvvJes19Up < 1.0 && PuppiMET_ptJes19Up > {1}".format(altMass,metCut))
        dfwzvbscatJes20Up       [x] = dfwzvbscatJes20Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes20Up == 0 && nvbs_jetsJes20Up >= 2 && vbs_mjjJes20Up > 500 && vbs_detajjJes20Up > 2.5 && vbs_zepvvJes20Up < 1.0 && PuppiMET_ptJes20Up > {1}".format(altMass,metCut))
        dfwzvbscatJes21Up       [x] = dfwzvbscatJes21Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes21Up == 0 && nvbs_jetsJes21Up >= 2 && vbs_mjjJes21Up > 500 && vbs_detajjJes21Up > 2.5 && vbs_zepvvJes21Up < 1.0 && PuppiMET_ptJes21Up > {1}".format(altMass,metCut))
        dfwzvbscatJes22Up       [x] = dfwzvbscatJes22Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes22Up == 0 && nvbs_jetsJes22Up >= 2 && vbs_mjjJes22Up > 500 && vbs_detajjJes22Up > 2.5 && vbs_zepvvJes22Up < 1.0 && PuppiMET_ptJes22Up > {1}".format(altMass,metCut))
        dfwzvbscatJes23Up       [x] = dfwzvbscatJes23Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes23Up == 0 && nvbs_jetsJes23Up >= 2 && vbs_mjjJes23Up > 500 && vbs_detajjJes23Up > 2.5 && vbs_zepvvJes23Up < 1.0 && PuppiMET_ptJes23Up > {1}".format(altMass,metCut))
        dfwzvbscatJes24Up       [x] = dfwzvbscatJes24Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes24Up == 0 && nvbs_jetsJes24Up >= 2 && vbs_mjjJes24Up > 500 && vbs_detajjJes24Up > 2.5 && vbs_zepvvJes24Up < 1.0 && PuppiMET_ptJes24Up > {1}".format(altMass,metCut))
        dfwzvbscatJes25Up       [x] = dfwzvbscatJes25Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes25Up == 0 && nvbs_jetsJes25Up >= 2 && vbs_mjjJes25Up > 500 && vbs_detajjJes25Up > 2.5 && vbs_zepvvJes25Up < 1.0 && PuppiMET_ptJes25Up > {1}".format(altMass,metCut))
        dfwzvbscatJes26Up       [x] = dfwzvbscatJes26Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes26Up == 0 && nvbs_jetsJes26Up >= 2 && vbs_mjjJes26Up > 500 && vbs_detajjJes26Up > 2.5 && vbs_zepvvJes26Up < 1.0 && PuppiMET_ptJes26Up > {1}".format(altMass,metCut))
        dfwzvbscatJes27Up       [x] = dfwzvbscatJes27Up       [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes27Up == 0 && nvbs_jetsJes27Up >= 2 && vbs_mjjJes27Up > 500 && vbs_detajjJes27Up > 2.5 && vbs_zepvvJes27Up < 1.0 && PuppiMET_ptJes27Up > {1}".format(altMass,metCut))
        dfwzvbscatJerUp         [x] = dfwzvbscatJerUp         [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJerUp   == 0 && nvbs_jetsJerUp	>= 2 && vbs_mjjJerUp   > 500 && vbs_detajjJerUp   > 2.5 && vbs_zepvvJerUp   < 1.0 && PuppiMET_ptJerUp	> {1}".format(altMass,metCut))
        dfwzvbscatJERUp         [x] = dfwzvbscatJERUp         [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjet        == 0 && nvbs_jets	>= 2 && vbs_mjj        > 500 && vbs_detajj	  > 2.5 && vbs_zepvv	    < 1.0 && PuppiMET_ptDef	> {1}".format(altMass,metCut))
        dfwzvbscatJESUp         [x] = dfwzvbscatJESUp         [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjet        == 0 && nvbs_jets	>= 2 && vbs_mjj        > 500 && vbs_detajj	  > 2.5 && vbs_zepvv	    < 1.0 && PuppiMET_ptDef	> {1}".format(altMass,metCut))
        dfwzvbscatUnclusteredUp [x] = dfwzvbscatUnclusteredUp [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjet        == 0 && nvbs_jets	>= 2 && vbs_mjj        > 500 && vbs_detajj	  > 2.5 && vbs_zepvv	    < 1.0 && PuppiMET_ptUnclUp	> {1}".format(altMass,metCut))

        dfwzbvbscatMuonMomUp    [x] = dfwzbvbscatMuonMomUp    [x].Filter("mllZMuonMomUp     < 15 && m3lMuonMomUp     > 100 && ptlWMuonMomUp     > 20 && nbtag_goodbtag_Jet_bjet        >  0 && nvbs_jets	>= 2 && vbs_mjj        > 500 && vbs_detajj	  > 2.5 && vbs_zepvv	    < 1.0 && PuppiMET_ptDef	> {0}".format(metCut))
        dfwzbvbscatElectronMomUp[x] = dfwzbvbscatElectronMomUp[x].Filter("mllZElectronMomUp < 15 && m3lElectronMomUp > 100 && ptlWElectronMomUp > 20 && nbtag_goodbtag_Jet_bjet        >  0 && nvbs_jets	>= 2 && vbs_mjj        > 500 && vbs_detajj	  > 2.5 && vbs_zepvv	    < 1.0 && PuppiMET_ptDef	> {0}".format(metCut))
        dfwzbvbscatJes00Up      [x] = dfwzbvbscatJes00Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes00Up >  0 && nvbs_jetsJes00Up >= 2 && vbs_mjjJes00Up > 500 && vbs_detajjJes00Up > 2.5 && vbs_zepvvJes00Up < 1.0 && PuppiMET_ptJes00Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes01Up      [x] = dfwzbvbscatJes01Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes01Up >  0 && nvbs_jetsJes01Up >= 2 && vbs_mjjJes01Up > 500 && vbs_detajjJes01Up > 2.5 && vbs_zepvvJes01Up < 1.0 && PuppiMET_ptJes01Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes02Up      [x] = dfwzbvbscatJes02Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes02Up >  0 && nvbs_jetsJes02Up >= 2 && vbs_mjjJes02Up > 500 && vbs_detajjJes02Up > 2.5 && vbs_zepvvJes02Up < 1.0 && PuppiMET_ptJes02Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes03Up      [x] = dfwzbvbscatJes03Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes03Up >  0 && nvbs_jetsJes03Up >= 2 && vbs_mjjJes03Up > 500 && vbs_detajjJes03Up > 2.5 && vbs_zepvvJes03Up < 1.0 && PuppiMET_ptJes03Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes04Up      [x] = dfwzbvbscatJes04Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes04Up >  0 && nvbs_jetsJes04Up >= 2 && vbs_mjjJes04Up > 500 && vbs_detajjJes04Up > 2.5 && vbs_zepvvJes04Up < 1.0 && PuppiMET_ptJes04Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes05Up      [x] = dfwzbvbscatJes05Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes05Up >  0 && nvbs_jetsJes05Up >= 2 && vbs_mjjJes05Up > 500 && vbs_detajjJes05Up > 2.5 && vbs_zepvvJes05Up < 1.0 && PuppiMET_ptJes05Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes06Up      [x] = dfwzbvbscatJes06Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes06Up >  0 && nvbs_jetsJes06Up >= 2 && vbs_mjjJes06Up > 500 && vbs_detajjJes06Up > 2.5 && vbs_zepvvJes06Up < 1.0 && PuppiMET_ptJes06Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes07Up      [x] = dfwzbvbscatJes07Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes07Up >  0 && nvbs_jetsJes07Up >= 2 && vbs_mjjJes07Up > 500 && vbs_detajjJes07Up > 2.5 && vbs_zepvvJes07Up < 1.0 && PuppiMET_ptJes07Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes08Up      [x] = dfwzbvbscatJes08Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes08Up >  0 && nvbs_jetsJes08Up >= 2 && vbs_mjjJes08Up > 500 && vbs_detajjJes08Up > 2.5 && vbs_zepvvJes08Up < 1.0 && PuppiMET_ptJes08Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes09Up      [x] = dfwzbvbscatJes09Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes09Up >  0 && nvbs_jetsJes09Up >= 2 && vbs_mjjJes09Up > 500 && vbs_detajjJes09Up > 2.5 && vbs_zepvvJes09Up < 1.0 && PuppiMET_ptJes09Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes10Up      [x] = dfwzbvbscatJes10Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes10Up >  0 && nvbs_jetsJes10Up >= 2 && vbs_mjjJes10Up > 500 && vbs_detajjJes10Up > 2.5 && vbs_zepvvJes10Up < 1.0 && PuppiMET_ptJes10Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes11Up      [x] = dfwzbvbscatJes11Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes11Up >  0 && nvbs_jetsJes11Up >= 2 && vbs_mjjJes11Up > 500 && vbs_detajjJes11Up > 2.5 && vbs_zepvvJes11Up < 1.0 && PuppiMET_ptJes11Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes12Up      [x] = dfwzbvbscatJes12Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes12Up >  0 && nvbs_jetsJes12Up >= 2 && vbs_mjjJes12Up > 500 && vbs_detajjJes12Up > 2.5 && vbs_zepvvJes12Up < 1.0 && PuppiMET_ptJes12Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes13Up      [x] = dfwzbvbscatJes13Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes13Up >  0 && nvbs_jetsJes13Up >= 2 && vbs_mjjJes13Up > 500 && vbs_detajjJes13Up > 2.5 && vbs_zepvvJes13Up < 1.0 && PuppiMET_ptJes13Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes14Up      [x] = dfwzbvbscatJes14Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes14Up >  0 && nvbs_jetsJes14Up >= 2 && vbs_mjjJes14Up > 500 && vbs_detajjJes14Up > 2.5 && vbs_zepvvJes14Up < 1.0 && PuppiMET_ptJes14Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes15Up      [x] = dfwzbvbscatJes15Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes15Up >  0 && nvbs_jetsJes15Up >= 2 && vbs_mjjJes15Up > 500 && vbs_detajjJes15Up > 2.5 && vbs_zepvvJes15Up < 1.0 && PuppiMET_ptJes15Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes16Up      [x] = dfwzbvbscatJes16Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes16Up >  0 && nvbs_jetsJes16Up >= 2 && vbs_mjjJes16Up > 500 && vbs_detajjJes16Up > 2.5 && vbs_zepvvJes16Up < 1.0 && PuppiMET_ptJes16Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes17Up      [x] = dfwzbvbscatJes17Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes17Up >  0 && nvbs_jetsJes17Up >= 2 && vbs_mjjJes17Up > 500 && vbs_detajjJes17Up > 2.5 && vbs_zepvvJes17Up < 1.0 && PuppiMET_ptJes17Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes18Up      [x] = dfwzbvbscatJes18Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes18Up >  0 && nvbs_jetsJes18Up >= 2 && vbs_mjjJes18Up > 500 && vbs_detajjJes18Up > 2.5 && vbs_zepvvJes18Up < 1.0 && PuppiMET_ptJes18Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes19Up      [x] = dfwzbvbscatJes19Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes19Up >  0 && nvbs_jetsJes19Up >= 2 && vbs_mjjJes19Up > 500 && vbs_detajjJes19Up > 2.5 && vbs_zepvvJes19Up < 1.0 && PuppiMET_ptJes19Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes20Up      [x] = dfwzbvbscatJes20Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes20Up >  0 && nvbs_jetsJes20Up >= 2 && vbs_mjjJes20Up > 500 && vbs_detajjJes20Up > 2.5 && vbs_zepvvJes20Up < 1.0 && PuppiMET_ptJes20Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes21Up      [x] = dfwzbvbscatJes21Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes21Up >  0 && nvbs_jetsJes21Up >= 2 && vbs_mjjJes21Up > 500 && vbs_detajjJes21Up > 2.5 && vbs_zepvvJes21Up < 1.0 && PuppiMET_ptJes21Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes22Up      [x] = dfwzbvbscatJes22Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes22Up >  0 && nvbs_jetsJes22Up >= 2 && vbs_mjjJes22Up > 500 && vbs_detajjJes22Up > 2.5 && vbs_zepvvJes22Up < 1.0 && PuppiMET_ptJes22Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes23Up      [x] = dfwzbvbscatJes23Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes23Up >  0 && nvbs_jetsJes23Up >= 2 && vbs_mjjJes23Up > 500 && vbs_detajjJes23Up > 2.5 && vbs_zepvvJes23Up < 1.0 && PuppiMET_ptJes23Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes24Up      [x] = dfwzbvbscatJes24Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes24Up >  0 && nvbs_jetsJes24Up >= 2 && vbs_mjjJes24Up > 500 && vbs_detajjJes24Up > 2.5 && vbs_zepvvJes24Up < 1.0 && PuppiMET_ptJes24Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes25Up      [x] = dfwzbvbscatJes25Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes25Up >  0 && nvbs_jetsJes25Up >= 2 && vbs_mjjJes25Up > 500 && vbs_detajjJes25Up > 2.5 && vbs_zepvvJes25Up < 1.0 && PuppiMET_ptJes25Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes26Up      [x] = dfwzbvbscatJes26Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes26Up >  0 && nvbs_jetsJes26Up >= 2 && vbs_mjjJes26Up > 500 && vbs_detajjJes26Up > 2.5 && vbs_zepvvJes26Up < 1.0 && PuppiMET_ptJes26Up > {1}".format(altMass,metCut))
        dfwzbvbscatJes27Up      [x] = dfwzbvbscatJes27Up      [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJes27Up >  0 && nvbs_jetsJes27Up >= 2 && vbs_mjjJes27Up > 500 && vbs_detajjJes27Up > 2.5 && vbs_zepvvJes27Up < 1.0 && PuppiMET_ptJes27Up > {1}".format(altMass,metCut))
        dfwzbvbscatJerUp        [x] = dfwzbvbscatJerUp        [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjetJerUp   >  0 && nvbs_jetsJerUp	>= 2 && vbs_mjjJerUp   > 500 && vbs_detajjJerUp   > 2.5 && vbs_zepvvJerUp   < 1.0 && PuppiMET_ptJerUp	> {1}".format(altMass,metCut))
        dfwzbvbscatJERUp        [x] = dfwzbvbscatJERUp        [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjet        >  0 && nvbs_jets	>= 2 && vbs_mjj        > 500 && vbs_detajj	  > 2.5 && vbs_zepvv	    < 1.0 && PuppiMET_ptDef	> {1}".format(altMass,metCut))
        dfwzbvbscatJESUp        [x] = dfwzbvbscatJESUp        [x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjet        >  0 && nvbs_jets	>= 2 && vbs_mjj        > 500 && vbs_detajj	  > 2.5 && vbs_zepvv	    < 1.0 && PuppiMET_ptDef	> {1}".format(altMass,metCut))
        dfwzbvbscatUnclusteredUp[x] = dfwzbvbscatUnclusteredUp[x].Filter("mllZ{0}           < 15 && m3l{0}           > 100 && ptlW{0}           > 20 && nbtag_goodbtag_Jet_bjet        >  0 && nvbs_jets	>= 2 && vbs_mjj        > 500 && vbs_detajj	  > 2.5 && vbs_zepvv	    < 1.0 && PuppiMET_ptUnclUp	> {1}".format(altMass,metCut))

        if(tmva_helper is not None):
            dfwzvbscatJes00Up[x] = redefineMVAVariables(dfwzvbscatJes00Up[x],tmva_helper,"Jes00Up",versionMVA)
            dfwzvbscatJes01Up[x] = redefineMVAVariables(dfwzvbscatJes01Up[x],tmva_helper,"Jes01Up",versionMVA)
            dfwzvbscatJes02Up[x] = redefineMVAVariables(dfwzvbscatJes02Up[x],tmva_helper,"Jes02Up",versionMVA)
            dfwzvbscatJes03Up[x] = redefineMVAVariables(dfwzvbscatJes03Up[x],tmva_helper,"Jes03Up",versionMVA)
            dfwzvbscatJes04Up[x] = redefineMVAVariables(dfwzvbscatJes04Up[x],tmva_helper,"Jes04Up",versionMVA)
            dfwzvbscatJes05Up[x] = redefineMVAVariables(dfwzvbscatJes05Up[x],tmva_helper,"Jes05Up",versionMVA)
            dfwzvbscatJes06Up[x] = redefineMVAVariables(dfwzvbscatJes06Up[x],tmva_helper,"Jes06Up",versionMVA)
            dfwzvbscatJes07Up[x] = redefineMVAVariables(dfwzvbscatJes07Up[x],tmva_helper,"Jes07Up",versionMVA)
            dfwzvbscatJes08Up[x] = redefineMVAVariables(dfwzvbscatJes08Up[x],tmva_helper,"Jes08Up",versionMVA)
            dfwzvbscatJes09Up[x] = redefineMVAVariables(dfwzvbscatJes09Up[x],tmva_helper,"Jes09Up",versionMVA)
            dfwzvbscatJes10Up[x] = redefineMVAVariables(dfwzvbscatJes10Up[x],tmva_helper,"Jes10Up",versionMVA)
            dfwzvbscatJes11Up[x] = redefineMVAVariables(dfwzvbscatJes11Up[x],tmva_helper,"Jes11Up",versionMVA)
            dfwzvbscatJes12Up[x] = redefineMVAVariables(dfwzvbscatJes12Up[x],tmva_helper,"Jes12Up",versionMVA)
            dfwzvbscatJes13Up[x] = redefineMVAVariables(dfwzvbscatJes13Up[x],tmva_helper,"Jes13Up",versionMVA)
            dfwzvbscatJes14Up[x] = redefineMVAVariables(dfwzvbscatJes14Up[x],tmva_helper,"Jes14Up",versionMVA)
            dfwzvbscatJes15Up[x] = redefineMVAVariables(dfwzvbscatJes15Up[x],tmva_helper,"Jes15Up",versionMVA)
            dfwzvbscatJes16Up[x] = redefineMVAVariables(dfwzvbscatJes16Up[x],tmva_helper,"Jes16Up",versionMVA)
            dfwzvbscatJes17Up[x] = redefineMVAVariables(dfwzvbscatJes17Up[x],tmva_helper,"Jes17Up",versionMVA)
            dfwzvbscatJes18Up[x] = redefineMVAVariables(dfwzvbscatJes18Up[x],tmva_helper,"Jes18Up",versionMVA)
            dfwzvbscatJes19Up[x] = redefineMVAVariables(dfwzvbscatJes19Up[x],tmva_helper,"Jes19Up",versionMVA)
            dfwzvbscatJes20Up[x] = redefineMVAVariables(dfwzvbscatJes20Up[x],tmva_helper,"Jes20Up",versionMVA)
            dfwzvbscatJes21Up[x] = redefineMVAVariables(dfwzvbscatJes21Up[x],tmva_helper,"Jes21Up",versionMVA)
            dfwzvbscatJes22Up[x] = redefineMVAVariables(dfwzvbscatJes22Up[x],tmva_helper,"Jes22Up",versionMVA)
            dfwzvbscatJes23Up[x] = redefineMVAVariables(dfwzvbscatJes23Up[x],tmva_helper,"Jes23Up",versionMVA)
            dfwzvbscatJes24Up[x] = redefineMVAVariables(dfwzvbscatJes24Up[x],tmva_helper,"Jes24Up",versionMVA)
            dfwzvbscatJes25Up[x] = redefineMVAVariables(dfwzvbscatJes25Up[x],tmva_helper,"Jes25Up",versionMVA)
            dfwzvbscatJes26Up[x] = redefineMVAVariables(dfwzvbscatJes26Up[x],tmva_helper,"Jes26Up",versionMVA)
            dfwzvbscatJes27Up[x] = redefineMVAVariables(dfwzvbscatJes27Up[x],tmva_helper,"Jes27Up",versionMVA)
            dfwzvbscatJerUp  [x] = redefineMVAVariables(dfwzvbscatJerUp  [x],tmva_helper,"JerUp"  ,versionMVA)

            dfwzbvbscatJes00Up[x] = redefineMVAVariables(dfwzbvbscatJes00Up[x],tmva_helper,"Jes00Up",versionMVA)
            dfwzbvbscatJes01Up[x] = redefineMVAVariables(dfwzbvbscatJes01Up[x],tmva_helper,"Jes01Up",versionMVA)
            dfwzbvbscatJes02Up[x] = redefineMVAVariables(dfwzbvbscatJes02Up[x],tmva_helper,"Jes02Up",versionMVA)
            dfwzbvbscatJes03Up[x] = redefineMVAVariables(dfwzbvbscatJes03Up[x],tmva_helper,"Jes03Up",versionMVA)
            dfwzbvbscatJes04Up[x] = redefineMVAVariables(dfwzbvbscatJes04Up[x],tmva_helper,"Jes04Up",versionMVA)
            dfwzbvbscatJes05Up[x] = redefineMVAVariables(dfwzbvbscatJes05Up[x],tmva_helper,"Jes05Up",versionMVA)
            dfwzbvbscatJes06Up[x] = redefineMVAVariables(dfwzbvbscatJes06Up[x],tmva_helper,"Jes06Up",versionMVA)
            dfwzbvbscatJes07Up[x] = redefineMVAVariables(dfwzbvbscatJes07Up[x],tmva_helper,"Jes07Up",versionMVA)
            dfwzbvbscatJes08Up[x] = redefineMVAVariables(dfwzbvbscatJes08Up[x],tmva_helper,"Jes08Up",versionMVA)
            dfwzbvbscatJes09Up[x] = redefineMVAVariables(dfwzbvbscatJes09Up[x],tmva_helper,"Jes09Up",versionMVA)
            dfwzbvbscatJes10Up[x] = redefineMVAVariables(dfwzbvbscatJes10Up[x],tmva_helper,"Jes10Up",versionMVA)
            dfwzbvbscatJes11Up[x] = redefineMVAVariables(dfwzbvbscatJes11Up[x],tmva_helper,"Jes11Up",versionMVA)
            dfwzbvbscatJes12Up[x] = redefineMVAVariables(dfwzbvbscatJes12Up[x],tmva_helper,"Jes12Up",versionMVA)
            dfwzbvbscatJes13Up[x] = redefineMVAVariables(dfwzbvbscatJes13Up[x],tmva_helper,"Jes13Up",versionMVA)
            dfwzbvbscatJes14Up[x] = redefineMVAVariables(dfwzbvbscatJes14Up[x],tmva_helper,"Jes14Up",versionMVA)
            dfwzbvbscatJes15Up[x] = redefineMVAVariables(dfwzbvbscatJes15Up[x],tmva_helper,"Jes15Up",versionMVA)
            dfwzbvbscatJes16Up[x] = redefineMVAVariables(dfwzbvbscatJes16Up[x],tmva_helper,"Jes16Up",versionMVA)
            dfwzbvbscatJes17Up[x] = redefineMVAVariables(dfwzbvbscatJes17Up[x],tmva_helper,"Jes17Up",versionMVA)
            dfwzbvbscatJes18Up[x] = redefineMVAVariables(dfwzbvbscatJes18Up[x],tmva_helper,"Jes18Up",versionMVA)
            dfwzbvbscatJes19Up[x] = redefineMVAVariables(dfwzbvbscatJes19Up[x],tmva_helper,"Jes19Up",versionMVA)
            dfwzbvbscatJes20Up[x] = redefineMVAVariables(dfwzbvbscatJes20Up[x],tmva_helper,"Jes20Up",versionMVA)
            dfwzbvbscatJes21Up[x] = redefineMVAVariables(dfwzbvbscatJes21Up[x],tmva_helper,"Jes21Up",versionMVA)
            dfwzbvbscatJes22Up[x] = redefineMVAVariables(dfwzbvbscatJes22Up[x],tmva_helper,"Jes22Up",versionMVA)
            dfwzbvbscatJes23Up[x] = redefineMVAVariables(dfwzbvbscatJes23Up[x],tmva_helper,"Jes23Up",versionMVA)
            dfwzbvbscatJes24Up[x] = redefineMVAVariables(dfwzbvbscatJes24Up[x],tmva_helper,"Jes24Up",versionMVA)
            dfwzbvbscatJes25Up[x] = redefineMVAVariables(dfwzbvbscatJes25Up[x],tmva_helper,"Jes25Up",versionMVA)
            dfwzbvbscatJes26Up[x] = redefineMVAVariables(dfwzbvbscatJes26Up[x],tmva_helper,"Jes26Up",versionMVA)
            dfwzbvbscatJes27Up[x] = redefineMVAVariables(dfwzbvbscatJes27Up[x],tmva_helper,"Jes27Up",versionMVA)
            dfwzbvbscatJerUp  [x] = redefineMVAVariables(dfwzbvbscatJerUp  [x],tmva_helper,"JerUp"  ,versionMVA)
 
        if(makeDataCards >= 3):
            dfwzcat[x] = dfwzcat[x].Filter("nvbs_jets >= 2 && vbs_mjj > 150")

        dfzgcat.append(dfwzcat[x].Filter("mll{0} > 10 && mll{0} < 110 && ptl1Z{0} > 25 && ptl2Z{0} > 20 && ptlW{0} > 20".format(altMass)))

        dfwhcat.append(dfwzcat[x].Filter("mll{0} == -1 && mllmin{0} > 10".format(altMass)))

        dfwzcat[x] = dfwzcat[x].Filter("mll{0} > 0".format(altMass),"mll > 0")

        histo[ 0][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format( 0,x), "histo_{0}_{1}".format( 0,x),120,  0, 120), "mllmin{0}".format(altMass),"weightNoBTag")
        dfwzcat[x] = dfwzcat[x].Filter("mllmin{0} > 1".format(altMass),"mllmin cut")

        dfEMMcat.append(dfwzcat[x].Filter("TriLepton_flavor == 1 && triggerSEL > 0 && fake_Electron_pt[0] > 30")
                                  .Define("pttag","Max(fake_Electron_pt)")
                                  .Define("ptmax","Max(fake_Muon_pt)")
                                  .Define("ptmin","Min(fake_Muon_pt)")
                                  )
        dfMEEcat.append(dfwzcat[x].Filter("TriLepton_flavor == 2 && triggerSMU > 0 && fake_Muon_pt[0] > 30")
                                  .Define("pttag","Max(fake_Muon_pt)")
                                  .Define("ptmax","Max(fake_Electron_pt)")
                                  .Define("ptmin","Min(fake_Electron_pt)")
                                  )
        histo[61][x] = dfEMMcat[x].Histo1D(("histo_{0}_{1}".format(61,x), "histo_{0}_{1}".format(61,x), 20, 30, 130), "pttag","weightNoBTag")
        histo[62][x] = dfMEEcat[x].Histo1D(("histo_{0}_{1}".format(62,x), "histo_{0}_{1}".format(62,x), 20, 30, 130), "pttag","weightNoBTag")

        dfEMMcat[x] = dfEMMcat[x].Filter("hasTriggerMatch(fake_Electron_eta[0],fake_Electron_phi[0],TrigObj_eta,TrigObj_phi,TrigObj_id,TrigObj_filterBits,11,1)")
        dfMEEcat[x] = dfMEEcat[x].Filter("hasTriggerMatch(fake_Muon_eta[0],fake_Muon_phi[0],TrigObj_eta,TrigObj_phi,TrigObj_id,TrigObj_filterBits,13,1)")

        histo[63][x] = dfEMMcat[x].Histo1D(("histo_{0}_{1}".format(63,x), "histo_{0}_{1}".format(63,x), 20, 30, 130), "pttag","weightNoBTag")
        histo[64][x] = dfMEEcat[x].Histo1D(("histo_{0}_{1}".format(64,x), "histo_{0}_{1}".format(64,x), 20, 30, 130), "pttag","weightNoBTag")

        histo[65][x] = dfEMMcat[x].Histo1D(("histo_{0}_{1}".format(65,x), "histo_{0}_{1}".format(65,x), len(xPtTrgBins)-1, xPtTrgBins), "ptmax","weightNoBTag")
        histo[66][x] = dfEMMcat[x].Histo1D(("histo_{0}_{1}".format(66,x), "histo_{0}_{1}".format(66,x), len(xPtTrgBins)-1, xPtTrgBins), "ptmin","weightNoBTag")
        histo[67][x] = dfMEEcat[x].Histo1D(("histo_{0}_{1}".format(67,x), "histo_{0}_{1}".format(67,x), len(xPtTrgBins)-1, xPtTrgBins), "ptmax","weightNoBTag")
        histo[68][x] = dfMEEcat[x].Histo1D(("histo_{0}_{1}".format(68,x), "histo_{0}_{1}".format(68,x), len(xPtTrgBins)-1, xPtTrgBins), "ptmin","weightNoBTag")

        dfEMMcat[x] = dfEMMcat[x].Filter("triggerDMU > 0")
        dfMEEcat[x] = dfMEEcat[x].Filter("triggerDEL > 0")

        histo[69][x] = dfEMMcat[x].Histo1D(("histo_{0}_{1}".format(69,x), "histo_{0}_{1}".format(69,x), len(xPtTrgBins)-1, xPtTrgBins), "ptmax","weightNoBTag")
        histo[70][x] = dfEMMcat[x].Histo1D(("histo_{0}_{1}".format(70,x), "histo_{0}_{1}".format(70,x), len(xPtTrgBins)-1, xPtTrgBins), "ptmin","weightNoBTag")
        histo[71][x] = dfMEEcat[x].Histo1D(("histo_{0}_{1}".format(71,x), "histo_{0}_{1}".format(71,x), len(xPtTrgBins)-1, xPtTrgBins), "ptmax","weightNoBTag")
        histo[72][x] = dfMEEcat[x].Histo1D(("histo_{0}_{1}".format(72,x), "histo_{0}_{1}".format(72,x), len(xPtTrgBins)-1, xPtTrgBins), "ptmin","weightNoBTag")

        dfwzcatMuonMomUp     .append(dfwzcat[x])
        dfwzcatElectronMomUp .append(dfwzcat[x])
        dfwzbcatMuonMomUp    .append(dfwzcat[x])
        dfwzbcatElectronMomUp.append(dfwzcat[x])

        histo[ 1][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format( 1,x), "histo_{0}_{1}".format( 1,x),100,  0, 100), "mllZ{0}".format(altMass),"weightNoBTag")
        dfwzcat                [x] = dfwzcat                [x].Filter("mllZ{0}             < 15".format(altMass),"mllZ cut")
        dfwzcatMuonMomUp       [x] = dfwzcatMuonMomUp       [x].Filter("mllZMuonMomUp       < 15")
        dfwzcatElectronMomUp   [x] = dfwzcatElectronMomUp   [x].Filter("mllZElectronMomUp   < 15")
        dfwzbcatMuonMomUp      [x] = dfwzbcatMuonMomUp      [x].Filter("mllZMuonMomUp       < 15")
        dfwzbcatElectronMomUp  [x] = dfwzbcatElectronMomUp  [x].Filter("mllZElectronMomUp   < 15")

        histo[ 2][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format( 2,x), "histo_{0}_{1}".format( 2,x), 50, 70, 270), "m3l{0}".format(altMass),"weightNoBTag")
        dfwzcat                [x] = dfwzcat                [x].Filter("m3l{0}             > 100".format(altMass),"m3l cut")
        dfwzcatMuonMomUp       [x] = dfwzcatMuonMomUp       [x].Filter("m3lMuonMomUp       > 100")
        dfwzcatElectronMomUp   [x] = dfwzcatElectronMomUp   [x].Filter("m3lElectronMomUp   > 100")
        dfwzbcatMuonMomUp      [x] = dfwzbcatMuonMomUp      [x].Filter("m3lMuonMomUp       > 100")
        dfwzbcatElectronMomUp  [x] = dfwzbcatElectronMomUp  [x].Filter("m3lElectronMomUp   > 100")

        histo[73][x] = dfwzcat[x].Filter("(TriLepton_flavor==0||TriLepton_flavor==2) && ptlW{0} < 110".format(altMass)).Histo1D(("histo_{0}_{1}".format(73,x), "histo_{0}_{1}".format(73,x),40, 10, 110), "ptlW{0}".format(altMass),"weight")
        histo[74][x] = dfwzcat[x].Filter("(TriLepton_flavor==1||TriLepton_flavor==3) && ptlW{0} < 110".format(altMass)).Histo1D(("histo_{0}_{1}".format(74,x), "histo_{0}_{1}".format(74,x),40, 10, 110), "ptlW{0}".format(altMass),"weight")
        histo[75][x] = dfwzcat[x].Filter("(TriLepton_flavor==0||TriLepton_flavor==2) && ptlW{0} < 40".format(altMass)).Histo1D(("histo_{0}_{1}".format(75,x), "histo_{0}_{1}".format(75,x),25, 0.0, 2.5), "etalW","weight")
        histo[76][x] = dfwzcat[x].Filter("(TriLepton_flavor==1||TriLepton_flavor==3) && ptlW{0} < 40".format(altMass)).Histo1D(("histo_{0}_{1}".format(76,x), "histo_{0}_{1}".format(76,x),25, 0.0, 2.5), "etalW","weight")

        histo[77][x] = dfsscat[x].Histo1D(("histo_{0}_{1}".format(77,x), "histo_{0}_{1}".format(77,x), 4,-0.5, 3.5), "TriLepton_flavor","weightNoBTag")
        histo[78][x] = dfsscat[x].Histo1D(("histo_{0}_{1}".format(78,x), "histo_{0}_{1}".format(78,x),60,  0, 120), "mllAllmin{0}".format(altMass),"weightNoBTag")
        histo[79][x] = dfsscat[x].Histo1D(("histo_{0}_{1}".format(79,x), "histo_{0}_{1}".format(79,x),40,  0, 40), "mllSSZ{0}".format(altMass),"weightNoBTag")
        histo[80][x] = dfsscat[x].Histo1D(("histo_{0}_{1}".format(80,x), "histo_{0}_{1}".format(80,x),20, 10, 110), "ptl3{0}".format(altMass),"weightNoBTag")

        dfsscat[x] = dfsscat[x].Filter("Sum(fake_el) == 0 or Min(fake_Electron_tightCharge) == 2")
        histo[81][x] = dfsscat[x].Histo1D(("histo_{0}_{1}".format(81,x), "histo_{0}_{1}".format(81,x), 4,-0.5, 3.5), "TriLepton_flavor","weightNoBTag")
        histo[82][x] = dfsscat[x].Histo1D(("histo_{0}_{1}".format(82,x), "histo_{0}_{1}".format(82,x),40,  0, 40), "mllSSZ{0}".format(altMass),"weightNoBTag")
        dfsscat[x] = dfsscat[x].Filter("mllSSZ{0} > 15".format(altMass))
        histo[83][x] = dfsscat[x].Histo1D(("histo_{0}_{1}".format(83,x), "histo_{0}_{1}".format(83,x), 4,-0.5, 3.5), "TriLepton_flavor","weightNoBTag")

        histo[ 3][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format( 3,x), "histo_{0}_{1}".format( 3,x), 50, 10, 210), "ptlW{0}".format(altMass),"weightNoBTag")
        dfwzcat                [x] = dfwzcat                [x].Filter("ptlW{0}             > 20".format(altMass),"ptlW cut")
        dfwzcatMuonMomUp       [x] = dfwzcatMuonMomUp       [x].Filter("ptlWMuonMomUp       > 20")
        dfwzcatElectronMomUp   [x] = dfwzcatElectronMomUp   [x].Filter("ptlWElectronMomUp   > 20")
        dfwzbcatMuonMomUp      [x] = dfwzbcatMuonMomUp      [x].Filter("ptlWMuonMomUp       > 20")
        dfwzbcatElectronMomUp  [x] = dfwzbcatElectronMomUp  [x].Filter("ptlWElectronMomUp   > 20")

        dfwzbcat.append(dfwzcat[x].Filter("nbtag_goodbtag_Jet_bjet > 0","at least one good b-jet"))

        histo[ 4][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format( 4,x), "histo_{0}_{1}".format( 4,x), 4,-0.5 ,3.5), "nbtag_goodbtag_Jet_bjet","weight")
        dfwzcat[x]                 = dfwzcat                [x].Filter("nbtag_goodbtag_Jet_bjet == 0","no good b-jets")
        dfwzcatMuonMomUp       [x] = dfwzcatMuonMomUp       [x].Filter("nbtag_goodbtag_Jet_bjet == 0")
        dfwzcatElectronMomUp   [x] = dfwzcatElectronMomUp   [x].Filter("nbtag_goodbtag_Jet_bjet == 0")
        dfwzbcatMuonMomUp      [x] = dfwzbcatMuonMomUp      [x].Filter("nbtag_goodbtag_Jet_bjet > 0")
        dfwzbcatElectronMomUp  [x] = dfwzbcatElectronMomUp  [x].Filter("nbtag_goodbtag_Jet_bjet > 0")

        histo[15][x] = dfwzcat[x] .Histo1D(("histo_{0}_{1}".format(15,x), "histo_{0}_{1}".format(15,x), 40,  0, 200), "PuppiMET_pt{0}".format(altMass),"weight")
        histo[16][x] = dfwzbcat[x].Histo1D(("histo_{0}_{1}".format(16,x), "histo_{0}_{1}".format(16,x), 40,  0, 200), "PuppiMET_pt{0}".format(altMass),"weight")

        histo[29][x] = dfwzcat[x] .Histo1D(("histo_{0}_{1}".format(29,x), "histo_{0}_{1}".format(29,x), 40,  0, 200), "PuppiMET_ptUnclUp","weight")
        histo[30][x] = dfwzbcat[x].Histo1D(("histo_{0}_{1}".format(30,x), "histo_{0}_{1}".format(30,x), 40,  0, 200), "PuppiMET_ptUnclUp","weight")

        dfwzcatJERUp          .append(dfwzcat[x].Filter("PuppiMET_ptDef    > {0}".format(metCut)))
        dfwzcatJESUp          .append(dfwzcat[x].Filter("PuppiMET_ptDef    > {0}".format(metCut)))
        dfwzcatUnclusteredUp  .append(dfwzcat[x].Filter("PuppiMET_ptUnclUp > {0}".format(metCut)))

        dfwzbcatJERUp          .append(dfwzbcat[x].Filter("PuppiMET_ptDef    > {0}".format(metCut)))
        dfwzbcatJESUp          .append(dfwzbcat[x].Filter("PuppiMET_ptDef    > {0}".format(metCut)))
        dfwzbcatUnclusteredUp  .append(dfwzbcat[x].Filter("PuppiMET_ptUnclUp > {0}".format(metCut)))

        dfwzcat[x]                 = dfwzcat                [x].Filter("PuppiMET_ptDef > {0}".format(metCut),"PuppiMET_pt > {0}".format(metCut))
        dfwzcatMuonMomUp       [x] = dfwzcatMuonMomUp       [x].Filter("PuppiMET_ptDef > {0}".format(metCut))
        dfwzcatElectronMomUp   [x] = dfwzcatElectronMomUp   [x].Filter("PuppiMET_ptDef > {0}".format(metCut))
        dfwzbcat[x]                = dfwzbcat               [x].Filter("PuppiMET_ptDef > {0}".format(metCut),"PuppiMET_pt > {0}".format(metCut))
        dfwzbcatMuonMomUp      [x] = dfwzbcatMuonMomUp      [x].Filter("PuppiMET_ptDef > {0}".format(metCut))
        dfwzbcatElectronMomUp  [x] = dfwzbcatElectronMomUp  [x].Filter("PuppiMET_ptDef > {0}".format(metCut))

        histo[ 5][x] = dfwzcat[x] .Histo1D(("histo_{0}_{1}".format( 5,x), "histo_{0}_{1}".format( 5,x), 40, 25, 225), "ptl1Z{0}".format(altMass),"weight")
        histo[ 6][x] = dfwzbcat[x].Histo1D(("histo_{0}_{1}".format( 6,x), "histo_{0}_{1}".format( 6,x), 40, 25, 225), "ptl1Z{0}".format(altMass),"weight")
        histo[ 7][x] = dfwzcat[x] .Histo1D(("histo_{0}_{1}".format( 7,x), "histo_{0}_{1}".format( 7,x), 40, 10, 210), "ptl2Z{0}".format(altMass),"weight")
        histo[ 8][x] = dfwzbcat[x].Histo1D(("histo_{0}_{1}".format( 8,x), "histo_{0}_{1}".format( 8,x), 40, 10, 210), "ptl2Z{0}".format(altMass),"weight")
        histo[ 9][x] = dfwzcat[x] .Histo1D(("histo_{0}_{1}".format( 9,x), "histo_{0}_{1}".format( 9,x), 40,  0, 200), "mtW{0}".format(altMass),"weight")
        histo[10][x] = dfwzbcat[x].Histo1D(("histo_{0}_{1}".format(10,x), "histo_{0}_{1}".format(10,x), 40,  0, 200), "mtW{0}".format(altMass),"weight")
        histo[11][x] = dfwzcat[x] .Histo1D(("histo_{0}_{1}".format(11,x), "histo_{0}_{1}".format(11,x), 4,-0.5, 3.5), "TriLepton_flavor","weight")
        histo[12][x] = dfwzbcat[x].Histo1D(("histo_{0}_{1}".format(12,x), "histo_{0}_{1}".format(12,x), 4,-0.5, 3.5), "TriLepton_flavor","weight")
        histo[13][x] = dfwzcat[x] .Histo1D(("histo_{0}_{1}".format(13,x), "histo_{0}_{1}".format(13,x), 4,-0.5, 3.5), "ngood_jets","weight")
        histo[14][x] = dfwzbcat[x].Histo1D(("histo_{0}_{1}".format(14,x), "histo_{0}_{1}".format(14,x), 4,-0.5, 3.5), "ngood_jets","weight")

        dfwzjjcat .append(dfwzcat[x] .Filter(VBSQCDSEL, "VBS QCD selection"))
        dfwzbjjcat.append(dfwzbcat[x].Filter(VBSQCDSEL, "VBS QCD selection"))

        histo[17][x] = dfwzjjcat[x] .Histo1D(("histo_{0}_{1}".format(17,x), "histo_{0}_{1}".format(17,x), 4,1.5, 5.5), "ngood_jets","weight")
        histo[18][x] = dfwzbjjcat[x].Histo1D(("histo_{0}_{1}".format(18,x), "histo_{0}_{1}".format(18,x), 4,1.5, 5.5), "ngood_jets","weight")
        histo[19][x] = dfwzjjcat[x] .Histo1D(("histo_{0}_{1}".format(19,x), "histo_{0}_{1}".format(19,x), 30,200,500), "vbs_mjj","weight")
        histo[20][x] = dfwzbjjcat[x].Histo1D(("histo_{0}_{1}".format(20,x), "histo_{0}_{1}".format(20,x), 30,200,500), "vbs_mjj","weight")
        histo[21][x] = dfwzjjcat[x] .Histo1D(("histo_{0}_{1}".format(21,x), "histo_{0}_{1}".format(21,x), 40,0,10), "vbs_detajj","weight")
        histo[22][x] = dfwzbjjcat[x].Histo1D(("histo_{0}_{1}".format(22,x), "histo_{0}_{1}".format(22,x), 40,0,10), "vbs_detajj","weight")
        histo[23][x] = dfwzjjcat[x] .Histo1D(("histo_{0}_{1}".format(23,x), "histo_{0}_{1}".format(23,x), 40,0,3.1416), "vbs_dphijj","weight")
        histo[24][x] = dfwzbjjcat[x].Histo1D(("histo_{0}_{1}".format(24,x), "histo_{0}_{1}".format(24,x), 40,0,3.1416), "vbs_dphijj","weight")

        dfwzvbscat .append(dfwzcat[x] .Filter(VBSSEL, "VBS selection"))
        dfwzbvbscat.append(dfwzbcat[x].Filter(VBSSEL, "VBS selection"))
        histo[25][x] = dfwzvbscat[x] .Histo1D(("histo_{0}_{1}".format(25,x), "histo_{0}_{1}".format(25,x), 10,-1,1), "bdt_vbfinc","weight")
        histo[26][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(26,x), "histo_{0}_{1}".format(26,x), 10,-1,1), "bdt_vbfinc","weight")
        histo[27][x] = dfwzvbscat[x] .Histo1D(("histo_{0}_{1}".format(27,x), "histo_{0}_{1}".format(27,x), 4,1.5, 5.5), "ngood_jets","weight") 
        histo[28][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(28,x), "histo_{0}_{1}".format(28,x), 4,1.5, 5.5), "ngood_jets","weight")

        histo[100][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(100,x), "histo_{0}_{1}".format(100,x), 4,-0.5, 3.5), "TriLepton_flavor","weight")
        histo[102][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(102,x), "histo_{0}_{1}".format(102,x), 20,500,2500), "vbs_mjj","weight")
        histo[104][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(104,x), "histo_{0}_{1}".format(104,x), 20,0,800), "vbs_ptjj","weight")
        histo[106][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(106,x), "histo_{0}_{1}".format(106,x), 14,2.5,9.5), "vbs_detajj","weight")
        histo[108][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(108,x), "histo_{0}_{1}".format(108,x), 20,0,3.1416), "vbs_dphijj","weight")
        histo[110][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(110,x), "histo_{0}_{1}".format(110,x), 20,0,800), "vbs_ptj1","weight")
        histo[112][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(112,x), "histo_{0}_{1}".format(112,x), 20,0,400), "vbs_ptj2","weight")
        histo[114][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(114,x), "histo_{0}_{1}".format(114,x), 20,0,5), "vbs_etaj1","weight")
        histo[116][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(116,x), "histo_{0}_{1}".format(116,x), 20,0,5), "vbs_etaj2","weight")
        histo[118][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(118,x), "histo_{0}_{1}".format(118,x), 20,0.0,1.0), "vbs_zepvv","weight")
        histo[120][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(120,x), "histo_{0}_{1}".format(120,x), 20,0,2500), "vbs_sumHT","weight")
        histo[122][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(122,x), "histo_{0}_{1}".format(122,x), 20,0,1000), "vbs_ptvv","weight")
        histo[124][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(124,x), "histo_{0}_{1}".format(124,x), 20,0,300), "vbs_pttot","weight")
        histo[126][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(126,x), "histo_{0}_{1}".format(126,x), 20,0,8), "vbs_detavvj1","weight")
        histo[128][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(128,x), "histo_{0}_{1}".format(128,x), 20,0,8), "vbs_detavvj2","weight")
        histo[130][x] = dfwzvbscat[x].Histo1D(("histo_{0}_{1}".format(130,x), "histo_{0}_{1}".format(130,x), 20,-1,3), "vbs_ptbalance","weight")

        histo[101][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(101,x), "histo_{0}_{1}".format(101,x), 4,-0.5, 3.5), "TriLepton_flavor","weight")
        histo[103][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(103,x), "histo_{0}_{1}".format(103,x), 20,500,2500), "vbs_mjj","weight")
        histo[105][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(105,x), "histo_{0}_{1}".format(105,x), 20,0,800), "vbs_ptjj","weight")
        histo[107][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(107,x), "histo_{0}_{1}".format(107,x), 14,2.5,9.5), "vbs_detajj","weight")
        histo[109][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(109,x), "histo_{0}_{1}".format(109,x), 20,0,3.1416), "vbs_dphijj","weight")
        histo[111][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(111,x), "histo_{0}_{1}".format(111,x), 20,0,800), "vbs_ptj1","weight")
        histo[113][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(113,x), "histo_{0}_{1}".format(113,x), 20,0,400), "vbs_ptj2","weight")
        histo[115][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(115,x), "histo_{0}_{1}".format(115,x), 20,0,5), "vbs_etaj1","weight")
        histo[117][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(117,x), "histo_{0}_{1}".format(117,x), 20,0,5), "vbs_etaj2","weight")
        histo[119][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(119,x), "histo_{0}_{1}".format(119,x), 20,0.0,1.0), "vbs_zepvv","weight")
        histo[121][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(121,x), "histo_{0}_{1}".format(121,x), 20,0,2500), "vbs_sumHT","weight")
        histo[123][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(123,x), "histo_{0}_{1}".format(123,x), 20,0,1000), "vbs_ptvv","weight")
        histo[125][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(125,x), "histo_{0}_{1}".format(125,x), 20,0,300), "vbs_pttot","weight")
        histo[127][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(127,x), "histo_{0}_{1}".format(127,x), 20,0,8), "vbs_detavvj1","weight")
        histo[129][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(129,x), "histo_{0}_{1}".format(129,x), 20,0,8), "vbs_detavvj2","weight")
        histo[131][x] = dfwzbvbscat[x].Histo1D(("histo_{0}_{1}".format(131,x), "histo_{0}_{1}".format(131,x), 20,-1,3), "vbs_ptbalance","weight")

        if(doNtuples == True and x == theCat):
            outputFile = "ntupleWZAna_sample{0}_year{1}_job{2}.root".format(count,year,whichJob)
            dfwzvbscat[x].Snapshot("events", outputFile, branchList)

        histo[37][x] = dfzgcat[x].Histo1D(("histo_{0}_{1}".format(37,x), "histo_{0}_{1}".format(37,x), 40, 10, 210), "m3l{0}".format(altMass),"weight")
        dfzgcat[x] = dfzgcat[x].Filter("abs(m3l{0}-91.1876)<15".format(altMass))
        histo[38][x] = dfzgcat[x].Histo1D(("histo_{0}_{1}".format(38,x), "histo_{0}_{1}".format(38,x), 4,-0.5, 3.5), "TriLepton_flavor","weight")
        histo[39][x] = dfzgcat[x].Filter("TriLepton_flavor==0||TriLepton_flavor==2").Histo1D(("histo_{0}_{1}".format(39,x), "histo_{0}_{1}".format(39,x),20, 20, 120), "ptlW{0}".format(altMass),"weight")
        histo[40][x] = dfzgcat[x].Filter("TriLepton_flavor==1||TriLepton_flavor==3").Histo1D(("histo_{0}_{1}".format(40,x), "histo_{0}_{1}".format(40,x),20, 20, 120), "ptlW{0}".format(altMass),"weight")

        histo[51][x] = dfwhcat[x].Histo1D(("histo_{0}_{1}".format(51,x), "histo_{0}_{1}".format(51,x), 4,-0.5 ,3.5), "nbtag_goodbtag_Jet_bjet","weight")
        dfwhcat[x] = dfwhcat[x].Filter("nbtag_goodbtag_Jet_bjet == 0")
        histo[52][x] = dfwhcat[x].Histo1D(("histo_{0}_{1}".format(52,x), "histo_{0}_{1}".format(52,x), 4,-0.5, 3.5), "ngood_jets","weight")
        dfwhcat[x] = dfwhcat[x].Filter("ngood_jets == 0")
        histo[53][x] = dfwhcat[x].Histo1D(("histo_{0}_{1}".format(53,x), "histo_{0}_{1}".format(53,x),4,-0.5, 3.5), "TriLepton_flavor","weight")
        histo[54][x] = dfwhcat[x].Histo1D(("histo_{0}_{1}".format(54,x), "histo_{0}_{1}".format(54,x),20, 10, 210), "mllmin{0}".format(altMass),"weight")
        histo[55][x] = dfwhcat[x].Histo1D(("histo_{0}_{1}".format(55,x), "histo_{0}_{1}".format(55,x),20,  0, 4), "drllmin","weight")
        histo[56][x] = dfwhcat[x].Histo1D(("histo_{0}_{1}".format(56,x), "histo_{0}_{1}".format(56,x),20, 10, 110), "ptl3{0}".format(altMass),"weight")

        histo[57][x] = dfwzcat[x].Filter("TriLepton_flavor==0").Histo1D(("histo_{0}_{1}".format(57,x), "histo_{0}_{1}".format(57,x), 4,-0.5, 3.5), "ngood_jets","weight")
        histo[58][x] = dfwzcat[x].Filter("TriLepton_flavor==1").Histo1D(("histo_{0}_{1}".format(58,x), "histo_{0}_{1}".format(58,x), 4,-0.5, 3.5), "ngood_jets","weight")
        histo[59][x] = dfwzcat[x].Filter("TriLepton_flavor==2").Histo1D(("histo_{0}_{1}".format(59,x), "histo_{0}_{1}".format(59,x), 4,-0.5, 3.5), "ngood_jets","weight")
        histo[60][x] = dfwzcat[x].Filter("TriLepton_flavor==3").Histo1D(("histo_{0}_{1}".format(60,x), "histo_{0}_{1}".format(60,x), 4,-0.5, 3.5), "ngood_jets","weight")

        histo[88][x] = dfwzvbscat[x]                          .Histo1D(("histo_{0}_{1}".format(88,x), "histo_{0}_{1}".format(88,x),200,-1,1), "bdt_vbfinc","weight")
        histo[89][x] = dfwzvbscat[x].Filter("vbs_zepvv>=0.25").Histo1D(("histo_{0}_{1}".format(89,x), "histo_{0}_{1}".format(89,x),200,-1,1), "bdt_vbfinc","weight")
        histo[90][x] = dfwzvbscat[x].Filter("vbs_zepvv<0.25") .Histo1D(("histo_{0}_{1}".format(90,x), "histo_{0}_{1}".format(90,x),200,-1,1), "bdt_vbfinc","weight")

        histo[91][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format(91,x), "histo_{0}_{1}".format(91,x), 4,-0.5, 3.5), "TriLepton_flavor","weight")
        histo[92][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format(92,x), "histo_{0}_{1}".format(92,x), 4,-0.5, 3.5), "TriLepton_flavor","weight0")
        histo[93][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format(93,x), "histo_{0}_{1}".format(93,x), 4,-0.5, 3.5), "TriLepton_flavor","weight1")
        histo[94][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format(94,x), "histo_{0}_{1}".format(94,x), 4,-0.5, 3.5), "TriLepton_flavor","weight2")
        histo[95][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format(95,x), "histo_{0}_{1}".format(95,x), 4,-0.5, 3.5), "TriLepton_flavor","weight3")
        histo[96][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format(96,x), "histo_{0}_{1}".format(96,x), 4,-0.5, 3.5), "TriLepton_flavor","weight4")
        histo[97][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format(97,x), "histo_{0}_{1}".format(97,x), 4,-0.5, 3.5), "TriLepton_flavor","weight5")
        histo[98][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format(98,x), "histo_{0}_{1}".format(98,x), 4,-0.5, 3.5), "TriLepton_flavor","weight6")
        histo[99][x] = dfwzcat[x].Histo1D(("histo_{0}_{1}".format(99,x), "histo_{0}_{1}".format(99,x), 4,-0.5, 3.5), "TriLepton_flavor","weight7")

        x1Bins = array('d', [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])
        x2Bins = array('d', [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])

        if(makeDataCards == 1):
            xBins = array('d', [-0.5,0.5,1.5,2.5,3.5])

            startF = 300
            for nv in range(0,135):
                histo[startF+nv][x] = makeFinalVariableVar(dfwzcat[x],"ngood_jets",theCat,startF,x,xBins,nv)
            histo[startF+135][x]    = makeFinalVariableVar(dfwzcatMuonMomUp      [x],"ngood_jets",theCat,startF,x,xBins,135)
            histo[startF+136][x]    = makeFinalVariableVar(dfwzcatElectronMomUp  [x],"ngood_jets",theCat,startF,x,xBins,136)
            histo[startF+137][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes00Up"        ,theCat,startF,x,xBins,137)
            histo[startF+138][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes01Up"        ,theCat,startF,x,xBins,138)
            histo[startF+139][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes02Up"        ,theCat,startF,x,xBins,139)
            histo[startF+140][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes03Up"        ,theCat,startF,x,xBins,140)
            histo[startF+141][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes04Up"        ,theCat,startF,x,xBins,141)
            histo[startF+142][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes05Up"        ,theCat,startF,x,xBins,142)
            histo[startF+143][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes06Up"        ,theCat,startF,x,xBins,143)
            histo[startF+144][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes07Up"        ,theCat,startF,x,xBins,144)
            histo[startF+145][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes08Up"        ,theCat,startF,x,xBins,145)
            histo[startF+146][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes09Up"        ,theCat,startF,x,xBins,146)
            histo[startF+147][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes10Up"        ,theCat,startF,x,xBins,147)
            histo[startF+148][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes11Up"        ,theCat,startF,x,xBins,148)
            histo[startF+149][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes12Up"        ,theCat,startF,x,xBins,149)
            histo[startF+150][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes13Up"        ,theCat,startF,x,xBins,150)
            histo[startF+151][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes14Up"        ,theCat,startF,x,xBins,151)
            histo[startF+152][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes15Up"        ,theCat,startF,x,xBins,152)
            histo[startF+153][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes16Up"        ,theCat,startF,x,xBins,153)
            histo[startF+154][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes17Up"        ,theCat,startF,x,xBins,154)
            histo[startF+155][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes18Up"        ,theCat,startF,x,xBins,155)
            histo[startF+156][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes19Up"        ,theCat,startF,x,xBins,156)
            histo[startF+157][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes20Up"        ,theCat,startF,x,xBins,157)
            histo[startF+158][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes21Up"        ,theCat,startF,x,xBins,158)
            histo[startF+159][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes22Up"        ,theCat,startF,x,xBins,159)
            histo[startF+160][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes23Up"        ,theCat,startF,x,xBins,160)
            histo[startF+161][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes24Up"        ,theCat,startF,x,xBins,161)
            histo[startF+162][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes25Up"        ,theCat,startF,x,xBins,162)
            histo[startF+163][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes26Up"        ,theCat,startF,x,xBins,163)
            histo[startF+164][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJes27Up"        ,theCat,startF,x,xBins,164)
            histo[startF+165][x]    = makeFinalVariableVar(dfwzcat[x],"ngood_jetsJerUp"          ,theCat,startF,x,xBins,165)
            histo[startF+166][x]    = makeFinalVariableVar(dfwzcatJERUp        [x],"ngood_jets"  ,theCat,startF,x,xBins,166)
            histo[startF+167][x]    = makeFinalVariableVar(dfwzcatJESUp        [x],"ngood_jets"  ,theCat,startF,x,xBins,167)
            histo[startF+168][x]    = makeFinalVariableVar(dfwzcatUnclusteredUp[x],"ngood_jets"  ,theCat,startF,x,xBins,168)
            if(x == plotCategory("kPlotNonPrompt")):
                startNonPrompt = 0
                histoNonPrompt[0+startNonPrompt] = dfwzcat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(xBins)-1,xBins), "ngood_jets","weightFakeAltm0")
                histoNonPrompt[1+startNonPrompt] = dfwzcat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(xBins)-1,xBins), "ngood_jets","weightFakeAltm1")
                histoNonPrompt[2+startNonPrompt] = dfwzcat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(xBins)-1,xBins), "ngood_jets","weightFakeAltm2")
                histoNonPrompt[3+startNonPrompt] = dfwzcat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(xBins)-1,xBins), "ngood_jets","weightFakeAlte0")
                histoNonPrompt[4+startNonPrompt] = dfwzcat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(xBins)-1,xBins), "ngood_jets","weightFakeAlte1")
                histoNonPrompt[5+startNonPrompt] = dfwzcat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(xBins)-1,xBins), "ngood_jets","weightFakeAlte2")

            startF = 500
            for nv in range(0,135):
                histo[startF+nv][x] = makeFinalVariableVar(dfwzbcat[x],"ngood_jets",theCat,startF,x,xBins,nv)
            histo[startF+135][x]    = makeFinalVariableVar(dfwzbcatMuonMomUp      [x],"ngood_jets",theCat,startF,x,xBins,135)
            histo[startF+136][x]    = makeFinalVariableVar(dfwzbcatElectronMomUp  [x],"ngood_jets",theCat,startF,x,xBins,136)
            histo[startF+137][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes00Up"        ,theCat,startF,x,xBins,137)
            histo[startF+138][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes01Up"        ,theCat,startF,x,xBins,138)
            histo[startF+139][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes02Up"        ,theCat,startF,x,xBins,139)
            histo[startF+140][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes03Up"        ,theCat,startF,x,xBins,140)
            histo[startF+141][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes04Up"        ,theCat,startF,x,xBins,141)
            histo[startF+142][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes05Up"        ,theCat,startF,x,xBins,142)
            histo[startF+143][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes06Up"        ,theCat,startF,x,xBins,143)
            histo[startF+144][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes07Up"        ,theCat,startF,x,xBins,144)
            histo[startF+145][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes08Up"        ,theCat,startF,x,xBins,145)
            histo[startF+146][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes09Up"        ,theCat,startF,x,xBins,146)
            histo[startF+147][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes10Up"        ,theCat,startF,x,xBins,147)
            histo[startF+148][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes11Up"        ,theCat,startF,x,xBins,148)
            histo[startF+149][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes12Up"        ,theCat,startF,x,xBins,149)
            histo[startF+150][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes13Up"        ,theCat,startF,x,xBins,150)
            histo[startF+151][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes14Up"        ,theCat,startF,x,xBins,151)
            histo[startF+152][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes15Up"        ,theCat,startF,x,xBins,152)
            histo[startF+153][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes16Up"        ,theCat,startF,x,xBins,153)
            histo[startF+154][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes17Up"        ,theCat,startF,x,xBins,154)
            histo[startF+155][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes18Up"        ,theCat,startF,x,xBins,155)
            histo[startF+156][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes19Up"        ,theCat,startF,x,xBins,156)
            histo[startF+157][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes20Up"        ,theCat,startF,x,xBins,157)
            histo[startF+158][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes21Up"        ,theCat,startF,x,xBins,158)
            histo[startF+159][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes22Up"        ,theCat,startF,x,xBins,159)
            histo[startF+160][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes23Up"        ,theCat,startF,x,xBins,160)
            histo[startF+161][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes24Up"        ,theCat,startF,x,xBins,161)
            histo[startF+162][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes25Up"        ,theCat,startF,x,xBins,162)
            histo[startF+163][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes26Up"        ,theCat,startF,x,xBins,163)
            histo[startF+164][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJes27Up"        ,theCat,startF,x,xBins,164)
            histo[startF+165][x]    = makeFinalVariableVar(dfwzbcat[x],"ngood_jetsJerUp"          ,theCat,startF,x,xBins,165)
            histo[startF+166][x]    = makeFinalVariableVar(dfwzbcatJERUp        [x],"ngood_jets"  ,theCat,startF,x,xBins,166)
            histo[startF+167][x]    = makeFinalVariableVar(dfwzbcatJESUp        [x],"ngood_jets"  ,theCat,startF,x,xBins,167)
            histo[startF+168][x]    = makeFinalVariableVar(dfwzbcatUnclusteredUp[x],"ngood_jets"  ,theCat,startF,x,xBins,168)
            if(x == plotCategory("kPlotNonPrompt")):
                startNonPrompt = 6
                histoNonPrompt[0+startNonPrompt] = dfwzbcat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(xBins)-1,xBins), "ngood_jets","weightFakeAltm0")
                histoNonPrompt[1+startNonPrompt] = dfwzbcat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(xBins)-1,xBins), "ngood_jets","weightFakeAltm1")
                histoNonPrompt[2+startNonPrompt] = dfwzbcat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(xBins)-1,xBins), "ngood_jets","weightFakeAltm2")
                histoNonPrompt[3+startNonPrompt] = dfwzbcat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(xBins)-1,xBins), "ngood_jets","weightFakeAlte0")
                histoNonPrompt[4+startNonPrompt] = dfwzbcat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(xBins)-1,xBins), "ngood_jets","weightFakeAlte1")
                histoNonPrompt[5+startNonPrompt] = dfwzbcat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(xBins)-1,xBins), "ngood_jets","weightFakeAlte2")


        elif(makeDataCards == 2):
            xBins = array('d', [-0.5,3.5])

            startF = 300
            for nv in range(0,135):
                histo[startF+nv][x] = makeFinalVariableVar(dfwzcat[x],"TriLepton_flavor",theCat,startF,x,xBins,nv)
            histo[startF+135][x]    = makeFinalVariableVar(dfwzcatMuonMomUp      [x],"TriLepton_flavor",theCat,startF,x,xBins,135)
            histo[startF+136][x]    = makeFinalVariableVar(dfwzcatElectronMomUp  [x],"TriLepton_flavor",theCat,startF,x,xBins,136)
            histo[startF+137][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,137)
            histo[startF+138][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,138)
            histo[startF+139][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,139)
            histo[startF+140][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,140)
            histo[startF+141][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,141)
            histo[startF+142][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,142)
            histo[startF+143][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,143)
            histo[startF+144][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,144)
            histo[startF+145][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,145)
            histo[startF+146][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,146)
            histo[startF+147][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,147)
            histo[startF+148][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,148)
            histo[startF+149][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,149)
            histo[startF+150][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,150)
            histo[startF+151][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,151)
            histo[startF+152][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,152)
            histo[startF+153][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,153)
            histo[startF+154][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,154)
            histo[startF+155][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,155)
            histo[startF+156][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,156)
            histo[startF+157][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,157)
            histo[startF+158][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,158)
            histo[startF+159][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,159)
            histo[startF+160][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,160)
            histo[startF+161][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,161)
            histo[startF+162][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,162)
            histo[startF+163][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,163)
            histo[startF+164][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,164)
            histo[startF+165][x]    = makeFinalVariableVar(dfwzcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,165)
            histo[startF+166][x]    = makeFinalVariableVar(dfwzcatJERUp          [x],"TriLepton_flavor",theCat,startF,x,xBins,166)
            histo[startF+167][x]    = makeFinalVariableVar(dfwzcatJESUp          [x],"TriLepton_flavor",theCat,startF,x,xBins,167)
            histo[startF+168][x]    = makeFinalVariableVar(dfwzcatUnclusteredUp  [x],"TriLepton_flavor",theCat,startF,x,xBins,168)
            if(x == plotCategory("kPlotNonPrompt")):
                startNonPrompt = 0
                histoNonPrompt[0+startNonPrompt] = dfwzcat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(xBins)-1,xBins), "TriLepton_flavor","weightFakeAltm0")
                histoNonPrompt[1+startNonPrompt] = dfwzcat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(xBins)-1,xBins), "TriLepton_flavor","weightFakeAltm1")
                histoNonPrompt[2+startNonPrompt] = dfwzcat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(xBins)-1,xBins), "TriLepton_flavor","weightFakeAltm2")
                histoNonPrompt[3+startNonPrompt] = dfwzcat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(xBins)-1,xBins), "TriLepton_flavor","weightFakeAlte0")
                histoNonPrompt[4+startNonPrompt] = dfwzcat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(xBins)-1,xBins), "TriLepton_flavor","weightFakeAlte1")
                histoNonPrompt[5+startNonPrompt] = dfwzcat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(xBins)-1,xBins), "TriLepton_flavor","weightFakeAlte2")

            startF = 500
            for nv in range(0,135):
                histo[startF+nv][x] = makeFinalVariableVar(dfwzbcat[x],"TriLepton_flavor",theCat,startF,x,xBins,nv)
            histo[startF+135][x]    = makeFinalVariableVar(dfwzbcatMuonMomUp      [x],"TriLepton_flavor",theCat,startF,x,xBins,135)
            histo[startF+136][x]    = makeFinalVariableVar(dfwzbcatElectronMomUp  [x],"TriLepton_flavor",theCat,startF,x,xBins,136)
            histo[startF+137][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,137)
            histo[startF+138][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,138)
            histo[startF+139][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,139)
            histo[startF+140][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,140)
            histo[startF+141][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,141)
            histo[startF+142][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,142)
            histo[startF+143][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,143)
            histo[startF+144][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,144)
            histo[startF+145][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,145)
            histo[startF+146][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,146)
            histo[startF+147][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,147)
            histo[startF+148][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,148)
            histo[startF+149][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,149)
            histo[startF+150][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,150)
            histo[startF+151][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,151)
            histo[startF+152][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,152)
            histo[startF+153][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,153)
            histo[startF+154][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,154)
            histo[startF+155][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,155)
            histo[startF+156][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,156)
            histo[startF+157][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,157)
            histo[startF+158][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,158)
            histo[startF+159][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,159)
            histo[startF+160][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,160)
            histo[startF+161][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,161)
            histo[startF+162][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,162)
            histo[startF+163][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,163)
            histo[startF+164][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,164)
            histo[startF+165][x]    = makeFinalVariableVar(dfwzbcat[x]               ,"TriLepton_flavor",theCat,startF,x,xBins,165)
            histo[startF+166][x]    = makeFinalVariableVar(dfwzbcatJERUp          [x],"TriLepton_flavor",theCat,startF,x,xBins,166)
            histo[startF+167][x]    = makeFinalVariableVar(dfwzbcatJESUp          [x],"TriLepton_flavor",theCat,startF,x,xBins,167)
            histo[startF+168][x]    = makeFinalVariableVar(dfwzbcatUnclusteredUp  [x],"TriLepton_flavor",theCat,startF,x,xBins,168)
            if(x == plotCategory("kPlotNonPrompt")):
                startNonPrompt = 6
                histoNonPrompt[0+startNonPrompt] = dfwzbcat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(xBins)-1,xBins), "TriLepton_flavor","weightFakeAltm0")
                histoNonPrompt[1+startNonPrompt] = dfwzbcat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(xBins)-1,xBins), "TriLepton_flavor","weightFakeAltm1")
                histoNonPrompt[2+startNonPrompt] = dfwzbcat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(xBins)-1,xBins), "TriLepton_flavor","weightFakeAltm2")
                histoNonPrompt[3+startNonPrompt] = dfwzbcat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(xBins)-1,xBins), "TriLepton_flavor","weightFakeAlte0")
                histoNonPrompt[4+startNonPrompt] = dfwzbcat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(xBins)-1,xBins), "TriLepton_flavor","weightFakeAlte1")
                histoNonPrompt[5+startNonPrompt] = dfwzbcat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(xBins)-1,xBins), "TriLepton_flavor","weightFakeAlte2")

        elif(makeDataCards == 3 or makeDataCards == 4 or makeDataCards == 5 or makeDataCards == 6):
            x1Bins = array('d', [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])
            x2Bins = array('d', [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])
            if(makeDataCards == 3): # 3D
                x1Bins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5])
                x2Bins = array('d', [-0.5,0.5,1.5,2.5,3.5])
                varSel1 = 10
                varSel2 = 11
            elif(makeDataCards == 4): # BDT 2D
                x1Bins = array('d', [0.000,0.125,0.250,0.375,0.500,0.625,0.750,0.875,1.000,1.125,1.250,1.375,1.500,1.625,1.750,1.875,2.000])
                x2Bins = array('d', [-0.5,0.5,1.5,2.5,3.5])
                varSel1 = 12
                varSel2 = 11
            elif(makeDataCards == 5): # BDT 1D
                x1Bins = array('d', [0.000,0.125,0.250,0.375,0.500,0.625,0.750,0.875,1.000])
                x2Bins = array('d', [0.000,0.125,0.250,0.375,0.500,0.625,0.750,0.875,1.000])
                varSel1 = 13
                varSel2 = 13
            elif(makeDataCards == 6): # mjj
                x1Bins = array('d', [500,700,900,1100,1300,1650,2000,2450,2900])
                x2Bins = array('d', [500,700,900,1100,1300,1650,2000,2450,2900])
                varSel1 = 20
                varSel2 = 20

            dfwzvbscat             [x] = dfwzvbscat             [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mll{0},ngood_jets,{1})".format(altMass,varSel1))
            dfwzvbscatMuonMomUp    [x] = dfwzvbscatMuonMomUp    [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mllMuonMomUp,ngood_jets,{1})".format(altMass,varSel1))
            dfwzvbscatElectronMomUp[x] = dfwzvbscatElectronMomUp[x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mllElectronMomUp,ngood_jets,{1})".format(altMass,varSel1))
            dfwzvbscatJes00Up      [x] = dfwzvbscatJes00Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes00Up,vbs_detajjJes00Up,vbs_dphijjJes00Up,vbs_zepvvJes00Up,bdt_vbfincJes00Up[0],mll{0},ngood_jetsJes00Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes01Up      [x] = dfwzvbscatJes01Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes01Up,vbs_detajjJes01Up,vbs_dphijjJes01Up,vbs_zepvvJes01Up,bdt_vbfincJes01Up[0],mll{0},ngood_jetsJes01Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes02Up      [x] = dfwzvbscatJes02Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes02Up,vbs_detajjJes02Up,vbs_dphijjJes02Up,vbs_zepvvJes02Up,bdt_vbfincJes02Up[0],mll{0},ngood_jetsJes02Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes03Up      [x] = dfwzvbscatJes03Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes03Up,vbs_detajjJes03Up,vbs_dphijjJes03Up,vbs_zepvvJes03Up,bdt_vbfincJes03Up[0],mll{0},ngood_jetsJes03Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes04Up      [x] = dfwzvbscatJes04Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes04Up,vbs_detajjJes04Up,vbs_dphijjJes04Up,vbs_zepvvJes04Up,bdt_vbfincJes04Up[0],mll{0},ngood_jetsJes04Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes05Up      [x] = dfwzvbscatJes05Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes05Up,vbs_detajjJes05Up,vbs_dphijjJes05Up,vbs_zepvvJes05Up,bdt_vbfincJes05Up[0],mll{0},ngood_jetsJes05Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes06Up      [x] = dfwzvbscatJes06Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes06Up,vbs_detajjJes06Up,vbs_dphijjJes06Up,vbs_zepvvJes06Up,bdt_vbfincJes06Up[0],mll{0},ngood_jetsJes06Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes07Up      [x] = dfwzvbscatJes07Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes07Up,vbs_detajjJes07Up,vbs_dphijjJes07Up,vbs_zepvvJes07Up,bdt_vbfincJes07Up[0],mll{0},ngood_jetsJes07Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes08Up      [x] = dfwzvbscatJes08Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes08Up,vbs_detajjJes08Up,vbs_dphijjJes08Up,vbs_zepvvJes08Up,bdt_vbfincJes08Up[0],mll{0},ngood_jetsJes08Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes09Up      [x] = dfwzvbscatJes09Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes09Up,vbs_detajjJes09Up,vbs_dphijjJes09Up,vbs_zepvvJes09Up,bdt_vbfincJes09Up[0],mll{0},ngood_jetsJes09Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes10Up      [x] = dfwzvbscatJes10Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes10Up,vbs_detajjJes10Up,vbs_dphijjJes10Up,vbs_zepvvJes10Up,bdt_vbfincJes10Up[0],mll{0},ngood_jetsJes10Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes11Up      [x] = dfwzvbscatJes11Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes11Up,vbs_detajjJes11Up,vbs_dphijjJes11Up,vbs_zepvvJes11Up,bdt_vbfincJes11Up[0],mll{0},ngood_jetsJes11Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes12Up      [x] = dfwzvbscatJes12Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes12Up,vbs_detajjJes12Up,vbs_dphijjJes12Up,vbs_zepvvJes12Up,bdt_vbfincJes12Up[0],mll{0},ngood_jetsJes12Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes13Up      [x] = dfwzvbscatJes13Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes13Up,vbs_detajjJes13Up,vbs_dphijjJes13Up,vbs_zepvvJes13Up,bdt_vbfincJes13Up[0],mll{0},ngood_jetsJes13Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes14Up      [x] = dfwzvbscatJes14Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes14Up,vbs_detajjJes14Up,vbs_dphijjJes14Up,vbs_zepvvJes14Up,bdt_vbfincJes14Up[0],mll{0},ngood_jetsJes14Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes15Up      [x] = dfwzvbscatJes15Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes15Up,vbs_detajjJes15Up,vbs_dphijjJes15Up,vbs_zepvvJes15Up,bdt_vbfincJes15Up[0],mll{0},ngood_jetsJes15Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes16Up      [x] = dfwzvbscatJes16Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes16Up,vbs_detajjJes16Up,vbs_dphijjJes16Up,vbs_zepvvJes16Up,bdt_vbfincJes16Up[0],mll{0},ngood_jetsJes16Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes17Up      [x] = dfwzvbscatJes17Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes17Up,vbs_detajjJes17Up,vbs_dphijjJes17Up,vbs_zepvvJes17Up,bdt_vbfincJes17Up[0],mll{0},ngood_jetsJes17Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes18Up      [x] = dfwzvbscatJes18Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes18Up,vbs_detajjJes18Up,vbs_dphijjJes18Up,vbs_zepvvJes18Up,bdt_vbfincJes18Up[0],mll{0},ngood_jetsJes18Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes19Up      [x] = dfwzvbscatJes19Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes19Up,vbs_detajjJes19Up,vbs_dphijjJes19Up,vbs_zepvvJes19Up,bdt_vbfincJes19Up[0],mll{0},ngood_jetsJes19Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes20Up      [x] = dfwzvbscatJes20Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes20Up,vbs_detajjJes20Up,vbs_dphijjJes20Up,vbs_zepvvJes20Up,bdt_vbfincJes20Up[0],mll{0},ngood_jetsJes20Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes21Up      [x] = dfwzvbscatJes21Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes21Up,vbs_detajjJes21Up,vbs_dphijjJes21Up,vbs_zepvvJes21Up,bdt_vbfincJes21Up[0],mll{0},ngood_jetsJes21Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes22Up      [x] = dfwzvbscatJes22Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes22Up,vbs_detajjJes22Up,vbs_dphijjJes22Up,vbs_zepvvJes22Up,bdt_vbfincJes22Up[0],mll{0},ngood_jetsJes22Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes23Up      [x] = dfwzvbscatJes23Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes23Up,vbs_detajjJes23Up,vbs_dphijjJes23Up,vbs_zepvvJes23Up,bdt_vbfincJes23Up[0],mll{0},ngood_jetsJes23Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes24Up      [x] = dfwzvbscatJes24Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes24Up,vbs_detajjJes24Up,vbs_dphijjJes24Up,vbs_zepvvJes24Up,bdt_vbfincJes24Up[0],mll{0},ngood_jetsJes24Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes25Up      [x] = dfwzvbscatJes25Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes25Up,vbs_detajjJes25Up,vbs_dphijjJes25Up,vbs_zepvvJes25Up,bdt_vbfincJes25Up[0],mll{0},ngood_jetsJes25Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes26Up      [x] = dfwzvbscatJes26Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes26Up,vbs_detajjJes26Up,vbs_dphijjJes26Up,vbs_zepvvJes26Up,bdt_vbfincJes26Up[0],mll{0},ngood_jetsJes26Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes27Up      [x] = dfwzvbscatJes27Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes27Up,vbs_detajjJes27Up,vbs_dphijjJes27Up,vbs_zepvvJes27Up,bdt_vbfincJes27Up[0],mll{0},ngood_jetsJes27Up,{1})".format(altMass,varSel1))
            dfwzvbscatJerUp        [x] = dfwzvbscatJerUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJerUp  ,vbs_detajjJerUp  ,vbs_dphijjJerUp  ,vbs_zepvvJerUp  ,bdt_vbfincJerUp  [0],mll{0},ngood_jetsJerUp  ,{1})".format(altMass,varSel1))
            dfwzvbscatJERUp        [x] = dfwzvbscatJERUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj       ,vbs_zepvv	,bdt_vbfinc	  [0],mll{0},ngood_jets       ,{1})".format(altMass,varSel1))
            dfwzvbscatJESUp        [x] = dfwzvbscatJESUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj       ,vbs_zepvv	,bdt_vbfinc	  [0],mll{0},ngood_jets       ,{1})".format(altMass,varSel1))
            dfwzvbscatUnclusteredUp[x] = dfwzvbscatUnclusteredUp[x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj       ,vbs_zepvv	,bdt_vbfinc	  [0],mll{0},ngood_jets       ,{1})".format(altMass,varSel1))

            dfwzbvbscat             [x] = dfwzbvbscat             [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mll{0},ngood_jets,{1})".format(altMass,varSel2))
            dfwzbvbscatMuonMomUp    [x] = dfwzbvbscatMuonMomUp    [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mllMuonMomUp,ngood_jets,{1})".format(altMass,varSel2))
            dfwzbvbscatElectronMomUp[x] = dfwzbvbscatElectronMomUp[x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mllElectronMomUp,ngood_jets,{1})".format(altMass,varSel2))
            dfwzbvbscatJes00Up      [x] = dfwzbvbscatJes00Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes00Up,vbs_detajjJes00Up,vbs_dphijjJes00Up,vbs_zepvvJes00Up,bdt_vbfincJes00Up[0],mll{0},ngood_jetsJes00Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes01Up      [x] = dfwzbvbscatJes01Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes01Up,vbs_detajjJes01Up,vbs_dphijjJes01Up,vbs_zepvvJes01Up,bdt_vbfincJes01Up[0],mll{0},ngood_jetsJes01Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes02Up      [x] = dfwzbvbscatJes02Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes02Up,vbs_detajjJes02Up,vbs_dphijjJes02Up,vbs_zepvvJes02Up,bdt_vbfincJes02Up[0],mll{0},ngood_jetsJes02Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes03Up      [x] = dfwzbvbscatJes03Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes03Up,vbs_detajjJes03Up,vbs_dphijjJes03Up,vbs_zepvvJes03Up,bdt_vbfincJes03Up[0],mll{0},ngood_jetsJes03Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes04Up      [x] = dfwzbvbscatJes04Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes04Up,vbs_detajjJes04Up,vbs_dphijjJes04Up,vbs_zepvvJes04Up,bdt_vbfincJes04Up[0],mll{0},ngood_jetsJes04Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes05Up      [x] = dfwzbvbscatJes05Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes05Up,vbs_detajjJes05Up,vbs_dphijjJes05Up,vbs_zepvvJes05Up,bdt_vbfincJes05Up[0],mll{0},ngood_jetsJes05Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes06Up      [x] = dfwzbvbscatJes06Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes06Up,vbs_detajjJes06Up,vbs_dphijjJes06Up,vbs_zepvvJes06Up,bdt_vbfincJes06Up[0],mll{0},ngood_jetsJes06Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes07Up      [x] = dfwzbvbscatJes07Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes07Up,vbs_detajjJes07Up,vbs_dphijjJes07Up,vbs_zepvvJes07Up,bdt_vbfincJes07Up[0],mll{0},ngood_jetsJes07Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes08Up      [x] = dfwzbvbscatJes08Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes08Up,vbs_detajjJes08Up,vbs_dphijjJes08Up,vbs_zepvvJes08Up,bdt_vbfincJes08Up[0],mll{0},ngood_jetsJes08Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes09Up      [x] = dfwzbvbscatJes09Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes09Up,vbs_detajjJes09Up,vbs_dphijjJes09Up,vbs_zepvvJes09Up,bdt_vbfincJes09Up[0],mll{0},ngood_jetsJes09Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes10Up      [x] = dfwzbvbscatJes10Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes10Up,vbs_detajjJes10Up,vbs_dphijjJes10Up,vbs_zepvvJes10Up,bdt_vbfincJes10Up[0],mll{0},ngood_jetsJes10Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes11Up      [x] = dfwzbvbscatJes11Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes11Up,vbs_detajjJes11Up,vbs_dphijjJes11Up,vbs_zepvvJes11Up,bdt_vbfincJes11Up[0],mll{0},ngood_jetsJes11Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes12Up      [x] = dfwzbvbscatJes12Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes12Up,vbs_detajjJes12Up,vbs_dphijjJes12Up,vbs_zepvvJes12Up,bdt_vbfincJes12Up[0],mll{0},ngood_jetsJes12Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes13Up      [x] = dfwzbvbscatJes13Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes13Up,vbs_detajjJes13Up,vbs_dphijjJes13Up,vbs_zepvvJes13Up,bdt_vbfincJes13Up[0],mll{0},ngood_jetsJes13Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes14Up      [x] = dfwzbvbscatJes14Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes14Up,vbs_detajjJes14Up,vbs_dphijjJes14Up,vbs_zepvvJes14Up,bdt_vbfincJes14Up[0],mll{0},ngood_jetsJes14Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes15Up      [x] = dfwzbvbscatJes15Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes15Up,vbs_detajjJes15Up,vbs_dphijjJes15Up,vbs_zepvvJes15Up,bdt_vbfincJes15Up[0],mll{0},ngood_jetsJes15Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes16Up      [x] = dfwzbvbscatJes16Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes16Up,vbs_detajjJes16Up,vbs_dphijjJes16Up,vbs_zepvvJes16Up,bdt_vbfincJes16Up[0],mll{0},ngood_jetsJes16Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes17Up      [x] = dfwzbvbscatJes17Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes17Up,vbs_detajjJes17Up,vbs_dphijjJes17Up,vbs_zepvvJes17Up,bdt_vbfincJes17Up[0],mll{0},ngood_jetsJes17Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes18Up      [x] = dfwzbvbscatJes18Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes18Up,vbs_detajjJes18Up,vbs_dphijjJes18Up,vbs_zepvvJes18Up,bdt_vbfincJes18Up[0],mll{0},ngood_jetsJes18Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes19Up      [x] = dfwzbvbscatJes19Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes19Up,vbs_detajjJes19Up,vbs_dphijjJes19Up,vbs_zepvvJes19Up,bdt_vbfincJes19Up[0],mll{0},ngood_jetsJes19Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes20Up      [x] = dfwzbvbscatJes20Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes20Up,vbs_detajjJes20Up,vbs_dphijjJes20Up,vbs_zepvvJes20Up,bdt_vbfincJes20Up[0],mll{0},ngood_jetsJes20Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes21Up      [x] = dfwzbvbscatJes21Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes21Up,vbs_detajjJes21Up,vbs_dphijjJes21Up,vbs_zepvvJes21Up,bdt_vbfincJes21Up[0],mll{0},ngood_jetsJes21Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes22Up      [x] = dfwzbvbscatJes22Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes22Up,vbs_detajjJes22Up,vbs_dphijjJes22Up,vbs_zepvvJes22Up,bdt_vbfincJes22Up[0],mll{0},ngood_jetsJes22Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes23Up      [x] = dfwzbvbscatJes23Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes23Up,vbs_detajjJes23Up,vbs_dphijjJes23Up,vbs_zepvvJes23Up,bdt_vbfincJes23Up[0],mll{0},ngood_jetsJes23Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes24Up      [x] = dfwzbvbscatJes24Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes24Up,vbs_detajjJes24Up,vbs_dphijjJes24Up,vbs_zepvvJes24Up,bdt_vbfincJes24Up[0],mll{0},ngood_jetsJes24Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes25Up      [x] = dfwzbvbscatJes25Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes25Up,vbs_detajjJes25Up,vbs_dphijjJes25Up,vbs_zepvvJes25Up,bdt_vbfincJes25Up[0],mll{0},ngood_jetsJes25Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes26Up      [x] = dfwzbvbscatJes26Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes26Up,vbs_detajjJes26Up,vbs_dphijjJes26Up,vbs_zepvvJes26Up,bdt_vbfincJes26Up[0],mll{0},ngood_jetsJes26Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes27Up      [x] = dfwzbvbscatJes27Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes27Up,vbs_detajjJes27Up,vbs_dphijjJes27Up,vbs_zepvvJes27Up,bdt_vbfincJes27Up[0],mll{0},ngood_jetsJes27Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJerUp        [x] = dfwzbvbscatJerUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJerUp  ,vbs_detajjJerUp  ,vbs_dphijjJerUp  ,vbs_zepvvJerUp  ,bdt_vbfincJerUp  [0],mll{0},ngood_jetsJerUp  ,{1})".format(altMass,varSel2))
            dfwzbvbscatJERUp        [x] = dfwzbvbscatJERUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj	 ,vbs_zepvv	  ,bdt_vbfinc	    [0],mll{0},ngood_jets	,{1})".format(altMass,varSel2))
            dfwzbvbscatJESUp        [x] = dfwzbvbscatJESUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj	 ,vbs_zepvv	  ,bdt_vbfinc	    [0],mll{0},ngood_jets	,{1})".format(altMass,varSel2))
            dfwzbvbscatUnclusteredUp[x] = dfwzbvbscatUnclusteredUp[x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj	 ,vbs_zepvv	  ,bdt_vbfinc	    [0],mll{0},ngood_jets	,{1})".format(altMass,varSel2))


            startF = 300
            for nv in range(0,136):
                histo[startF+nv][x] = makeFinalVariableVar(dfwzvbscat[x],"finalVar",theCat,startF,x,x1Bins,nv)
            histo[startF+136][x]    = makeFinalVariableVar(dfwzvbscatMuonMomUp    [x],"finalVar",theCat,startF,x,x1Bins,136)
            histo[startF+137][x]    = makeFinalVariableVar(dfwzvbscatElectronMomUp[x],"finalVar",theCat,startF,x,x1Bins,137)
            histo[startF+138][x]    = makeFinalVariableVar(dfwzvbscatJes00Up      [x],"finalVar",theCat,startF,x,x1Bins,138)
            histo[startF+139][x]    = makeFinalVariableVar(dfwzvbscatJes01Up      [x],"finalVar",theCat,startF,x,x1Bins,139)
            histo[startF+140][x]    = makeFinalVariableVar(dfwzvbscatJes02Up      [x],"finalVar",theCat,startF,x,x1Bins,140)
            histo[startF+141][x]    = makeFinalVariableVar(dfwzvbscatJes03Up      [x],"finalVar",theCat,startF,x,x1Bins,141)
            histo[startF+142][x]    = makeFinalVariableVar(dfwzvbscatJes04Up      [x],"finalVar",theCat,startF,x,x1Bins,142)
            histo[startF+143][x]    = makeFinalVariableVar(dfwzvbscatJes05Up      [x],"finalVar",theCat,startF,x,x1Bins,143)
            histo[startF+144][x]    = makeFinalVariableVar(dfwzvbscatJes06Up      [x],"finalVar",theCat,startF,x,x1Bins,144)
            histo[startF+145][x]    = makeFinalVariableVar(dfwzvbscatJes07Up      [x],"finalVar",theCat,startF,x,x1Bins,145)
            histo[startF+146][x]    = makeFinalVariableVar(dfwzvbscatJes08Up      [x],"finalVar",theCat,startF,x,x1Bins,146)
            histo[startF+147][x]    = makeFinalVariableVar(dfwzvbscatJes09Up      [x],"finalVar",theCat,startF,x,x1Bins,147)
            histo[startF+148][x]    = makeFinalVariableVar(dfwzvbscatJes10Up      [x],"finalVar",theCat,startF,x,x1Bins,148)
            histo[startF+149][x]    = makeFinalVariableVar(dfwzvbscatJes11Up      [x],"finalVar",theCat,startF,x,x1Bins,149)
            histo[startF+150][x]    = makeFinalVariableVar(dfwzvbscatJes12Up      [x],"finalVar",theCat,startF,x,x1Bins,150)
            histo[startF+151][x]    = makeFinalVariableVar(dfwzvbscatJes13Up      [x],"finalVar",theCat,startF,x,x1Bins,151)
            histo[startF+152][x]    = makeFinalVariableVar(dfwzvbscatJes14Up      [x],"finalVar",theCat,startF,x,x1Bins,152)
            histo[startF+153][x]    = makeFinalVariableVar(dfwzvbscatJes15Up      [x],"finalVar",theCat,startF,x,x1Bins,153)
            histo[startF+154][x]    = makeFinalVariableVar(dfwzvbscatJes16Up      [x],"finalVar",theCat,startF,x,x1Bins,154)
            histo[startF+155][x]    = makeFinalVariableVar(dfwzvbscatJes17Up      [x],"finalVar",theCat,startF,x,x1Bins,155)
            histo[startF+156][x]    = makeFinalVariableVar(dfwzvbscatJes18Up      [x],"finalVar",theCat,startF,x,x1Bins,156)
            histo[startF+157][x]    = makeFinalVariableVar(dfwzvbscatJes19Up      [x],"finalVar",theCat,startF,x,x1Bins,157)
            histo[startF+158][x]    = makeFinalVariableVar(dfwzvbscatJes20Up      [x],"finalVar",theCat,startF,x,x1Bins,158)
            histo[startF+159][x]    = makeFinalVariableVar(dfwzvbscatJes21Up      [x],"finalVar",theCat,startF,x,x1Bins,159)
            histo[startF+160][x]    = makeFinalVariableVar(dfwzvbscatJes22Up      [x],"finalVar",theCat,startF,x,x1Bins,160)
            histo[startF+161][x]    = makeFinalVariableVar(dfwzvbscatJes23Up      [x],"finalVar",theCat,startF,x,x1Bins,161)
            histo[startF+162][x]    = makeFinalVariableVar(dfwzvbscatJes24Up      [x],"finalVar",theCat,startF,x,x1Bins,162)
            histo[startF+163][x]    = makeFinalVariableVar(dfwzvbscatJes25Up      [x],"finalVar",theCat,startF,x,x1Bins,163)
            histo[startF+164][x]    = makeFinalVariableVar(dfwzvbscatJes26Up      [x],"finalVar",theCat,startF,x,x1Bins,164)
            histo[startF+165][x]    = makeFinalVariableVar(dfwzvbscatJes27Up      [x],"finalVar",theCat,startF,x,x1Bins,165)
            histo[startF+166][x]    = makeFinalVariableVar(dfwzvbscatJerUp        [x],"finalVar",theCat,startF,x,x1Bins,166)
            histo[startF+167][x]    = makeFinalVariableVar(dfwzvbscatJERUp        [x],"finalVar",theCat,startF,x,x1Bins,167)
            histo[startF+168][x]    = makeFinalVariableVar(dfwzvbscatJESUp        [x],"finalVar",theCat,startF,x,x1Bins,168)
            histo[startF+169][x]    = makeFinalVariableVar(dfwzvbscatUnclusteredUp[x],"finalVar",theCat,startF,x,x1Bins,169)
            if(x == plotCategory("kPlotNonPrompt")):
                startNonPrompt = 0
                histoNonPrompt[0+startNonPrompt] = dfwzvbscat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm0")
                histoNonPrompt[1+startNonPrompt] = dfwzvbscat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm1")
                histoNonPrompt[2+startNonPrompt] = dfwzvbscat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm2")
                histoNonPrompt[3+startNonPrompt] = dfwzvbscat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte0")
                histoNonPrompt[4+startNonPrompt] = dfwzvbscat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte1")
                histoNonPrompt[5+startNonPrompt] = dfwzvbscat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte2")

            startF = 500
            for nv in range(0,136):
                histo[startF+nv][x] = makeFinalVariableVar(dfwzbvbscat[x],"finalVar",theCat,startF,x,x2Bins,nv)
            histo[startF+136][x]    = makeFinalVariableVar(dfwzbvbscatMuonMomUp	[x],"finalVar",theCat,startF,x,x2Bins,136)
            histo[startF+137][x]    = makeFinalVariableVar(dfwzbvbscatElectronMomUp[x],"finalVar",theCat,startF,x,x2Bins,137)
            histo[startF+138][x]    = makeFinalVariableVar(dfwzbvbscatJes00Up	[x],"finalVar",theCat,startF,x,x2Bins,138)
            histo[startF+139][x]    = makeFinalVariableVar(dfwzbvbscatJes01Up	[x],"finalVar",theCat,startF,x,x2Bins,139)
            histo[startF+140][x]    = makeFinalVariableVar(dfwzbvbscatJes02Up	[x],"finalVar",theCat,startF,x,x2Bins,140)
            histo[startF+141][x]    = makeFinalVariableVar(dfwzbvbscatJes03Up	[x],"finalVar",theCat,startF,x,x2Bins,141)
            histo[startF+142][x]    = makeFinalVariableVar(dfwzbvbscatJes04Up	[x],"finalVar",theCat,startF,x,x2Bins,142)
            histo[startF+143][x]    = makeFinalVariableVar(dfwzbvbscatJes05Up	[x],"finalVar",theCat,startF,x,x2Bins,143)
            histo[startF+144][x]    = makeFinalVariableVar(dfwzbvbscatJes06Up	[x],"finalVar",theCat,startF,x,x2Bins,144)
            histo[startF+145][x]    = makeFinalVariableVar(dfwzbvbscatJes07Up	[x],"finalVar",theCat,startF,x,x2Bins,145)
            histo[startF+146][x]    = makeFinalVariableVar(dfwzbvbscatJes08Up	[x],"finalVar",theCat,startF,x,x2Bins,146)
            histo[startF+147][x]    = makeFinalVariableVar(dfwzbvbscatJes09Up	[x],"finalVar",theCat,startF,x,x2Bins,147)
            histo[startF+148][x]    = makeFinalVariableVar(dfwzbvbscatJes10Up	[x],"finalVar",theCat,startF,x,x2Bins,148)
            histo[startF+149][x]    = makeFinalVariableVar(dfwzbvbscatJes11Up	[x],"finalVar",theCat,startF,x,x2Bins,149)
            histo[startF+150][x]    = makeFinalVariableVar(dfwzbvbscatJes12Up	[x],"finalVar",theCat,startF,x,x2Bins,150)
            histo[startF+151][x]    = makeFinalVariableVar(dfwzbvbscatJes13Up	[x],"finalVar",theCat,startF,x,x2Bins,151)
            histo[startF+152][x]    = makeFinalVariableVar(dfwzbvbscatJes14Up	[x],"finalVar",theCat,startF,x,x2Bins,152)
            histo[startF+153][x]    = makeFinalVariableVar(dfwzbvbscatJes15Up	[x],"finalVar",theCat,startF,x,x2Bins,153)
            histo[startF+154][x]    = makeFinalVariableVar(dfwzbvbscatJes16Up	[x],"finalVar",theCat,startF,x,x2Bins,154)
            histo[startF+155][x]    = makeFinalVariableVar(dfwzbvbscatJes17Up	[x],"finalVar",theCat,startF,x,x2Bins,155)
            histo[startF+156][x]    = makeFinalVariableVar(dfwzbvbscatJes18Up	[x],"finalVar",theCat,startF,x,x2Bins,156)
            histo[startF+157][x]    = makeFinalVariableVar(dfwzbvbscatJes19Up	[x],"finalVar",theCat,startF,x,x2Bins,157)
            histo[startF+158][x]    = makeFinalVariableVar(dfwzbvbscatJes20Up	[x],"finalVar",theCat,startF,x,x2Bins,158)
            histo[startF+159][x]    = makeFinalVariableVar(dfwzbvbscatJes21Up	[x],"finalVar",theCat,startF,x,x2Bins,159)
            histo[startF+160][x]    = makeFinalVariableVar(dfwzbvbscatJes22Up	[x],"finalVar",theCat,startF,x,x2Bins,160)
            histo[startF+161][x]    = makeFinalVariableVar(dfwzbvbscatJes23Up	[x],"finalVar",theCat,startF,x,x2Bins,161)
            histo[startF+162][x]    = makeFinalVariableVar(dfwzbvbscatJes24Up	[x],"finalVar",theCat,startF,x,x2Bins,162)
            histo[startF+163][x]    = makeFinalVariableVar(dfwzbvbscatJes25Up	[x],"finalVar",theCat,startF,x,x2Bins,163)
            histo[startF+164][x]    = makeFinalVariableVar(dfwzbvbscatJes26Up	[x],"finalVar",theCat,startF,x,x2Bins,164)
            histo[startF+165][x]    = makeFinalVariableVar(dfwzbvbscatJes27Up	[x],"finalVar",theCat,startF,x,x2Bins,165)
            histo[startF+166][x]    = makeFinalVariableVar(dfwzbvbscatJerUp	[x],"finalVar",theCat,startF,x,x2Bins,166)
            histo[startF+167][x]    = makeFinalVariableVar(dfwzbvbscatJERUp	[x],"finalVar",theCat,startF,x,x2Bins,167)
            histo[startF+168][x]    = makeFinalVariableVar(dfwzbvbscatJESUp	[x],"finalVar",theCat,startF,x,x2Bins,168)
            histo[startF+169][x]    = makeFinalVariableVar(dfwzbvbscatUnclusteredUp[x],"finalVar",theCat,startF,x,x2Bins,169)
            if(x == plotCategory("kPlotNonPrompt")):
                startNonPrompt = 6
                histoNonPrompt[0+startNonPrompt] = dfwzbvbscat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm0")
                histoNonPrompt[1+startNonPrompt] = dfwzbvbscat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm1")
                histoNonPrompt[2+startNonPrompt] = dfwzbvbscat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm2")
                histoNonPrompt[3+startNonPrompt] = dfwzbvbscat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte0")
                histoNonPrompt[4+startNonPrompt] = dfwzbvbscat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte1")
                histoNonPrompt[5+startNonPrompt] = dfwzbvbscat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte2")

        elif(makeDataCards == 7):
            yBins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5])

            x1Bins = array('d', [0.000,0.125,0.250,0.375,0.500,0.625,0.750,0.875,1.000,1.125,1.250,1.375,1.500,1.625,1.750,1.875,2.000,2.125,2.250,2.375,2.500,2.625,2.750,2.875,3.000,3.125,3.250,3.375,3.500,3.625,3.750,3.875,4.000])
            x2Bins = array('d', [-0.5,0.5,1.5,2.5,3.5])
            varSel1 = 14
            varSel2 = 11

            dfwzvbscat             [x] = dfwzvbscat             [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mll{0},ngood_jets,{1})".format(altMass,varSel1))
            dfwzvbscatMuonMomUp    [x] = dfwzvbscatMuonMomUp    [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mllMuonMomUp,ngood_jets,{1})".format(altMass,varSel1))
            dfwzvbscatElectronMomUp[x] = dfwzvbscatElectronMomUp[x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mllElectronMomUp,ngood_jets,{1})".format(altMass,varSel1))
            dfwzvbscatJes00Up      [x] = dfwzvbscatJes00Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes00Up,vbs_detajjJes00Up,vbs_dphijjJes00Up,vbs_zepvvJes00Up,bdt_vbfincJes00Up[0],mll{0},ngood_jetsJes00Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes01Up      [x] = dfwzvbscatJes01Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes01Up,vbs_detajjJes01Up,vbs_dphijjJes01Up,vbs_zepvvJes01Up,bdt_vbfincJes01Up[0],mll{0},ngood_jetsJes01Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes02Up      [x] = dfwzvbscatJes02Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes02Up,vbs_detajjJes02Up,vbs_dphijjJes02Up,vbs_zepvvJes02Up,bdt_vbfincJes02Up[0],mll{0},ngood_jetsJes02Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes03Up      [x] = dfwzvbscatJes03Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes03Up,vbs_detajjJes03Up,vbs_dphijjJes03Up,vbs_zepvvJes03Up,bdt_vbfincJes03Up[0],mll{0},ngood_jetsJes03Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes04Up      [x] = dfwzvbscatJes04Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes04Up,vbs_detajjJes04Up,vbs_dphijjJes04Up,vbs_zepvvJes04Up,bdt_vbfincJes04Up[0],mll{0},ngood_jetsJes04Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes05Up      [x] = dfwzvbscatJes05Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes05Up,vbs_detajjJes05Up,vbs_dphijjJes05Up,vbs_zepvvJes05Up,bdt_vbfincJes05Up[0],mll{0},ngood_jetsJes05Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes06Up      [x] = dfwzvbscatJes06Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes06Up,vbs_detajjJes06Up,vbs_dphijjJes06Up,vbs_zepvvJes06Up,bdt_vbfincJes06Up[0],mll{0},ngood_jetsJes06Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes07Up      [x] = dfwzvbscatJes07Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes07Up,vbs_detajjJes07Up,vbs_dphijjJes07Up,vbs_zepvvJes07Up,bdt_vbfincJes07Up[0],mll{0},ngood_jetsJes07Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes08Up      [x] = dfwzvbscatJes08Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes08Up,vbs_detajjJes08Up,vbs_dphijjJes08Up,vbs_zepvvJes08Up,bdt_vbfincJes08Up[0],mll{0},ngood_jetsJes08Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes09Up      [x] = dfwzvbscatJes09Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes09Up,vbs_detajjJes09Up,vbs_dphijjJes09Up,vbs_zepvvJes09Up,bdt_vbfincJes09Up[0],mll{0},ngood_jetsJes09Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes10Up      [x] = dfwzvbscatJes10Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes10Up,vbs_detajjJes10Up,vbs_dphijjJes10Up,vbs_zepvvJes10Up,bdt_vbfincJes10Up[0],mll{0},ngood_jetsJes10Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes11Up      [x] = dfwzvbscatJes11Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes11Up,vbs_detajjJes11Up,vbs_dphijjJes11Up,vbs_zepvvJes11Up,bdt_vbfincJes11Up[0],mll{0},ngood_jetsJes11Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes12Up      [x] = dfwzvbscatJes12Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes12Up,vbs_detajjJes12Up,vbs_dphijjJes12Up,vbs_zepvvJes12Up,bdt_vbfincJes12Up[0],mll{0},ngood_jetsJes12Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes13Up      [x] = dfwzvbscatJes13Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes13Up,vbs_detajjJes13Up,vbs_dphijjJes13Up,vbs_zepvvJes13Up,bdt_vbfincJes13Up[0],mll{0},ngood_jetsJes13Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes14Up      [x] = dfwzvbscatJes14Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes14Up,vbs_detajjJes14Up,vbs_dphijjJes14Up,vbs_zepvvJes14Up,bdt_vbfincJes14Up[0],mll{0},ngood_jetsJes14Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes15Up      [x] = dfwzvbscatJes15Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes15Up,vbs_detajjJes15Up,vbs_dphijjJes15Up,vbs_zepvvJes15Up,bdt_vbfincJes15Up[0],mll{0},ngood_jetsJes15Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes16Up      [x] = dfwzvbscatJes16Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes16Up,vbs_detajjJes16Up,vbs_dphijjJes16Up,vbs_zepvvJes16Up,bdt_vbfincJes16Up[0],mll{0},ngood_jetsJes16Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes17Up      [x] = dfwzvbscatJes17Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes17Up,vbs_detajjJes17Up,vbs_dphijjJes17Up,vbs_zepvvJes17Up,bdt_vbfincJes17Up[0],mll{0},ngood_jetsJes17Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes18Up      [x] = dfwzvbscatJes18Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes18Up,vbs_detajjJes18Up,vbs_dphijjJes18Up,vbs_zepvvJes18Up,bdt_vbfincJes18Up[0],mll{0},ngood_jetsJes18Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes19Up      [x] = dfwzvbscatJes19Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes19Up,vbs_detajjJes19Up,vbs_dphijjJes19Up,vbs_zepvvJes19Up,bdt_vbfincJes19Up[0],mll{0},ngood_jetsJes19Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes20Up      [x] = dfwzvbscatJes20Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes20Up,vbs_detajjJes20Up,vbs_dphijjJes20Up,vbs_zepvvJes20Up,bdt_vbfincJes20Up[0],mll{0},ngood_jetsJes20Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes21Up      [x] = dfwzvbscatJes21Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes21Up,vbs_detajjJes21Up,vbs_dphijjJes21Up,vbs_zepvvJes21Up,bdt_vbfincJes21Up[0],mll{0},ngood_jetsJes21Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes22Up      [x] = dfwzvbscatJes22Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes22Up,vbs_detajjJes22Up,vbs_dphijjJes22Up,vbs_zepvvJes22Up,bdt_vbfincJes22Up[0],mll{0},ngood_jetsJes22Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes23Up      [x] = dfwzvbscatJes23Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes23Up,vbs_detajjJes23Up,vbs_dphijjJes23Up,vbs_zepvvJes23Up,bdt_vbfincJes23Up[0],mll{0},ngood_jetsJes23Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes24Up      [x] = dfwzvbscatJes24Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes24Up,vbs_detajjJes24Up,vbs_dphijjJes24Up,vbs_zepvvJes24Up,bdt_vbfincJes24Up[0],mll{0},ngood_jetsJes24Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes25Up      [x] = dfwzvbscatJes25Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes25Up,vbs_detajjJes25Up,vbs_dphijjJes25Up,vbs_zepvvJes25Up,bdt_vbfincJes25Up[0],mll{0},ngood_jetsJes25Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes26Up      [x] = dfwzvbscatJes26Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes26Up,vbs_detajjJes26Up,vbs_dphijjJes26Up,vbs_zepvvJes26Up,bdt_vbfincJes26Up[0],mll{0},ngood_jetsJes26Up,{1})".format(altMass,varSel1))
            dfwzvbscatJes27Up      [x] = dfwzvbscatJes27Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes27Up,vbs_detajjJes27Up,vbs_dphijjJes27Up,vbs_zepvvJes27Up,bdt_vbfincJes27Up[0],mll{0},ngood_jetsJes27Up,{1})".format(altMass,varSel1))
            dfwzvbscatJerUp        [x] = dfwzvbscatJerUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJerUp  ,vbs_detajjJerUp  ,vbs_dphijjJerUp  ,vbs_zepvvJerUp  ,bdt_vbfincJerUp  [0],mll{0},ngood_jetsJerUp  ,{1})".format(altMass,varSel1))
            dfwzvbscatJERUp        [x] = dfwzvbscatJERUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj       ,vbs_zepvv	,bdt_vbfinc	  [0],mll{0},ngood_jets       ,{1})".format(altMass,varSel1))
            dfwzvbscatJESUp        [x] = dfwzvbscatJESUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj       ,vbs_zepvv	,bdt_vbfinc	  [0],mll{0},ngood_jets       ,{1})".format(altMass,varSel1))
            dfwzvbscatUnclusteredUp[x] = dfwzvbscatUnclusteredUp[x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj       ,vbs_zepvv	,bdt_vbfinc	  [0],mll{0},ngood_jets       ,{1})".format(altMass,varSel1))

            dfwzbvbscat             [x] = dfwzbvbscat             [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mll{0},ngood_jets,{1})".format(altMass,varSel2))
            dfwzbvbscatMuonMomUp    [x] = dfwzbvbscatMuonMomUp    [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mllMuonMomUp,ngood_jets,{1})".format(altMass,varSel2))
            dfwzbvbscatElectronMomUp[x] = dfwzbvbscatElectronMomUp[x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mllElectronMomUp,ngood_jets,{1})".format(altMass,varSel2))
            dfwzbvbscatJes00Up      [x] = dfwzbvbscatJes00Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes00Up,vbs_detajjJes00Up,vbs_dphijjJes00Up,vbs_zepvvJes00Up,bdt_vbfincJes00Up[0],mll{0},ngood_jetsJes00Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes01Up      [x] = dfwzbvbscatJes01Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes01Up,vbs_detajjJes01Up,vbs_dphijjJes01Up,vbs_zepvvJes01Up,bdt_vbfincJes01Up[0],mll{0},ngood_jetsJes01Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes02Up      [x] = dfwzbvbscatJes02Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes02Up,vbs_detajjJes02Up,vbs_dphijjJes02Up,vbs_zepvvJes02Up,bdt_vbfincJes02Up[0],mll{0},ngood_jetsJes02Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes03Up      [x] = dfwzbvbscatJes03Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes03Up,vbs_detajjJes03Up,vbs_dphijjJes03Up,vbs_zepvvJes03Up,bdt_vbfincJes03Up[0],mll{0},ngood_jetsJes03Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes04Up      [x] = dfwzbvbscatJes04Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes04Up,vbs_detajjJes04Up,vbs_dphijjJes04Up,vbs_zepvvJes04Up,bdt_vbfincJes04Up[0],mll{0},ngood_jetsJes04Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes05Up      [x] = dfwzbvbscatJes05Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes05Up,vbs_detajjJes05Up,vbs_dphijjJes05Up,vbs_zepvvJes05Up,bdt_vbfincJes05Up[0],mll{0},ngood_jetsJes05Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes06Up      [x] = dfwzbvbscatJes06Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes06Up,vbs_detajjJes06Up,vbs_dphijjJes06Up,vbs_zepvvJes06Up,bdt_vbfincJes06Up[0],mll{0},ngood_jetsJes06Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes07Up      [x] = dfwzbvbscatJes07Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes07Up,vbs_detajjJes07Up,vbs_dphijjJes07Up,vbs_zepvvJes07Up,bdt_vbfincJes07Up[0],mll{0},ngood_jetsJes07Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes08Up      [x] = dfwzbvbscatJes08Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes08Up,vbs_detajjJes08Up,vbs_dphijjJes08Up,vbs_zepvvJes08Up,bdt_vbfincJes08Up[0],mll{0},ngood_jetsJes08Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes09Up      [x] = dfwzbvbscatJes09Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes09Up,vbs_detajjJes09Up,vbs_dphijjJes09Up,vbs_zepvvJes09Up,bdt_vbfincJes09Up[0],mll{0},ngood_jetsJes09Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes10Up      [x] = dfwzbvbscatJes10Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes10Up,vbs_detajjJes10Up,vbs_dphijjJes10Up,vbs_zepvvJes10Up,bdt_vbfincJes10Up[0],mll{0},ngood_jetsJes10Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes11Up      [x] = dfwzbvbscatJes11Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes11Up,vbs_detajjJes11Up,vbs_dphijjJes11Up,vbs_zepvvJes11Up,bdt_vbfincJes11Up[0],mll{0},ngood_jetsJes11Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes12Up      [x] = dfwzbvbscatJes12Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes12Up,vbs_detajjJes12Up,vbs_dphijjJes12Up,vbs_zepvvJes12Up,bdt_vbfincJes12Up[0],mll{0},ngood_jetsJes12Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes13Up      [x] = dfwzbvbscatJes13Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes13Up,vbs_detajjJes13Up,vbs_dphijjJes13Up,vbs_zepvvJes13Up,bdt_vbfincJes13Up[0],mll{0},ngood_jetsJes13Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes14Up      [x] = dfwzbvbscatJes14Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes14Up,vbs_detajjJes14Up,vbs_dphijjJes14Up,vbs_zepvvJes14Up,bdt_vbfincJes14Up[0],mll{0},ngood_jetsJes14Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes15Up      [x] = dfwzbvbscatJes15Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes15Up,vbs_detajjJes15Up,vbs_dphijjJes15Up,vbs_zepvvJes15Up,bdt_vbfincJes15Up[0],mll{0},ngood_jetsJes15Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes16Up      [x] = dfwzbvbscatJes16Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes16Up,vbs_detajjJes16Up,vbs_dphijjJes16Up,vbs_zepvvJes16Up,bdt_vbfincJes16Up[0],mll{0},ngood_jetsJes16Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes17Up      [x] = dfwzbvbscatJes17Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes17Up,vbs_detajjJes17Up,vbs_dphijjJes17Up,vbs_zepvvJes17Up,bdt_vbfincJes17Up[0],mll{0},ngood_jetsJes17Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes18Up      [x] = dfwzbvbscatJes18Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes18Up,vbs_detajjJes18Up,vbs_dphijjJes18Up,vbs_zepvvJes18Up,bdt_vbfincJes18Up[0],mll{0},ngood_jetsJes18Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes19Up      [x] = dfwzbvbscatJes19Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes19Up,vbs_detajjJes19Up,vbs_dphijjJes19Up,vbs_zepvvJes19Up,bdt_vbfincJes19Up[0],mll{0},ngood_jetsJes19Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes20Up      [x] = dfwzbvbscatJes20Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes20Up,vbs_detajjJes20Up,vbs_dphijjJes20Up,vbs_zepvvJes20Up,bdt_vbfincJes20Up[0],mll{0},ngood_jetsJes20Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes21Up      [x] = dfwzbvbscatJes21Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes21Up,vbs_detajjJes21Up,vbs_dphijjJes21Up,vbs_zepvvJes21Up,bdt_vbfincJes21Up[0],mll{0},ngood_jetsJes21Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes22Up      [x] = dfwzbvbscatJes22Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes22Up,vbs_detajjJes22Up,vbs_dphijjJes22Up,vbs_zepvvJes22Up,bdt_vbfincJes22Up[0],mll{0},ngood_jetsJes22Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes23Up      [x] = dfwzbvbscatJes23Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes23Up,vbs_detajjJes23Up,vbs_dphijjJes23Up,vbs_zepvvJes23Up,bdt_vbfincJes23Up[0],mll{0},ngood_jetsJes23Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes24Up      [x] = dfwzbvbscatJes24Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes24Up,vbs_detajjJes24Up,vbs_dphijjJes24Up,vbs_zepvvJes24Up,bdt_vbfincJes24Up[0],mll{0},ngood_jetsJes24Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes25Up      [x] = dfwzbvbscatJes25Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes25Up,vbs_detajjJes25Up,vbs_dphijjJes25Up,vbs_zepvvJes25Up,bdt_vbfincJes25Up[0],mll{0},ngood_jetsJes25Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes26Up      [x] = dfwzbvbscatJes26Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes26Up,vbs_detajjJes26Up,vbs_dphijjJes26Up,vbs_zepvvJes26Up,bdt_vbfincJes26Up[0],mll{0},ngood_jetsJes26Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJes27Up      [x] = dfwzbvbscatJes27Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes27Up,vbs_detajjJes27Up,vbs_dphijjJes27Up,vbs_zepvvJes27Up,bdt_vbfincJes27Up[0],mll{0},ngood_jetsJes27Up,{1})".format(altMass,varSel2))
            dfwzbvbscatJerUp        [x] = dfwzbvbscatJerUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJerUp  ,vbs_detajjJerUp  ,vbs_dphijjJerUp  ,vbs_zepvvJerUp  ,bdt_vbfincJerUp  [0],mll{0},ngood_jetsJerUp  ,{1})".format(altMass,varSel2))
            dfwzbvbscatJERUp        [x] = dfwzbvbscatJERUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj	 ,vbs_zepvv	  ,bdt_vbfinc	    [0],mll{0},ngood_jets	,{1})".format(altMass,varSel2))
            dfwzbvbscatJESUp        [x] = dfwzbvbscatJESUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj	 ,vbs_zepvv	  ,bdt_vbfinc	    [0],mll{0},ngood_jets	,{1})".format(altMass,varSel2))
            dfwzbvbscatUnclusteredUp[x] = dfwzbvbscatUnclusteredUp[x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj	 ,vbs_zepvv	  ,bdt_vbfinc	    [0],mll{0},ngood_jets	,{1})".format(altMass,varSel2))


            startF = 300
            for nv in range(0,136):
                histo2D[startF+nv][x] = makeFinalVariable2DVar(dfwzvbscat             [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,nv)
            histo2D[startF+136][x]    = makeFinalVariable2DVar(dfwzvbscatMuonMomUp    [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,136)
            histo2D[startF+137][x]    = makeFinalVariable2DVar(dfwzvbscatElectronMomUp[x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,137)
            histo2D[startF+138][x]    = makeFinalVariable2DVar(dfwzvbscatJes00Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,138)
            histo2D[startF+139][x]    = makeFinalVariable2DVar(dfwzvbscatJes01Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,139)
            histo2D[startF+140][x]    = makeFinalVariable2DVar(dfwzvbscatJes02Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,140)
            histo2D[startF+141][x]    = makeFinalVariable2DVar(dfwzvbscatJes03Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,141)
            histo2D[startF+142][x]    = makeFinalVariable2DVar(dfwzvbscatJes04Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,142)
            histo2D[startF+143][x]    = makeFinalVariable2DVar(dfwzvbscatJes05Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,143)
            histo2D[startF+144][x]    = makeFinalVariable2DVar(dfwzvbscatJes06Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,144)
            histo2D[startF+145][x]    = makeFinalVariable2DVar(dfwzvbscatJes07Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,145)
            histo2D[startF+146][x]    = makeFinalVariable2DVar(dfwzvbscatJes08Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,146)
            histo2D[startF+147][x]    = makeFinalVariable2DVar(dfwzvbscatJes09Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,147)
            histo2D[startF+148][x]    = makeFinalVariable2DVar(dfwzvbscatJes10Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,148)
            histo2D[startF+149][x]    = makeFinalVariable2DVar(dfwzvbscatJes11Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,149)
            histo2D[startF+150][x]    = makeFinalVariable2DVar(dfwzvbscatJes12Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,150)
            histo2D[startF+151][x]    = makeFinalVariable2DVar(dfwzvbscatJes13Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,151)
            histo2D[startF+152][x]    = makeFinalVariable2DVar(dfwzvbscatJes14Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,152)
            histo2D[startF+153][x]    = makeFinalVariable2DVar(dfwzvbscatJes15Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,153)
            histo2D[startF+154][x]    = makeFinalVariable2DVar(dfwzvbscatJes16Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,154)
            histo2D[startF+155][x]    = makeFinalVariable2DVar(dfwzvbscatJes17Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,155)
            histo2D[startF+156][x]    = makeFinalVariable2DVar(dfwzvbscatJes18Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,156)
            histo2D[startF+157][x]    = makeFinalVariable2DVar(dfwzvbscatJes19Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,157)
            histo2D[startF+158][x]    = makeFinalVariable2DVar(dfwzvbscatJes20Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,158)
            histo2D[startF+159][x]    = makeFinalVariable2DVar(dfwzvbscatJes21Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,159)
            histo2D[startF+160][x]    = makeFinalVariable2DVar(dfwzvbscatJes22Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,160)
            histo2D[startF+161][x]    = makeFinalVariable2DVar(dfwzvbscatJes23Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,161)
            histo2D[startF+162][x]    = makeFinalVariable2DVar(dfwzvbscatJes24Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,162)
            histo2D[startF+163][x]    = makeFinalVariable2DVar(dfwzvbscatJes25Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,163)
            histo2D[startF+164][x]    = makeFinalVariable2DVar(dfwzvbscatJes26Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,164)
            histo2D[startF+165][x]    = makeFinalVariable2DVar(dfwzvbscatJes27Up	   [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,165)
            histo2D[startF+166][x]    = makeFinalVariable2DVar(dfwzvbscatJerUp	           [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,166)
            histo2D[startF+167][x]    = makeFinalVariable2DVar(dfwzvbscatJERUp	           [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,167)
            histo2D[startF+168][x]    = makeFinalVariable2DVar(dfwzvbscatJESUp	           [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,168)
            histo2D[startF+169][x]    = makeFinalVariable2DVar(dfwzvbscatUnclusteredUp     [x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,169)
            if(x == plotCategory("kPlotNonPrompt")):
                startNonPrompt = 0
                histoNonPrompt[0+startNonPrompt] = dfwzvbscat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm0")
                histoNonPrompt[1+startNonPrompt] = dfwzvbscat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm1")
                histoNonPrompt[2+startNonPrompt] = dfwzvbscat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm2")
                histoNonPrompt[3+startNonPrompt] = dfwzvbscat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte0")
                histoNonPrompt[4+startNonPrompt] = dfwzvbscat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte1")
                histoNonPrompt[5+startNonPrompt] = dfwzvbscat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte2")

            startF = 500
            for nv in range(0,136):
                histo2D[startF+nv][x] = makeFinalVariable2DVar(dfwzbvbscat             [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,nv)
            histo2D[startF+136][x]    = makeFinalVariable2DVar(dfwzbvbscatMuonMomUp    [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,136)
            histo2D[startF+137][x]    = makeFinalVariable2DVar(dfwzbvbscatElectronMomUp[x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,137)
            histo2D[startF+138][x]    = makeFinalVariable2DVar(dfwzbvbscatJes00Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,138)
            histo2D[startF+139][x]    = makeFinalVariable2DVar(dfwzbvbscatJes01Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,139)
            histo2D[startF+140][x]    = makeFinalVariable2DVar(dfwzbvbscatJes02Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,140)
            histo2D[startF+141][x]    = makeFinalVariable2DVar(dfwzbvbscatJes03Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,141)
            histo2D[startF+142][x]    = makeFinalVariable2DVar(dfwzbvbscatJes04Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,142)
            histo2D[startF+143][x]    = makeFinalVariable2DVar(dfwzbvbscatJes05Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,143)
            histo2D[startF+144][x]    = makeFinalVariable2DVar(dfwzbvbscatJes06Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,144)
            histo2D[startF+145][x]    = makeFinalVariable2DVar(dfwzbvbscatJes07Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,145)
            histo2D[startF+146][x]    = makeFinalVariable2DVar(dfwzbvbscatJes08Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,146)
            histo2D[startF+147][x]    = makeFinalVariable2DVar(dfwzbvbscatJes09Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,147)
            histo2D[startF+148][x]    = makeFinalVariable2DVar(dfwzbvbscatJes10Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,148)
            histo2D[startF+149][x]    = makeFinalVariable2DVar(dfwzbvbscatJes11Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,149)
            histo2D[startF+150][x]    = makeFinalVariable2DVar(dfwzbvbscatJes12Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,150)
            histo2D[startF+151][x]    = makeFinalVariable2DVar(dfwzbvbscatJes13Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,151)
            histo2D[startF+152][x]    = makeFinalVariable2DVar(dfwzbvbscatJes14Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,152)
            histo2D[startF+153][x]    = makeFinalVariable2DVar(dfwzbvbscatJes15Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,153)
            histo2D[startF+154][x]    = makeFinalVariable2DVar(dfwzbvbscatJes16Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,154)
            histo2D[startF+155][x]    = makeFinalVariable2DVar(dfwzbvbscatJes17Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,155)
            histo2D[startF+156][x]    = makeFinalVariable2DVar(dfwzbvbscatJes18Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,156)
            histo2D[startF+157][x]    = makeFinalVariable2DVar(dfwzbvbscatJes19Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,157)
            histo2D[startF+158][x]    = makeFinalVariable2DVar(dfwzbvbscatJes20Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,158)
            histo2D[startF+159][x]    = makeFinalVariable2DVar(dfwzbvbscatJes21Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,159)
            histo2D[startF+160][x]    = makeFinalVariable2DVar(dfwzbvbscatJes22Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,160)
            histo2D[startF+161][x]    = makeFinalVariable2DVar(dfwzbvbscatJes23Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,161)
            histo2D[startF+162][x]    = makeFinalVariable2DVar(dfwzbvbscatJes24Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,162)
            histo2D[startF+163][x]    = makeFinalVariable2DVar(dfwzbvbscatJes25Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,163)
            histo2D[startF+164][x]    = makeFinalVariable2DVar(dfwzbvbscatJes26Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,164)
            histo2D[startF+165][x]    = makeFinalVariable2DVar(dfwzbvbscatJes27Up      [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,165)
            histo2D[startF+166][x]    = makeFinalVariable2DVar(dfwzbvbscatJerUp	       [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,166)
            histo2D[startF+167][x]    = makeFinalVariable2DVar(dfwzbvbscatJERUp	       [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,167)
            histo2D[startF+168][x]    = makeFinalVariable2DVar(dfwzbvbscatJESUp	       [x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,168)
            histo2D[startF+169][x]    = makeFinalVariable2DVar(dfwzbvbscatUnclusteredUp[x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,169)
            if(x == plotCategory("kPlotNonPrompt")):
                startNonPrompt = 6
                histoNonPrompt[0+startNonPrompt] = dfwzbvbscat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm0")
                histoNonPrompt[1+startNonPrompt] = dfwzbvbscat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm1")
                histoNonPrompt[2+startNonPrompt] = dfwzbvbscat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm2")
                histoNonPrompt[3+startNonPrompt] = dfwzbvbscat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte0")
                histoNonPrompt[4+startNonPrompt] = dfwzbvbscat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte1")
                histoNonPrompt[5+startNonPrompt] = dfwzbvbscat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte2")

    report = []
    for x in range(nCat):
        report.append(dfwzvbscat[x].Report())
        if(x != theCat): continue
        print("---------------- SUMMARY {0} -------------".format(x))
        report[x].Print()

    if(makeDataCards == 7):
        for j in range(300,nHistoMVA):
            if(j < 500):
                for x in range(nCat):
                    histo[j][x] = ROOT.TH1D("histo_{0}_{1}".format(j,x), "histo_{0}_{1}".format(j,x), len(x1Bins)-1, x1Bins)
            else:
                for x in range(nCat):
                    histo[j][x] = ROOT.TH1D("histo_{0}_{1}".format(j,x), "histo_{0}_{1}".format(j,x), len(x2Bins)-1, x2Bins)

    for j in range(300,nHistoMVA):
        for x in range(nCat):
            if(histo2D[j][x] == 0):
                continue
            for i in range(histo2D[j][x].GetNbinsX()):
                histo2D[j][x].SetBinContent(i+1,histo2D[j][x].GetNbinsY(),histo2D[j][x].GetBinContent(i+1,histo2D[j][x].GetNbinsY())+histo2D[j][x].GetBinContent(i+1,histo2D[j][x].GetNbinsY()+1))
                histo2D[j][x].SetBinError  (i+1,histo2D[j][x].GetNbinsY(),pow(pow(histo2D[j][x].GetBinError(i+1,histo2D[j][x].GetNbinsY()),2)+pow(histo2D[j][x].GetBinError(i+1,histo2D[j][x].GetNbinsY()+1),2),0.5))
                histo2D[j][x].SetBinContent(i+1,histo2D[j][x].GetNbinsY()+1,0.0)
                histo2D[j][x].SetBinError  (i+1,histo2D[j][x].GetNbinsY()+1,0.0)

            for i in range(histo2D[j][x].GetNbinsY()):
                histo2D[j][x].SetBinContent(histo2D[j][x].GetNbinsX(),i+1,histo2D[j][x].GetBinContent(histo2D[j][x].GetNbinsX(),i+1)+histo2D[j][x].GetBinContent(histo2D[j][x].GetNbinsX()+1,i+1))
                histo2D[j][x].SetBinError  (histo2D[j][x].GetNbinsX(),i+1,pow(pow(histo2D[j][x].GetBinError(histo2D[j][x].GetNbinsX(),i+1),2)+pow(histo2D[j][x].GetBinError(histo2D[j][x].GetNbinsX()+1,i+1),2),0.5))
                histo2D[j][x].SetBinContent(histo2D[j][x].GetNbinsX()+1,i+1,0.0)
                histo2D[j][x].SetBinError  (histo2D[j][x].GetNbinsX()+1,i+1,0.0)

            if(x == plotCategory("kPlotEWKWZ")):
                histo[j][plotCategory("kPlotEWKWZ")]  .SetBinError(1,0.0)
                histo[j][plotCategory("kPlotSignal0")].SetBinError(1,0.0)
                histo[j][plotCategory("kPlotSignal1")].SetBinError(1,0.0)
                histo[j][plotCategory("kPlotSignal2")].SetBinError(1,0.0)
                histo[j][plotCategory("kPlotSignal3")].SetBinError(1,0.0)
                for i in range(histo[j][x].GetNbinsX()):
                    histo[j][plotCategory("kPlotEWKWZ")]  .SetBinContent(i+1,	     histo[j][plotCategory("kPlotEWKWZ")]  .GetBinContent(i+1)+       histo2D[j][x].GetBinContent(i+1,1))
                    histo[j][plotCategory("kPlotEWKWZ")]  .SetBinError  (i+1,pow(pow(histo[j][plotCategory("kPlotEWKWZ")]  .GetBinError  (i+1),2)+pow(histo2D[j][x].GetBinError  (i+1,1),2),0.5))

                    histo[j][plotCategory("kPlotSignal0")].SetBinContent(i+1,	     histo[j][plotCategory("kPlotSignal0")].GetBinContent(i+1)+       histo2D[j][x].GetBinContent(i+1,2))
                    histo[j][plotCategory("kPlotSignal0")].SetBinError  (i+1,pow(pow(histo[j][plotCategory("kPlotSignal0")].GetBinError  (i+1),2)+pow(histo2D[j][x].GetBinError  (i+1,2),2),0.5))

                    histo[j][plotCategory("kPlotSignal1")].SetBinContent(i+1,	     histo[j][plotCategory("kPlotSignal1")].GetBinContent(i+1)+       histo2D[j][x].GetBinContent(i+1,3))
                    histo[j][plotCategory("kPlotSignal1")].SetBinError  (i+1,pow(pow(histo[j][plotCategory("kPlotSignal1")].GetBinError  (i+1),2)+pow(histo2D[j][x].GetBinError  (i+1,3),2),0.5))

                    histo[j][plotCategory("kPlotSignal2")].SetBinContent(i+1,	     histo[j][plotCategory("kPlotSignal2")].GetBinContent(i+1)+       histo2D[j][x].GetBinContent(i+1,4))
                    histo[j][plotCategory("kPlotSignal2")].SetBinError  (i+1,pow(pow(histo[j][plotCategory("kPlotSignal2")].GetBinError  (i+1),2)+pow(histo2D[j][x].GetBinError  (i+1,4),2),0.5))

                    histo[j][plotCategory("kPlotSignal3")].SetBinContent(i+1,	     histo[j][plotCategory("kPlotSignal3")].GetBinContent(i+1)+       histo2D[j][x].GetBinContent(i+1,5))
                    histo[j][plotCategory("kPlotSignal3")].SetBinError  (i+1,pow(pow(histo[j][plotCategory("kPlotSignal3")].GetBinError  (i+1),2)+pow(histo2D[j][x].GetBinError  (i+1,5),2),0.5))

            else:
                for i in range(histo[j][x].GetNbinsX()):
                    histo[j][x].SetBinContent(i+1,	  histo[j][x].GetBinContent(i+1)+	histo2D[j][x].GetBinContent(i+1,1))
                    histo[j][x].SetBinError  (i+1,pow(pow(histo[j][x].GetBinError  (i+1),2)+pow(histo2D[j][x].GetBinError  (i+1,1),2),0.5))

    myfile = ROOT.TFile("fillhisto_wzAnalysis_sample{0}_year{1}_job{2}.root".format(count,year,whichJob),'RECREATE')
    for i in range(nCat):
        for j in range(nHisto):
            if(histo[j][i] == 0): continue
            histo[j][i].Write()
    for i in range(nhistoNonPrompt):
        if(histoNonPrompt[i] == 0): continue
        histoNonPrompt[i].Write()
    myfile.Close()

def readMCSample(sampleNOW,year,skimType,whichJob,group,ewkCorrWeights,wsWeights,puWeights,histoBTVEffEtaPtLF,histoBTVEffEtaPtCJ,histoBTVEffEtaPtBJ,histoFakeEtaPt_mu,histoFakeEtaPt_el,histoLepSFEtaPt_mu,histoLepSFEtaPt_el,histoTriggerSFEtaPt_0_0,histoTriggerSFEtaPt_0_1,histoTriggerSFEtaPt_0_2,histoTriggerSFEtaPt_0_3,histoTriggerSFEtaPt_1_0,histoTriggerSFEtaPt_1_1,histoTriggerSFEtaPt_1_2,histoTriggerSFEtaPt_1_3,histoTriggerSFEtaPt_2_0,histoTriggerSFEtaPt_2_1,histoTriggerSFEtaPt_2_2,histoTriggerSFEtaPt_2_3,histoTriggerSFEtaPt_3_0,histoTriggerSFEtaPt_3_1,histoTriggerSFEtaPt_3_2,histoTriggerSFEtaPt_3_3):

    files = getMClist(sampleNOW, skimType)
    print("Total files: {0}".format(len(files)))

    genEventSumWeight = 0
    genEventSumNoWeight = 0
    nTheoryReplicas = [103, 9, 4]
    genEventSumLHEScaleWeight = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    genEventSumPSWeight = [0, 0, 0, 0, 0]

    dfRuns = ROOT.RDataFrame("Runs", files)
    genEventSumWeight = dfRuns.Sum("genEventSumw").GetValue()
    genEventSumNoWeight = dfRuns.Sum("genEventCount").GetValue()
    try:
        if(dfRuns.Min("nLHEPdfSumw").GetValue() < nTheoryReplicas[0]):
            nTheoryReplicas[0] = int(dfRuns.Min("nLHEPdfSumw").GetValue())
    except Exception as e:
        nTheoryReplicas[0] = 0
    for n in range(9):
        try:
            if(dfRuns.Min("nLHEScaleSumw").GetValue() > n):
                dfRuns = dfRuns.Define("genEventSumLHEScaleWeight{0}".format(n),"LHEScaleSumw[{0}]".format(n))
                genEventSumLHEScaleWeight[n] = dfRuns.Sum("genEventSumLHEScaleWeight{0}".format(n)).GetValue()
            else:
                genEventSumLHEScaleWeight[n] = dfRuns.Count().GetValue()
                nTheoryReplicas[1] = int(dfRuns.Min("nLHEScaleSumw").GetValue())
        except Exception as e:
            genEventSumLHEScaleWeight[n] = dfRuns.Count().GetValue()
            nTheoryReplicas[1] = n
            print("Problem with LHEScaleWeights {0}".format(e))
    for n in range(4):
        try:
            if(dfRuns.Min("nPSSumw").GetValue() > n):
                dfRuns = dfRuns.Define("genEventSumPSWeight{0}".format(n),"PSSumw[{0}]".format(n))
                genEventSumPSWeight[n] = dfRuns.Sum("genEventSumPSWeight{0}".format(n)).GetValue()
            else:
                genEventSumPSWeight[n] = dfRuns.Count().GetValue()
                nTheoryReplicas[2] = int(dfRuns.Min("nPSSumw").GetValue())
        except Exception as e:
            genEventSumPSWeight[n] = dfRuns.Count().GetValue()
            nTheoryReplicas[2] = n
            print("Problem with PSWeights {0}".format(e))
    genEventSumPSWeight[4] = dfRuns.Count().GetValue()
    runGetEntries = dfRuns.Count().GetValue()

    print("Number of Theory replicas: {0} / {1} / {2}".format(nTheoryReplicas[0],nTheoryReplicas[1],nTheoryReplicas[2]))

    genEventSumLHEScaleRenorm = [1, 1, 1, 1, 1, 1]
    genEventSumPSRenorm = [1, 1, 1, 1]
    if(SwitchSample(sampleNOW,skimType)[2] == plotCategory("kPlotWZ") or
       SwitchSample(sampleNOW,skimType)[2] == plotCategory("kPlotEWKWZ") or
       SwitchSample(sampleNOW,skimType)[2] == plotCategory("kPlotZZ")):
        genEventSumLHEScaleRenorm[0] = genEventSumLHEScaleWeight[0] / genEventSumLHEScaleWeight[4]
        genEventSumLHEScaleRenorm[1] = genEventSumLHEScaleWeight[1] / genEventSumLHEScaleWeight[4]
        genEventSumLHEScaleRenorm[2] = genEventSumLHEScaleWeight[3] / genEventSumLHEScaleWeight[4]
        genEventSumLHEScaleRenorm[3] = genEventSumLHEScaleWeight[5] / genEventSumLHEScaleWeight[4]
        genEventSumLHEScaleRenorm[4] = genEventSumLHEScaleWeight[7] / genEventSumLHEScaleWeight[4]
        genEventSumLHEScaleRenorm[5] = genEventSumLHEScaleWeight[8] / genEventSumLHEScaleWeight[4]
        for n in range(4):
            genEventSumPSRenorm[n] = genEventSumPSWeight[n] / genEventSumPSWeight[4]
    print("genEventSumLHEScaleRenorm: ",genEventSumLHEScaleRenorm)
    print("genEventSumPSRenorm: ",genEventSumPSRenorm)

    weight = (SwitchSample(sampleNOW, skimType)[1] / genEventSumWeight)*getLumi(year)
    weightApprox = (SwitchSample(sampleNOW, skimType)[1] / genEventSumNoWeight)*getLumi(year)

    if(whichJob != -1):
        groupedFile = groupFiles(files, group)
        files = groupedFile[whichJob]
        if(len(files) == 0):
            print("no files in job/group: {0} / {1}".format(whichJob, group))
            return 0
        print("Used files: {0}".format(len(files)))

    df = ROOT.RDataFrame("Events", files)
    nevents = df.Count().GetValue()

    print("genEventSum({0}): {1} / Events(total/ntuple): {2} / {3}".format(runGetEntries,genEventSumWeight,genEventSumNoWeight,nevents))
    print("WeightExact/Approx %f / %f / Cross section: %f" %(weight, weightApprox, SwitchSample(sampleNOW, skimType)[1]))

    PDType = os.path.basename(SwitchSample(sampleNOW, skimType)[0]).split('+')[0]

    analysis(df,sampleNOW,SwitchSample(sampleNOW,skimType)[2],weight,year,PDType,"false",whichJob,nTheoryReplicas,genEventSumLHEScaleRenorm,genEventSumPSRenorm,ewkCorrWeights,wsWeights,puWeights,histoBTVEffEtaPtLF,histoBTVEffEtaPtCJ,histoBTVEffEtaPtBJ,histoFakeEtaPt_mu,histoFakeEtaPt_el,histoLepSFEtaPt_mu,histoLepSFEtaPt_el,histoTriggerSFEtaPt_0_0,histoTriggerSFEtaPt_0_1,histoTriggerSFEtaPt_0_2,histoTriggerSFEtaPt_0_3,histoTriggerSFEtaPt_1_0,histoTriggerSFEtaPt_1_1,histoTriggerSFEtaPt_1_2,histoTriggerSFEtaPt_1_3,histoTriggerSFEtaPt_2_0,histoTriggerSFEtaPt_2_1,histoTriggerSFEtaPt_2_2,histoTriggerSFEtaPt_2_3,histoTriggerSFEtaPt_3_0,histoTriggerSFEtaPt_3_1,histoTriggerSFEtaPt_3_2,histoTriggerSFEtaPt_3_3)

def readDASample(sampleNOW,year,skimType,whichJob,group,ewkCorrWeights,wsWeights,puWeights,histoBTVEffEtaPtLF,histoBTVEffEtaPtCJ,histoBTVEffEtaPtBJ,histoFakeEtaPt_mu,histoFakeEtaPt_el,histoLepSFEtaPt_mu,histoLepSFEtaPt_el,histoTriggerSFEtaPt_0_0,histoTriggerSFEtaPt_0_1,histoTriggerSFEtaPt_0_2,histoTriggerSFEtaPt_0_3,histoTriggerSFEtaPt_1_0,histoTriggerSFEtaPt_1_1,histoTriggerSFEtaPt_1_2,histoTriggerSFEtaPt_1_3,histoTriggerSFEtaPt_2_0,histoTriggerSFEtaPt_2_1,histoTriggerSFEtaPt_2_2,histoTriggerSFEtaPt_2_3,histoTriggerSFEtaPt_3_0,histoTriggerSFEtaPt_3_1,histoTriggerSFEtaPt_3_2,histoTriggerSFEtaPt_3_3):

    PDType = "0"
    if  (sampleNOW >= 1000 and sampleNOW <= 1009): PDType = "SingleMuon"
    elif(sampleNOW >= 1010 and sampleNOW <= 1019): PDType = "DoubleMuon"
    elif(sampleNOW >= 1020 and sampleNOW <= 1029): PDType = "MuonEG"
    elif(sampleNOW >= 1030 and sampleNOW <= 1039): PDType = "EGamma"
    elif(sampleNOW >= 1040 and sampleNOW <= 1049): PDType = "Muon"
    elif(sampleNOW >= 1050 and sampleNOW <= 1059): PDType = "MET"

    files = getDATAlist(sampleNOW, year, skimType)
    print("Total files: {0}".format(len(files)))

    if(whichJob != -1):
        groupedFile = groupFiles(files, group)
        files = groupedFile[whichJob]
        if(len(files) == 0):
            print("no files in job/group: {0} / {1}".format(whichJob, group))
            return 0
        print("Used files: {0}".format(len(files)))

    df = ROOT.RDataFrame("Events", files)

    genEventSumLHEScaleRenorm = [1, 1, 1, 1, 1, 1]
    genEventSumPSRenorm = [1, 1, 1, 1]

    weight=1.
    nevents = df.Count().GetValue()
    print("%s entries in the dataset" %nevents)

    analysis(df,sampleNOW,sampleNOW,weight,year,PDType,"true",whichJob,0,genEventSumLHEScaleRenorm,genEventSumPSRenorm,ewkCorrWeights,wsWeights,puWeights,histoBTVEffEtaPtLF,histoBTVEffEtaPtCJ,histoBTVEffEtaPtBJ,histoFakeEtaPt_mu,histoFakeEtaPt_el,histoLepSFEtaPt_mu,histoLepSFEtaPt_el,histoTriggerSFEtaPt_0_0,histoTriggerSFEtaPt_0_1,histoTriggerSFEtaPt_0_2,histoTriggerSFEtaPt_0_3,histoTriggerSFEtaPt_1_0,histoTriggerSFEtaPt_1_1,histoTriggerSFEtaPt_1_2,histoTriggerSFEtaPt_1_3,histoTriggerSFEtaPt_2_0,histoTriggerSFEtaPt_2_1,histoTriggerSFEtaPt_2_2,histoTriggerSFEtaPt_2_3,histoTriggerSFEtaPt_3_0,histoTriggerSFEtaPt_3_1,histoTriggerSFEtaPt_3_2,histoTriggerSFEtaPt_3_3)

if __name__ == "__main__":

    group = 2

    skimType = "3l"
    year = 2022
    process = -1
    whichJob = -1

    valid = ['year=', "process=", 'whichJob=', 'help']
    usage  =  "Usage: ana.py --year=<{0}>\n".format(year)
    usage +=  "              --process=<{0}>\n".format(process)
    usage +=  "              --whichJob=<{0}>".format(whichJob)
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", valid)
    except getopt.GetoptError as ex:
        print(usage)
        print(str(ex))
        sys.exit(1)

    for opt, arg in opts:
        if opt == "--help":
            print(usage)
            sys.exit(1)
        if opt == "--year":
            year = int(arg)
        if opt == "--process":
            process = int(arg)
        if opt == "--whichJob":
            whichJob = int(arg)

    ewkCorrWeights = []
    ewkCorrPath = "data/VV_NLO_LO_CMS_mjj.root"
    fewkCorrFile = ROOT.TFile(ewkCorrPath)
    ewkCorrWeights.append(fewkCorrFile.Get("hWW13p6_KF_CMS"))
    ewkCorrWeights.append(fewkCorrFile.Get("hWZ13p0_KF_CMS"))
    ewkCorrWeights.append(fewkCorrFile.Get("hWW13p6_KF_CMSUp"))
    ewkCorrWeights.append(fewkCorrFile.Get("hWZ13p0_KF_CMSUp"))
    for x in range(4):
        ewkCorrWeights[x].SetDirectory(0)
    fewkCorrFile.Close()

    wsWeights = []
    wsPath = "data/histoWSSF_{0}.root".format(year)
    fwsFile = ROOT.TFile(wsPath)
    wsWeights.append(fwsFile.Get("histoWSEtaSF"))
    wsWeights.append(fwsFile.Get("histoWSEtaSF_unc"))
    wsWeights.append(fwsFile.Get("histoWSEtaPtSF"))
    for x in range(3):
        wsWeights[x].SetDirectory(0)
    fwsFile.Close()

    puWeights = []
    puPath = "data/puWeights_UL_{0}.root".format(year)
    fPuFile = ROOT.TFile(puPath)
    puWeights.append(fPuFile.Get("puWeights"))
    puWeights.append(fPuFile.Get("puWeightsUp"))
    puWeights.append(fPuFile.Get("puWeightsDown"))
    for x in range(3):
        puWeights[x].SetDirectory(0)
    fPuFile.Close()

    histoFakeEtaPt_mu = []
    histoFakeEtaPt_el = []
    fakePath = "data/histoFakeEtaPt_{0}.root".format(year)
    fFakeFile = ROOT.TFile(fakePath)
    histoFakeEtaPt_mu.append(fFakeFile.Get("histoFakeEffSelEtaPt_0_{0}_fakeAnalysis1001_anaType1".format(muSelChoice)))
    histoFakeEtaPt_mu.append(fFakeFile.Get("histoFakeEffSelEtaPt_0_{0}_fakeAnalysis1002_anaType1".format(muSelChoice)))
    histoFakeEtaPt_mu.append(fFakeFile.Get("histoFakeEffSelEtaPt_0_{0}_fakeAnalysis1003_anaType1".format(muSelChoice)))
    histoFakeEtaPt_mu.append(fFakeFile.Get("histoFakeEffSelEtaPt_0_{0}_fakeAnalysis1001_anaType2".format(muSelChoice)))
    histoFakeEtaPt_mu.append(fFakeFile.Get("histoFakeEffSelEtaPt_0_{0}_fakeAnalysis1002_anaType2".format(muSelChoice)))
    histoFakeEtaPt_mu.append(fFakeFile.Get("histoFakeEffSelEtaPt_0_{0}_fakeAnalysis1003_anaType2".format(muSelChoice)))
    histoFakeEtaPt_mu.append(fFakeFile.Get("histoFakeEffSelEtaPt_0_{0}_fakeAnalysis1001_anaType3".format(muSelChoice)))
    histoFakeEtaPt_mu.append(fFakeFile.Get("histoFakeEffSelEtaPt_0_{0}_fakeAnalysis1002_anaType3".format(muSelChoice)))
    histoFakeEtaPt_mu.append(fFakeFile.Get("histoFakeEffSelEtaPt_0_{0}_fakeAnalysis1003_anaType3".format(muSelChoice)))
    histoFakeEtaPt_el.append(fFakeFile.Get("histoFakeEffSelEtaPt_1_{0}_fakeAnalysis1001_anaType1".format(elSelChoice)))
    histoFakeEtaPt_el.append(fFakeFile.Get("histoFakeEffSelEtaPt_1_{0}_fakeAnalysis1002_anaType1".format(elSelChoice)))
    histoFakeEtaPt_el.append(fFakeFile.Get("histoFakeEffSelEtaPt_1_{0}_fakeAnalysis1003_anaType1".format(elSelChoice)))
    histoFakeEtaPt_el.append(fFakeFile.Get("histoFakeEffSelEtaPt_1_{0}_fakeAnalysis1001_anaType2".format(elSelChoice)))
    histoFakeEtaPt_el.append(fFakeFile.Get("histoFakeEffSelEtaPt_1_{0}_fakeAnalysis1002_anaType2".format(elSelChoice)))
    histoFakeEtaPt_el.append(fFakeFile.Get("histoFakeEffSelEtaPt_1_{0}_fakeAnalysis1003_anaType2".format(elSelChoice)))
    histoFakeEtaPt_el.append(fFakeFile.Get("histoFakeEffSelEtaPt_1_{0}_fakeAnalysis1001_anaType3".format(elSelChoice)))
    histoFakeEtaPt_el.append(fFakeFile.Get("histoFakeEffSelEtaPt_1_{0}_fakeAnalysis1002_anaType3".format(elSelChoice)))
    histoFakeEtaPt_el.append(fFakeFile.Get("histoFakeEffSelEtaPt_1_{0}_fakeAnalysis1003_anaType3".format(elSelChoice)))
    for x in range(9):
        histoFakeEtaPt_mu[x].SetDirectory(0)
        histoFakeEtaPt_el[x].SetDirectory(0)
    fFakeFile.Close()

    lepSFPath = "data/histoLepSFEtaPt_{0}{1}.root".format(year,correctionString)
    fLepSFFile = ROOT.TFile(lepSFPath)
    histoLepSFEtaPt_mu = fLepSFFile.Get("histoLepSFEtaPt_0_{0}".format(muSelChoice))
    histoLepSFEtaPt_el = fLepSFFile.Get("histoLepSFEtaPt_1_{0}".format(elSelChoice))
    histoLepSFEtaPt_mu.SetDirectory(0)
    histoLepSFEtaPt_el.SetDirectory(0)
    fLepSFFile.Close()

    triggerSFPath = "data/histoTriggerSFEtaPt_{0}.root".format(year)
    fTriggerSFFile = ROOT.TFile(triggerSFPath)
    histoTriggerSFEtaPt_0_0 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_0_0")
    histoTriggerSFEtaPt_0_1 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_0_1")
    histoTriggerSFEtaPt_0_2 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_0_2")
    histoTriggerSFEtaPt_0_3 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_0_3")
    histoTriggerSFEtaPt_1_0 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_1_0")
    histoTriggerSFEtaPt_1_1 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_1_1")
    histoTriggerSFEtaPt_1_2 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_1_2")
    histoTriggerSFEtaPt_1_3 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_1_3")
    histoTriggerSFEtaPt_2_0 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_2_0")
    histoTriggerSFEtaPt_2_1 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_2_1")
    histoTriggerSFEtaPt_2_2 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_2_2")
    histoTriggerSFEtaPt_2_3 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_2_3")
    histoTriggerSFEtaPt_3_0 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_3_0")
    histoTriggerSFEtaPt_3_1 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_3_1")
    histoTriggerSFEtaPt_3_2 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_3_2")
    histoTriggerSFEtaPt_3_3 = fTriggerSFFile.Get("histoTriggerV1SFEtaPt_3_3")
    histoTriggerSFEtaPt_0_0.SetDirectory(0)
    histoTriggerSFEtaPt_0_1.SetDirectory(0)
    histoTriggerSFEtaPt_0_2.SetDirectory(0)
    histoTriggerSFEtaPt_0_3.SetDirectory(0)
    histoTriggerSFEtaPt_1_0.SetDirectory(0)
    histoTriggerSFEtaPt_1_1.SetDirectory(0)
    histoTriggerSFEtaPt_1_2.SetDirectory(0)
    histoTriggerSFEtaPt_1_3.SetDirectory(0)
    histoTriggerSFEtaPt_2_0.SetDirectory(0)
    histoTriggerSFEtaPt_2_1.SetDirectory(0)
    histoTriggerSFEtaPt_2_2.SetDirectory(0)
    histoTriggerSFEtaPt_2_3.SetDirectory(0)
    histoTriggerSFEtaPt_3_0.SetDirectory(0)
    histoTriggerSFEtaPt_3_1.SetDirectory(0)
    histoTriggerSFEtaPt_3_2.SetDirectory(0)
    histoTriggerSFEtaPt_3_3.SetDirectory(0)
    fTriggerSFFile.Close()

    BTVEffPath = "data/histoBtagEffSelEtaPt_{0}.root".format(year)
    fBTVEffPathFile = ROOT.TFile(BTVEffPath)
    histoBTVEffEtaPtLF = fBTVEffPathFile.Get("histoBtagEffSelEtaPt_{0}".format(0+3*bTagSel))
    histoBTVEffEtaPtCJ = fBTVEffPathFile.Get("histoBtagEffSelEtaPt_{0}".format(1+3*bTagSel))
    histoBTVEffEtaPtBJ = fBTVEffPathFile.Get("histoBtagEffSelEtaPt_{0}".format(2+3*bTagSel))
    histoBTVEffEtaPtLF.SetDirectory(0)
    histoBTVEffEtaPtCJ.SetDirectory(0)
    histoBTVEffEtaPtBJ.SetDirectory(0)
    fBTVEffPathFile.Close()

    try:
        if(process >= 0 and process < 1000):
            readMCSample(process,year,skimType,whichJob,group,ewkCorrWeights,wsWeights,puWeights,histoBTVEffEtaPtLF,histoBTVEffEtaPtCJ,histoBTVEffEtaPtBJ,histoFakeEtaPt_mu,histoFakeEtaPt_el,histoLepSFEtaPt_mu,histoLepSFEtaPt_el,histoTriggerSFEtaPt_0_0,histoTriggerSFEtaPt_0_1,histoTriggerSFEtaPt_0_2,histoTriggerSFEtaPt_0_3,histoTriggerSFEtaPt_1_0,histoTriggerSFEtaPt_1_1,histoTriggerSFEtaPt_1_2,histoTriggerSFEtaPt_1_3,histoTriggerSFEtaPt_2_0,histoTriggerSFEtaPt_2_1,histoTriggerSFEtaPt_2_2,histoTriggerSFEtaPt_2_3,histoTriggerSFEtaPt_3_0,histoTriggerSFEtaPt_3_1,histoTriggerSFEtaPt_3_2,histoTriggerSFEtaPt_3_3)
        elif(process >= 1000):
            readDASample(process,year,skimType,whichJob,group,ewkCorrWeights,wsWeights,puWeights,histoBTVEffEtaPtLF,histoBTVEffEtaPtCJ,histoBTVEffEtaPtBJ,histoFakeEtaPt_mu,histoFakeEtaPt_el,histoLepSFEtaPt_mu,histoLepSFEtaPt_el,histoTriggerSFEtaPt_0_0,histoTriggerSFEtaPt_0_1,histoTriggerSFEtaPt_0_2,histoTriggerSFEtaPt_0_3,histoTriggerSFEtaPt_1_0,histoTriggerSFEtaPt_1_1,histoTriggerSFEtaPt_1_2,histoTriggerSFEtaPt_1_3,histoTriggerSFEtaPt_2_0,histoTriggerSFEtaPt_2_1,histoTriggerSFEtaPt_2_2,histoTriggerSFEtaPt_2_3,histoTriggerSFEtaPt_3_0,histoTriggerSFEtaPt_3_1,histoTriggerSFEtaPt_3_2,histoTriggerSFEtaPt_3_3)
    except Exception as e:
        print("FAILED {0}".format(e))
