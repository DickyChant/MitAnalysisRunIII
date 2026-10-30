import ROOT
import os, sys, getopt, json

ROOT.ROOT.EnableImplicitMT(10)
from utilsCategory import plotCategory
from utilsAna import getMClist, getDATAlist
from utilsAna import SwitchSample, groupFiles, getTriggerFromJson, getLeptomSelFromJson, getLumi
from utilsSelection import selectionTauVeto, selectionPhoton, selectionJetMet, selection2LVar, selectionLGVar, selectionTrigger2L, selectionElMu, selectionWeigths, selectionGenLepJet, makeFinalVariable2DVar
from utilsMVA import redefineVBSIncMVAVariables, redefineVBSPolMVAVariables
import tmva_helper_xml
from array import array

correctionString = "_correction"
makeDataCards = 1 # 1 (mjj diff), 2 (mll diff), 3 (njets diff), 4 (detajj diff), 5 (dphijj diff), 6 (mjj), 7 (mll), 8 (njets), 9 (detajj), 10 (dphijj), 11 (zepvv), 12 (pol3D), 13 (pol2DLX), 14 (polLL)
genVBSSel = makeDataCards
if(genVBSSel == 6):
    genVBSSel = 1
    genVBSSel = 0
elif(genVBSSel == 7):
    genVBSSel = 2
    genVBSSel = 0
elif(genVBSSel == 8):
    genVBSSel = 3
    genVBSSel = 0
elif(genVBSSel == 9):
    genVBSSel = 4
    genVBSSel = 0
elif(genVBSSel == 10):
    genVBSSel = 5
    genVBSSel = 0
elif(genVBSSel == 11):
    genVBSSel = 1
    genVBSSel = 0

versionCharges = 0
versionWG = False
versionDoEWKQCD = False
doNtuples = False
# 0 = T, 1 = M, 2 = L
bTagSel = 1
useBTaggingWeights = 1
if(versionWG == True):
    bTagSel = 1

useFR = 1
whichAna = 2

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

altMass = "Def"
jetEtaCut = 4.7
metCut = 30.0

muSelChoice = 8
MUOWP = "Medium"

elSelChoice = 7
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

    if(versionWG == True):
        FAKE_EL   = getLeptomSelFromJson(overallLeptonSel, "FAKE_PHO_EL",   year)
        TIGHT_EL  = getLeptomSelFromJson(overallLeptonSel, "TIGHT_PHO_EL",  year, 1)

    dftag = selectionElMu(dftag,year,FAKE_MU,TIGHT_MU,FAKE_EL,TIGHT_EL)

    dftag =(dftag.Filter("nLoose == 2","Only two loose leptons")
                 .Filter("nFake == 2","Two fake leptons")
                 .Filter("Sum(fake_Muon_charge)+Sum(fake_Electron_charge) != 0", "Sign-sign leptons")
                 .Define("eventNum", "event")
                 )

    if(versionCharges > 0):
        dftag = dftag.Filter("Sum(fake_Muon_charge)+Sum(fake_Electron_charge) > 0", "Positive events")
    elif(versionCharges < 0):
        dftag = dftag.Filter("Sum(fake_Muon_charge)+Sum(fake_Electron_charge) < 0", "Negative events")

    if(versionWG == True):
        dftag = dftag.Filter("Sum(fake_Muon_charge) == 1 and Sum(fake_Electron_charge) == 1","emu events only")

    if(useFR == 0):
        dftag = dftag.Filter("nTight == 2","Two tight leptons")

    dftag = selectionJetMet (dftag,year,bTagSel,isData,count,jetEtaCut)
    dftag = selection2LVar  (dftag,year,isData)

    dftag = (dftag.Filter("ptl1{0} > 25 && ptl2{0} > 20".format(altMass),"ptl1 > 25 && ptl2 > 20")
                  .Filter("mll{0} > 20".format(altMass),"mll > 20 GeV")
                  )

    dftag = selectionTauVeto(dftag,year,isData)
    dftag = selectionPhoton (dftag,year,BARRELphotons,ENDCAPphotons)
    dftag = selectionLGVar  (dftag,year,isData)

    return dftag

def analysis(df,count,category,weight,year,PDType,isData,whichJob,nTheoryReplicas,genEventSumLHEScaleRenorm,genEventSumPSRenorm,ewkCorrWeights,wsWeights,puWeights,histoBTVEffEtaPtLF,histoBTVEffEtaPtCJ,histoBTVEffEtaPtBJ,histoFakeEtaPt_mu,histoFakeEtaPt_el,histoLepSFEtaPt_mu,histoLepSFEtaPt_el,histoTriggerSFEtaPt_0_0,histoTriggerSFEtaPt_0_1,histoTriggerSFEtaPt_0_2,histoTriggerSFEtaPt_0_3,histoTriggerSFEtaPt_1_0,histoTriggerSFEtaPt_1_1,histoTriggerSFEtaPt_1_2,histoTriggerSFEtaPt_1_3,histoTriggerSFEtaPt_2_0,histoTriggerSFEtaPt_2_1,histoTriggerSFEtaPt_2_2,histoTriggerSFEtaPt_2_3,histoTriggerSFEtaPt_3_0,histoTriggerSFEtaPt_3_1,histoTriggerSFEtaPt_3_2,histoTriggerSFEtaPt_3_3):

    print("starting {0} / {1} / {2} / {3} / {4} / {5} / {6}".format(count,category,weight,year,PDType,isData,whichJob))

    theCat = category
    if(theCat > 100): theCat = plotCategory("kPlotData")
    if(theCat == plotCategory("kPlotqqWW") or theCat == plotCategory("kPlotggWW") or
       theCat == plotCategory("kPlotDY") or theCat == plotCategory("kPlotTT") or
       theCat == plotCategory("kPlotTW")):
        theCat = plotCategory("kPlotWS")
    elif(theCat == plotCategory("kPlotHiggs")):
        theCat = plotCategory("kPlotVVV")

    nCat, nHisto, nhistoWS, nhistoNonPrompt, nHistoMVA = plotCategory("kPlotCategories"), 600, 20, 50, 1200
    histo = [[0 for y in range(nCat)] for x in range(nHisto)]
    histoWS = [0 for y in range(nhistoWS)]
    histoNonPrompt = [0 for y in range(nhistoNonPrompt)]
    histo2D  = [[0 for y in range(nCat)] for x in range(nHistoMVA)]
    histoMVA = [[0 for y in range(nCat)] for x in range(nHistoMVA)]

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
            "vbs_mjj",
            "vbs_ptjj",
            "vbs_detajj",
            "vbs_dphijj",
            "vbs_ptj1",
            "vbs_ptj2",
            "vbs_etaj1",
            "vbs_etaj2",
            "vbs_zepvv",
            "vbs_zepmax",
            "vbs_sumHT",
            "vbs_ptvv",
            "vbs_pttot",
            "vbs_detavvj1",
            "vbs_detavvj2",
            "vbs_ptbalance",
            "vbs_dphijjll",
            "vbs_rpt",
            "mll{0}".format(altMass),
	    "ptll{0}".format(altMass),
	    "drll{0}".format(altMass),
	    "dphill{0}".format(altMass),
	    "ptl1{0}".format(altMass),
	    "ptl2{0}".format(altMass),
	    "dPhilMETMin{0}".format(altMass),
	    "minPMET{0}".format(altMass),
	    "ptww{0}".format(altMass),
	    "mcoll{0}".format(altMass),
	    "mtwmax{0}".format(altMass),
	    "mtwmin{0}".format(altMass),
            "PuppiMET_ptDef"
    ]:
        branchList.push_back(branchName)

    #ROOT.gInterpreter.ProcessLine('''
    #TMVA::Experimental::RReader model("weights_mva/bdt_BDTG_vbfinc_v0.weights.xml");
    #computeModel = TMVA::Experimental::Compute<15, float>(model);
    #''')
    #variables = ROOT.model.GetVariableNames()
    #print(variables)

    #MVAweightsType0 = "weights_mva/bdt_BDTG_vbfinc_v0.weights.xml"
    #MVAweightsType0 = "weights_mva/bdt_BDTG_vbfinc_nsel2_v0.weights.xml"
    MVAweightsType0 = "weights_mva/bdt_BDTG_vbfinc_nsel3_v0.weights.xml"
    #MVAweightsType0 = "weights_mva/bdt_BDTG_vbfinc_pcut30_nsel2_v0.weights.xml"
    tmva_helperType0 = tmva_helper_xml.TMVAHelperXML(MVAweightsType0)
    print(tmva_helperType0.variables)

    MVAweightsType1 = "weights_mva/bdt_BDTG_vbfpolwwcm_nsel1_v8.weights.xml"
    #MVAweightsType1 = "weights_mva/bdt_BDTG_vbfpolwwcm_pcut30_nsel1_v7.weights.xml"
    tmva_helperType1 = tmva_helper_xml.TMVAHelperXML(MVAweightsType1)
    print(tmva_helperType1.variables)

    MVAweightsType2 = "weights_mva/bdt_BDTG_vbfpolwwcm_nsel2_v8.weights.xml"
    #MVAweightsType1 = "weights_mva/bdt_BDTG_vbfpolwwcm_pcut30_nsel2_v7.weights.xml"
    tmva_helperType2 = tmva_helper_xml.TMVAHelperXML(MVAweightsType2)
    print(tmva_helperType2.variables)

    dftag = selectionLL(df,year,PDType,isData,count)

    if(isData == "false"):
        dftag = selectionGenLepJet(dftag,20,30,5.0)
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
                    .Define("theCat","compute_category({0},kPlotNonPrompt,kPlotWS,nFake,nTight,nWS)".format(theCat))
                   #.Define("bdt_vbfinc", ROOT.computeModel, ROOT.model.GetVariableNames())
                    )

    dfbase = tmva_helperType0.run_inference(dfbase,"bdt_vbfinc")
    dfbase = tmva_helperType1.run_inference(dfbase,"bdt_vbfpol0",1)
    dfbase = tmva_helperType2.run_inference(dfbase,"bdt_vbfpol1",1)

    dfwwcat = []
    dfwwbcat = []
    dfwwvbscat = []
    dfwwbvbscat = []
    dfwwjjcat = []
    dfwwbjjcat = []

    dfwwvbs2Jcat              = []
    dfwwvbs3Jcat              = []
    dfwwvbs4Jcat              = []
    dfwwvbscatMuonMomUp       = []
    dfwwvbscatElectronMomUp   = []
    dfwwvbscatJes00Up         = []
    dfwwvbscatJes01Up         = []
    dfwwvbscatJes02Up         = []
    dfwwvbscatJes03Up         = []
    dfwwvbscatJes04Up         = []
    dfwwvbscatJes05Up         = []
    dfwwvbscatJes06Up         = []
    dfwwvbscatJes07Up         = []
    dfwwvbscatJes08Up         = []
    dfwwvbscatJes09Up         = []
    dfwwvbscatJes10Up         = []
    dfwwvbscatJes11Up         = []
    dfwwvbscatJes12Up         = []
    dfwwvbscatJes13Up         = []
    dfwwvbscatJes14Up         = []
    dfwwvbscatJes15Up         = []
    dfwwvbscatJes16Up         = []
    dfwwvbscatJes17Up         = []
    dfwwvbscatJes18Up         = []
    dfwwvbscatJes19Up         = []
    dfwwvbscatJes20Up         = []
    dfwwvbscatJes21Up         = []
    dfwwvbscatJes22Up         = []
    dfwwvbscatJes23Up         = []
    dfwwvbscatJes24Up         = []
    dfwwvbscatJes25Up         = []
    dfwwvbscatJes26Up         = []
    dfwwvbscatJes27Up         = []
    dfwwvbscatJerUp           = []
    dfwwvbscatJERUp           = []
    dfwwvbscatJESUp           = []
    dfwwvbscatUnclusteredUp   = []

    dfwwbvbs2Jcat             = []
    dfwwbvbs3Jcat             = []
    dfwwbvbs4Jcat             = []
    dfwwbvbscatMuonMomUp      = []
    dfwwbvbscatElectronMomUp  = []
    dfwwbvbscatJes00Up        = []
    dfwwbvbscatJes01Up        = []
    dfwwbvbscatJes02Up        = []
    dfwwbvbscatJes03Up        = []
    dfwwbvbscatJes04Up        = []
    dfwwbvbscatJes05Up        = []
    dfwwbvbscatJes06Up        = []
    dfwwbvbscatJes07Up        = []
    dfwwbvbscatJes08Up        = []
    dfwwbvbscatJes09Up        = []
    dfwwbvbscatJes10Up        = []
    dfwwbvbscatJes11Up        = []
    dfwwbvbscatJes12Up        = []
    dfwwbvbscatJes13Up        = []
    dfwwbvbscatJes14Up        = []
    dfwwbvbscatJes15Up        = []
    dfwwbvbscatJes16Up        = []
    dfwwbvbscatJes17Up        = []
    dfwwbvbscatJes18Up        = []
    dfwwbvbscatJes19Up        = []
    dfwwbvbscatJes20Up        = []
    dfwwbvbscatJes21Up        = []
    dfwwbvbscatJes22Up        = []
    dfwwbvbscatJes23Up        = []
    dfwwbvbscatJes24Up        = []
    dfwwbvbscatJes25Up        = []
    dfwwbvbscatJes26Up        = []
    dfwwbvbscatJes27Up        = []
    dfwwbvbscatJerUp          = []
    dfwwbvbscatJERUp          = []
    dfwwbvbscatJESUp          = []
    dfwwbvbscatUnclusteredUp  = []
    for x in range(nCat):
        dfwwcat.append(dfbase.Filter("theCat=={0}".format(x), "correct category ({0})".format(x)))

        if((x == plotCategory("kPlotEWKSSWW") or (x == plotCategory("kPlotQCDSSWW") and versionDoEWKQCD == True)) and isData == "false"):
            dfwwcat[x] = (dfwwcat[x].Define("theGenCat" , "compute_vbs_gen_category({0},ngood_GenJets,good_GenJet_pt,good_GenJet_eta,good_GenJet_phi,good_GenJet_mass,ngood_GenDressedLeptons,good_GenDressedLepton_pdgId,good_GenDressedLepton_hasTauAnc,good_GenDressedLepton_pt,good_GenDressedLepton_eta,good_GenDressedLepton_phi,good_GenDressedLepton_mass,3)".format(genVBSSel))
                                    )
        else:
            dfwwcat[x] = (dfwwcat[x].Define("theGenCat","{0}".format(0))
                                    )
        dfwwvbscatMuonMomUp    .append(dfwwcat[x])
        dfwwvbscatElectronMomUp.append(dfwwcat[x])
        dfwwvbscatJes00Up      .append(dfwwcat[x])
        dfwwvbscatJes01Up      .append(dfwwcat[x])
        dfwwvbscatJes02Up      .append(dfwwcat[x])
        dfwwvbscatJes03Up      .append(dfwwcat[x])
        dfwwvbscatJes04Up      .append(dfwwcat[x])
        dfwwvbscatJes05Up      .append(dfwwcat[x])
        dfwwvbscatJes06Up      .append(dfwwcat[x])
        dfwwvbscatJes07Up      .append(dfwwcat[x])
        dfwwvbscatJes08Up      .append(dfwwcat[x])
        dfwwvbscatJes09Up      .append(dfwwcat[x])
        dfwwvbscatJes10Up      .append(dfwwcat[x])
        dfwwvbscatJes11Up      .append(dfwwcat[x])
        dfwwvbscatJes12Up      .append(dfwwcat[x])
        dfwwvbscatJes13Up      .append(dfwwcat[x])
        dfwwvbscatJes14Up      .append(dfwwcat[x])
        dfwwvbscatJes15Up      .append(dfwwcat[x])
        dfwwvbscatJes16Up      .append(dfwwcat[x])
        dfwwvbscatJes17Up      .append(dfwwcat[x])
        dfwwvbscatJes18Up      .append(dfwwcat[x])
        dfwwvbscatJes19Up      .append(dfwwcat[x])
        dfwwvbscatJes20Up      .append(dfwwcat[x])
        dfwwvbscatJes21Up      .append(dfwwcat[x])
        dfwwvbscatJes22Up      .append(dfwwcat[x])
        dfwwvbscatJes23Up      .append(dfwwcat[x])
        dfwwvbscatJes24Up      .append(dfwwcat[x])
        dfwwvbscatJes25Up      .append(dfwwcat[x])
        dfwwvbscatJes26Up      .append(dfwwcat[x])
        dfwwvbscatJes27Up      .append(dfwwcat[x])
        dfwwvbscatJerUp        .append(dfwwcat[x])
        dfwwvbscatJERUp        .append(dfwwcat[x])
        dfwwvbscatJESUp        .append(dfwwcat[x])
        dfwwvbscatUnclusteredUp.append(dfwwcat[x])

        dfwwbvbscatMuonMomUp    .append(dfwwcat[x])
        dfwwbvbscatElectronMomUp.append(dfwwcat[x])
        dfwwbvbscatJes00Up      .append(dfwwcat[x])
        dfwwbvbscatJes01Up      .append(dfwwcat[x])
        dfwwbvbscatJes02Up      .append(dfwwcat[x])
        dfwwbvbscatJes03Up      .append(dfwwcat[x])
        dfwwbvbscatJes04Up      .append(dfwwcat[x])
        dfwwbvbscatJes05Up      .append(dfwwcat[x])
        dfwwbvbscatJes06Up      .append(dfwwcat[x])
        dfwwbvbscatJes07Up      .append(dfwwcat[x])
        dfwwbvbscatJes08Up      .append(dfwwcat[x])
        dfwwbvbscatJes09Up      .append(dfwwcat[x])
        dfwwbvbscatJes10Up      .append(dfwwcat[x])
        dfwwbvbscatJes11Up      .append(dfwwcat[x])
        dfwwbvbscatJes12Up      .append(dfwwcat[x])
        dfwwbvbscatJes13Up      .append(dfwwcat[x])
        dfwwbvbscatJes14Up      .append(dfwwcat[x])
        dfwwbvbscatJes15Up      .append(dfwwcat[x])
        dfwwbvbscatJes16Up      .append(dfwwcat[x])
        dfwwbvbscatJes17Up      .append(dfwwcat[x])
        dfwwbvbscatJes18Up      .append(dfwwcat[x])
        dfwwbvbscatJes19Up      .append(dfwwcat[x])
        dfwwbvbscatJes20Up      .append(dfwwcat[x])
        dfwwbvbscatJes21Up      .append(dfwwcat[x])
        dfwwbvbscatJes22Up      .append(dfwwcat[x])
        dfwwbvbscatJes23Up      .append(dfwwcat[x])
        dfwwbvbscatJes24Up      .append(dfwwcat[x])
        dfwwbvbscatJes25Up      .append(dfwwcat[x])
        dfwwbvbscatJes26Up      .append(dfwwcat[x])
        dfwwbvbscatJes27Up      .append(dfwwcat[x])
        dfwwbvbscatJerUp        .append(dfwwcat[x])
        dfwwbvbscatJERUp        .append(dfwwcat[x])
        dfwwbvbscatJESUp        .append(dfwwcat[x])
        dfwwbvbscatUnclusteredUp.append(dfwwcat[x])

        dfwwvbscatMuonMomUp     [x] = dfwwvbscatMuonMomUp     [x].Filter("mllMuonMomUp     > 20 && ptl1MuonMomUp     > 25 && ptl2MuonMomUp     > 20 && (DiLepton_flavor != 2 || abs(mllMuonMomUp     -91.1876) > 15) && nbtag_goodbtag_Jet_bjet        == 0 && nvbs_jets        >= 2 && vbs_mjj        > 500 && vbs_detajj        > 2.5 && vbs_zepvv        < 0.75 && PuppiMET_ptDef	> {1}".format(altMass,metCut))
        dfwwvbscatElectronMomUp [x] = dfwwvbscatElectronMomUp [x].Filter("mllElectronMomUp > 20 && ptl1ElectronMomUp > 25 && ptl2ElectronMomUp > 20 && (DiLepton_flavor != 2 || abs(mllElectronMomUp -91.1876) > 15) && nbtag_goodbtag_Jet_bjet        == 0 && nvbs_jets        >= 2 && vbs_mjj        > 500 && vbs_detajj        > 2.5 && vbs_zepvv        < 0.75 && PuppiMET_ptDef	> {1}".format(altMass,metCut))
        dfwwvbscatJes00Up       [x] = dfwwvbscatJes00Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes00Up == 0 && nvbs_jetsJes00Up >= 2 && vbs_mjjJes00Up > 500 && vbs_detajjJes00Up > 2.5 && vbs_zepvvJes00Up < 0.75 && PuppiMET_ptJes00Up > {1}".format(altMass,metCut))
        dfwwvbscatJes01Up       [x] = dfwwvbscatJes01Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes01Up == 0 && nvbs_jetsJes01Up >= 2 && vbs_mjjJes01Up > 500 && vbs_detajjJes01Up > 2.5 && vbs_zepvvJes01Up < 0.75 && PuppiMET_ptJes01Up > {1}".format(altMass,metCut))
        dfwwvbscatJes02Up       [x] = dfwwvbscatJes02Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes02Up == 0 && nvbs_jetsJes02Up >= 2 && vbs_mjjJes02Up > 500 && vbs_detajjJes02Up > 2.5 && vbs_zepvvJes02Up < 0.75 && PuppiMET_ptJes02Up > {1}".format(altMass,metCut))
        dfwwvbscatJes03Up       [x] = dfwwvbscatJes03Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes03Up == 0 && nvbs_jetsJes03Up >= 2 && vbs_mjjJes03Up > 500 && vbs_detajjJes03Up > 2.5 && vbs_zepvvJes03Up < 0.75 && PuppiMET_ptJes03Up > {1}".format(altMass,metCut))
        dfwwvbscatJes04Up       [x] = dfwwvbscatJes04Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes04Up == 0 && nvbs_jetsJes04Up >= 2 && vbs_mjjJes04Up > 500 && vbs_detajjJes04Up > 2.5 && vbs_zepvvJes04Up < 0.75 && PuppiMET_ptJes04Up > {1}".format(altMass,metCut))
        dfwwvbscatJes05Up       [x] = dfwwvbscatJes05Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes05Up == 0 && nvbs_jetsJes05Up >= 2 && vbs_mjjJes05Up > 500 && vbs_detajjJes05Up > 2.5 && vbs_zepvvJes05Up < 0.75 && PuppiMET_ptJes05Up > {1}".format(altMass,metCut))
        dfwwvbscatJes06Up       [x] = dfwwvbscatJes06Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes06Up == 0 && nvbs_jetsJes06Up >= 2 && vbs_mjjJes06Up > 500 && vbs_detajjJes06Up > 2.5 && vbs_zepvvJes06Up < 0.75 && PuppiMET_ptJes06Up > {1}".format(altMass,metCut))
        dfwwvbscatJes07Up       [x] = dfwwvbscatJes07Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes07Up == 0 && nvbs_jetsJes07Up >= 2 && vbs_mjjJes07Up > 500 && vbs_detajjJes07Up > 2.5 && vbs_zepvvJes07Up < 0.75 && PuppiMET_ptJes07Up > {1}".format(altMass,metCut))
        dfwwvbscatJes08Up       [x] = dfwwvbscatJes08Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes08Up == 0 && nvbs_jetsJes08Up >= 2 && vbs_mjjJes08Up > 500 && vbs_detajjJes08Up > 2.5 && vbs_zepvvJes08Up < 0.75 && PuppiMET_ptJes08Up > {1}".format(altMass,metCut))
        dfwwvbscatJes09Up       [x] = dfwwvbscatJes09Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes09Up == 0 && nvbs_jetsJes09Up >= 2 && vbs_mjjJes09Up > 500 && vbs_detajjJes09Up > 2.5 && vbs_zepvvJes09Up < 0.75 && PuppiMET_ptJes09Up > {1}".format(altMass,metCut))
        dfwwvbscatJes10Up       [x] = dfwwvbscatJes10Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes10Up == 0 && nvbs_jetsJes10Up >= 2 && vbs_mjjJes10Up > 500 && vbs_detajjJes10Up > 2.5 && vbs_zepvvJes10Up < 0.75 && PuppiMET_ptJes10Up > {1}".format(altMass,metCut))
        dfwwvbscatJes11Up       [x] = dfwwvbscatJes11Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes11Up == 0 && nvbs_jetsJes11Up >= 2 && vbs_mjjJes11Up > 500 && vbs_detajjJes11Up > 2.5 && vbs_zepvvJes11Up < 0.75 && PuppiMET_ptJes11Up > {1}".format(altMass,metCut))
        dfwwvbscatJes12Up       [x] = dfwwvbscatJes12Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes12Up == 0 && nvbs_jetsJes12Up >= 2 && vbs_mjjJes12Up > 500 && vbs_detajjJes12Up > 2.5 && vbs_zepvvJes12Up < 0.75 && PuppiMET_ptJes12Up > {1}".format(altMass,metCut))
        dfwwvbscatJes13Up       [x] = dfwwvbscatJes13Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes13Up == 0 && nvbs_jetsJes13Up >= 2 && vbs_mjjJes13Up > 500 && vbs_detajjJes13Up > 2.5 && vbs_zepvvJes13Up < 0.75 && PuppiMET_ptJes13Up > {1}".format(altMass,metCut))
        dfwwvbscatJes14Up       [x] = dfwwvbscatJes14Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes14Up == 0 && nvbs_jetsJes14Up >= 2 && vbs_mjjJes14Up > 500 && vbs_detajjJes14Up > 2.5 && vbs_zepvvJes14Up < 0.75 && PuppiMET_ptJes14Up > {1}".format(altMass,metCut))
        dfwwvbscatJes15Up       [x] = dfwwvbscatJes15Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes15Up == 0 && nvbs_jetsJes15Up >= 2 && vbs_mjjJes15Up > 500 && vbs_detajjJes15Up > 2.5 && vbs_zepvvJes15Up < 0.75 && PuppiMET_ptJes15Up > {1}".format(altMass,metCut))
        dfwwvbscatJes16Up       [x] = dfwwvbscatJes16Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes16Up == 0 && nvbs_jetsJes16Up >= 2 && vbs_mjjJes16Up > 500 && vbs_detajjJes16Up > 2.5 && vbs_zepvvJes16Up < 0.75 && PuppiMET_ptJes16Up > {1}".format(altMass,metCut))
        dfwwvbscatJes17Up       [x] = dfwwvbscatJes17Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes17Up == 0 && nvbs_jetsJes17Up >= 2 && vbs_mjjJes17Up > 500 && vbs_detajjJes17Up > 2.5 && vbs_zepvvJes17Up < 0.75 && PuppiMET_ptJes17Up > {1}".format(altMass,metCut))
        dfwwvbscatJes18Up       [x] = dfwwvbscatJes18Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes18Up == 0 && nvbs_jetsJes18Up >= 2 && vbs_mjjJes18Up > 500 && vbs_detajjJes18Up > 2.5 && vbs_zepvvJes18Up < 0.75 && PuppiMET_ptJes18Up > {1}".format(altMass,metCut))
        dfwwvbscatJes19Up       [x] = dfwwvbscatJes19Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes19Up == 0 && nvbs_jetsJes19Up >= 2 && vbs_mjjJes19Up > 500 && vbs_detajjJes19Up > 2.5 && vbs_zepvvJes19Up < 0.75 && PuppiMET_ptJes19Up > {1}".format(altMass,metCut))
        dfwwvbscatJes20Up       [x] = dfwwvbscatJes20Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes20Up == 0 && nvbs_jetsJes20Up >= 2 && vbs_mjjJes20Up > 500 && vbs_detajjJes20Up > 2.5 && vbs_zepvvJes20Up < 0.75 && PuppiMET_ptJes20Up > {1}".format(altMass,metCut))
        dfwwvbscatJes21Up       [x] = dfwwvbscatJes21Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes21Up == 0 && nvbs_jetsJes21Up >= 2 && vbs_mjjJes21Up > 500 && vbs_detajjJes21Up > 2.5 && vbs_zepvvJes21Up < 0.75 && PuppiMET_ptJes21Up > {1}".format(altMass,metCut))
        dfwwvbscatJes22Up       [x] = dfwwvbscatJes22Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes22Up == 0 && nvbs_jetsJes22Up >= 2 && vbs_mjjJes22Up > 500 && vbs_detajjJes22Up > 2.5 && vbs_zepvvJes22Up < 0.75 && PuppiMET_ptJes22Up > {1}".format(altMass,metCut))
        dfwwvbscatJes23Up       [x] = dfwwvbscatJes23Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes23Up == 0 && nvbs_jetsJes23Up >= 2 && vbs_mjjJes23Up > 500 && vbs_detajjJes23Up > 2.5 && vbs_zepvvJes23Up < 0.75 && PuppiMET_ptJes23Up > {1}".format(altMass,metCut))
        dfwwvbscatJes24Up       [x] = dfwwvbscatJes24Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes24Up == 0 && nvbs_jetsJes24Up >= 2 && vbs_mjjJes24Up > 500 && vbs_detajjJes24Up > 2.5 && vbs_zepvvJes24Up < 0.75 && PuppiMET_ptJes24Up > {1}".format(altMass,metCut))
        dfwwvbscatJes25Up       [x] = dfwwvbscatJes25Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes25Up == 0 && nvbs_jetsJes25Up >= 2 && vbs_mjjJes25Up > 500 && vbs_detajjJes25Up > 2.5 && vbs_zepvvJes25Up < 0.75 && PuppiMET_ptJes25Up > {1}".format(altMass,metCut))
        dfwwvbscatJes26Up       [x] = dfwwvbscatJes26Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes26Up == 0 && nvbs_jetsJes26Up >= 2 && vbs_mjjJes26Up > 500 && vbs_detajjJes26Up > 2.5 && vbs_zepvvJes26Up < 0.75 && PuppiMET_ptJes26Up > {1}".format(altMass,metCut))
        dfwwvbscatJes27Up       [x] = dfwwvbscatJes27Up       [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes27Up == 0 && nvbs_jetsJes27Up >= 2 && vbs_mjjJes27Up > 500 && vbs_detajjJes27Up > 2.5 && vbs_zepvvJes27Up < 0.75 && PuppiMET_ptJes27Up > {1}".format(altMass,metCut))
        dfwwvbscatJerUp         [x] = dfwwvbscatJerUp         [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJerUp   == 0 && nvbs_jetsJerUp   >= 2 && vbs_mjjJerUp   > 500 && vbs_detajjJerUp   > 2.5 && vbs_zepvvJerUp   < 0.75 && PuppiMET_ptJerUp	 > {1}".format(altMass,metCut))
        dfwwvbscatJERUp         [x] = dfwwvbscatJERUp         [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjet        == 0 && nvbs_jets        >= 2 && vbs_mjj        > 500 && vbs_detajj        > 2.5 && vbs_zepvv        < 0.75 && PuppiMET_ptJESlUp  > {1}".format(altMass,metCut))
        dfwwvbscatJESUp         [x] = dfwwvbscatJESUp         [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjet        == 0 && nvbs_jets        >= 2 && vbs_mjj        > 500 && vbs_detajj        > 2.5 && vbs_zepvv        < 0.75 && PuppiMET_ptJERlUp  > {1}".format(altMass,metCut))
        dfwwvbscatUnclusteredUp [x] = dfwwvbscatUnclusteredUp [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjet        == 0 && nvbs_jets        >= 2 && vbs_mjj        > 500 && vbs_detajj        > 2.5 && vbs_zepvv        < 0.75 && PuppiMET_ptUnclUp  > {1}".format(altMass,metCut))

        dfwwbvbscatMuonMomUp    [x] = dfwwbvbscatMuonMomUp    [x].Filter("mllMuonMomUp     > 20 && ptl1MuonMomUp     > 25 && ptl2MuonMomUp     > 20 && (DiLepton_flavor != 2 || abs(mllMuonMomUp     -91.1876) > 15) && nbtag_goodbtag_Jet_bjet        >  0 && nvbs_jets        >= 2 && vbs_mjj        > 500 && vbs_detajj        > 2.5 && vbs_zepvv        < 0.75 && PuppiMET_ptDef	> {1}".format(altMass,metCut))
        dfwwbvbscatElectronMomUp[x] = dfwwbvbscatElectronMomUp[x].Filter("mllElectronMomUp > 20 && ptl1ElectronMomUp > 25 && ptl2ElectronMomUp > 20 && (DiLepton_flavor != 2 || abs(mllElectronMomUp -91.1876) > 15) && nbtag_goodbtag_Jet_bjet        >  0 && nvbs_jets        >= 2 && vbs_mjj        > 500 && vbs_detajj        > 2.5 && vbs_zepvv        < 0.75 && PuppiMET_ptDef	> {1}".format(altMass,metCut))
        dfwwbvbscatJes00Up      [x] = dfwwbvbscatJes00Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes00Up >  0 && nvbs_jetsJes00Up >= 2 && vbs_mjjJes00Up > 500 && vbs_detajjJes00Up > 2.5 && vbs_zepvvJes00Up < 0.75 && PuppiMET_ptJes00Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes01Up      [x] = dfwwbvbscatJes01Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes01Up >  0 && nvbs_jetsJes01Up >= 2 && vbs_mjjJes01Up > 500 && vbs_detajjJes01Up > 2.5 && vbs_zepvvJes01Up < 0.75 && PuppiMET_ptJes01Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes02Up      [x] = dfwwbvbscatJes02Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes02Up >  0 && nvbs_jetsJes02Up >= 2 && vbs_mjjJes02Up > 500 && vbs_detajjJes02Up > 2.5 && vbs_zepvvJes02Up < 0.75 && PuppiMET_ptJes02Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes03Up      [x] = dfwwbvbscatJes03Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes03Up >  0 && nvbs_jetsJes03Up >= 2 && vbs_mjjJes03Up > 500 && vbs_detajjJes03Up > 2.5 && vbs_zepvvJes03Up < 0.75 && PuppiMET_ptJes03Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes04Up      [x] = dfwwbvbscatJes04Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes04Up >  0 && nvbs_jetsJes04Up >= 2 && vbs_mjjJes04Up > 500 && vbs_detajjJes04Up > 2.5 && vbs_zepvvJes04Up < 0.75 && PuppiMET_ptJes04Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes05Up      [x] = dfwwbvbscatJes05Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes05Up >  0 && nvbs_jetsJes05Up >= 2 && vbs_mjjJes05Up > 500 && vbs_detajjJes05Up > 2.5 && vbs_zepvvJes05Up < 0.75 && PuppiMET_ptJes05Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes06Up      [x] = dfwwbvbscatJes06Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes06Up >  0 && nvbs_jetsJes06Up >= 2 && vbs_mjjJes06Up > 500 && vbs_detajjJes06Up > 2.5 && vbs_zepvvJes06Up < 0.75 && PuppiMET_ptJes06Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes07Up      [x] = dfwwbvbscatJes07Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes07Up >  0 && nvbs_jetsJes07Up >= 2 && vbs_mjjJes07Up > 500 && vbs_detajjJes07Up > 2.5 && vbs_zepvvJes07Up < 0.75 && PuppiMET_ptJes07Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes08Up      [x] = dfwwbvbscatJes08Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes08Up >  0 && nvbs_jetsJes08Up >= 2 && vbs_mjjJes08Up > 500 && vbs_detajjJes08Up > 2.5 && vbs_zepvvJes08Up < 0.75 && PuppiMET_ptJes08Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes09Up      [x] = dfwwbvbscatJes09Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes09Up >  0 && nvbs_jetsJes09Up >= 2 && vbs_mjjJes09Up > 500 && vbs_detajjJes09Up > 2.5 && vbs_zepvvJes09Up < 0.75 && PuppiMET_ptJes09Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes10Up      [x] = dfwwbvbscatJes10Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes10Up >  0 && nvbs_jetsJes10Up >= 2 && vbs_mjjJes10Up > 500 && vbs_detajjJes10Up > 2.5 && vbs_zepvvJes10Up < 0.75 && PuppiMET_ptJes10Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes11Up      [x] = dfwwbvbscatJes11Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes11Up >  0 && nvbs_jetsJes11Up >= 2 && vbs_mjjJes11Up > 500 && vbs_detajjJes11Up > 2.5 && vbs_zepvvJes11Up < 0.75 && PuppiMET_ptJes11Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes12Up      [x] = dfwwbvbscatJes12Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes12Up >  0 && nvbs_jetsJes12Up >= 2 && vbs_mjjJes12Up > 500 && vbs_detajjJes12Up > 2.5 && vbs_zepvvJes12Up < 0.75 && PuppiMET_ptJes12Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes13Up      [x] = dfwwbvbscatJes13Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes13Up >  0 && nvbs_jetsJes13Up >= 2 && vbs_mjjJes13Up > 500 && vbs_detajjJes13Up > 2.5 && vbs_zepvvJes13Up < 0.75 && PuppiMET_ptJes13Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes14Up      [x] = dfwwbvbscatJes14Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes14Up >  0 && nvbs_jetsJes14Up >= 2 && vbs_mjjJes14Up > 500 && vbs_detajjJes14Up > 2.5 && vbs_zepvvJes14Up < 0.75 && PuppiMET_ptJes14Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes15Up      [x] = dfwwbvbscatJes15Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes15Up >  0 && nvbs_jetsJes15Up >= 2 && vbs_mjjJes15Up > 500 && vbs_detajjJes15Up > 2.5 && vbs_zepvvJes15Up < 0.75 && PuppiMET_ptJes15Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes16Up      [x] = dfwwbvbscatJes16Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes16Up >  0 && nvbs_jetsJes16Up >= 2 && vbs_mjjJes16Up > 500 && vbs_detajjJes16Up > 2.5 && vbs_zepvvJes16Up < 0.75 && PuppiMET_ptJes16Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes17Up      [x] = dfwwbvbscatJes17Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes17Up >  0 && nvbs_jetsJes17Up >= 2 && vbs_mjjJes17Up > 500 && vbs_detajjJes17Up > 2.5 && vbs_zepvvJes17Up < 0.75 && PuppiMET_ptJes17Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes18Up      [x] = dfwwbvbscatJes18Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes18Up >  0 && nvbs_jetsJes18Up >= 2 && vbs_mjjJes18Up > 500 && vbs_detajjJes18Up > 2.5 && vbs_zepvvJes18Up < 0.75 && PuppiMET_ptJes18Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes19Up      [x] = dfwwbvbscatJes19Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes19Up >  0 && nvbs_jetsJes19Up >= 2 && vbs_mjjJes19Up > 500 && vbs_detajjJes19Up > 2.5 && vbs_zepvvJes19Up < 0.75 && PuppiMET_ptJes19Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes20Up      [x] = dfwwbvbscatJes20Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes20Up >  0 && nvbs_jetsJes20Up >= 2 && vbs_mjjJes20Up > 500 && vbs_detajjJes20Up > 2.5 && vbs_zepvvJes20Up < 0.75 && PuppiMET_ptJes20Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes21Up      [x] = dfwwbvbscatJes21Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes21Up >  0 && nvbs_jetsJes21Up >= 2 && vbs_mjjJes21Up > 500 && vbs_detajjJes21Up > 2.5 && vbs_zepvvJes21Up < 0.75 && PuppiMET_ptJes21Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes22Up      [x] = dfwwbvbscatJes22Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes22Up >  0 && nvbs_jetsJes22Up >= 2 && vbs_mjjJes22Up > 500 && vbs_detajjJes22Up > 2.5 && vbs_zepvvJes22Up < 0.75 && PuppiMET_ptJes22Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes23Up      [x] = dfwwbvbscatJes23Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes23Up >  0 && nvbs_jetsJes23Up >= 2 && vbs_mjjJes23Up > 500 && vbs_detajjJes23Up > 2.5 && vbs_zepvvJes23Up < 0.75 && PuppiMET_ptJes23Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes24Up      [x] = dfwwbvbscatJes24Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes24Up >  0 && nvbs_jetsJes24Up >= 2 && vbs_mjjJes24Up > 500 && vbs_detajjJes24Up > 2.5 && vbs_zepvvJes24Up < 0.75 && PuppiMET_ptJes24Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes25Up      [x] = dfwwbvbscatJes25Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes25Up >  0 && nvbs_jetsJes25Up >= 2 && vbs_mjjJes25Up > 500 && vbs_detajjJes25Up > 2.5 && vbs_zepvvJes25Up < 0.75 && PuppiMET_ptJes25Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes26Up      [x] = dfwwbvbscatJes26Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes26Up >  0 && nvbs_jetsJes26Up >= 2 && vbs_mjjJes26Up > 500 && vbs_detajjJes26Up > 2.5 && vbs_zepvvJes26Up < 0.75 && PuppiMET_ptJes26Up > {1}".format(altMass,metCut))
        dfwwbvbscatJes27Up      [x] = dfwwbvbscatJes27Up      [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJes27Up >  0 && nvbs_jetsJes27Up >= 2 && vbs_mjjJes27Up > 500 && vbs_detajjJes27Up > 2.5 && vbs_zepvvJes27Up < 0.75 && PuppiMET_ptJes27Up > {1}".format(altMass,metCut))
        dfwwbvbscatJerUp        [x] = dfwwbvbscatJerUp        [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjetJerUp   >  0 && nvbs_jetsJerUp   >= 2 && vbs_mjjJerUp   > 500 && vbs_detajjJerUp   > 2.5 && vbs_zepvvJerUp   < 0.75 && PuppiMET_ptJerUp	 > {1}".format(altMass,metCut))
        dfwwbvbscatJERUp        [x] = dfwwbvbscatJERUp        [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjet        >  0 && nvbs_jets        >= 2 && vbs_mjj        > 500 && vbs_detajj        > 2.5 && vbs_zepvv        < 0.75 && PuppiMET_ptJESlUp  > {1}".format(altMass,metCut))
        dfwwbvbscatJESUp        [x] = dfwwbvbscatJESUp        [x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjet        >  0 && nvbs_jets        >= 2 && vbs_mjj        > 500 && vbs_detajj        > 2.5 && vbs_zepvv        < 0.75 && PuppiMET_ptJERlUp  > {1}".format(altMass,metCut))
        dfwwbvbscatUnclusteredUp[x] = dfwwbvbscatUnclusteredUp[x].Filter("mll{0}           > 20 && ptl1{0}           > 25 && ptl2{0}           > 20 && (DiLepton_flavor != 2 || abs(mll{0}           -91.1876) > 15) && nbtag_goodbtag_Jet_bjet        >  0 && nvbs_jets        >= 2 && vbs_mjj        > 500 && vbs_detajj        > 2.5 && vbs_zepvv        < 0.75 && PuppiMET_ptUnclUp  > {1}".format(altMass,metCut))

        histo[ 0][x] = dfwwcat[x].Histo1D(("histo_{0}_{1}".format( 0,x), "histo_{0}_{1}".format( 0,x),40, 20, 220), "mll{0}".format(altMass),"weightNoBTag")
        dfwwcat[x] = dfwwcat[x].Filter("DiLepton_flavor != 2 || abs(mll{0}-91.1876) > 15".format(altMass),"Z veto")

        dfwwbcat.append(dfwwcat[x].Filter("nbtag_goodbtag_Jet_bjet > 0","at least one good b-jets"))

        histo[ 1][x] = dfwwcat[x].Histo1D(("histo_{0}_{1}".format( 1,x), "histo_{0}_{1}".format( 1,x), 5,-0.5 ,4.5),     "nbtag_goodbtag_Jet_bjet","weight")
        dfwwcat[x] = dfwwcat[x].Filter("nbtag_goodbtag_Jet_bjet == 0","no good b-jets")

        histo[ 2][x] = dfwwcat[x] .Histo1D(("histo_{0}_{1}".format( 2,x), "histo_{0}_{1}".format( 2,x), 4,-0.5, 3.5), "ltype","weight")
        histo[ 3][x] = dfwwbcat[x].Histo1D(("histo_{0}_{1}".format( 3,x), "histo_{0}_{1}".format( 3,x), 4,-0.5, 3.5), "ltype","weight")
        histo[ 4][x] = dfwwcat[x] .Histo1D(("histo_{0}_{1}".format( 4,x), "histo_{0}_{1}".format( 4,x), 6,-0.5, 5.5), "ngood_jets","weight")
        histo[ 5][x] = dfwwbcat[x].Histo1D(("histo_{0}_{1}".format( 5,x), "histo_{0}_{1}".format( 5,x), 6,-0.5, 5.5), "ngood_jets","weight")

        dfwwcat[x]  = dfwwcat[x] .Filter("nvbs_jets >= 2 && vbs_mjj > 200", "vbs_mjj > 200")
        dfwwbcat[x] = dfwwbcat[x].Filter("nvbs_jets >= 2 && vbs_mjj > 200", "vbs_mjj > 200")
        histo[14][x] = dfwwcat[x] .Histo1D(("histo_{0}_{1}".format(14,x), "histo_{0}_{1}".format(14,x), 20,0,2), "vbs_zepvv","weight")
        histo[15][x] = dfwwbcat[x].Histo1D(("histo_{0}_{1}".format(15,x), "histo_{0}_{1}".format(15,x), 20,0,2), "vbs_zepvv","weight")

        dfwwcat[x]  = dfwwcat[x] .Filter("vbs_zepvv < 0.75", "vbs_zepvv < 0.75")
        dfwwbcat[x] = dfwwbcat[x].Filter("vbs_zepvv < 0.75", "vbs_zepvv < 0.75")
        histo[12][x] = dfwwcat[x] .Histo1D(("histo_{0}_{1}".format(12,x), "histo_{0}_{1}".format(12,x), 18,0.0,9.0), "vbs_detajj","weight")
        histo[13][x] = dfwwbcat[x].Histo1D(("histo_{0}_{1}".format(13,x), "histo_{0}_{1}".format(13,x), 18,0.0,9.0), "vbs_detajj","weight")

        histo[ 6][x] = dfwwcat[x] .Histo1D(("histo_{0}_{1}".format( 6,x), "histo_{0}_{1}".format( 6,x), 4,-0.5, 3.5), "ltype","weight")
        histo[ 7][x] = dfwwbcat[x].Histo1D(("histo_{0}_{1}".format( 7,x), "histo_{0}_{1}".format( 7,x), 4,-0.5, 3.5), "ltype","weight")
        histo[ 8][x] = dfwwcat[x] .Histo1D(("histo_{0}_{1}".format( 8,x), "histo_{0}_{1}".format( 8,x), 4, 1.5, 5.5), "ngood_jets","weight")
        histo[ 9][x] = dfwwbcat[x].Histo1D(("histo_{0}_{1}".format( 9,x), "histo_{0}_{1}".format( 9,x), 4, 1.5, 5.5), "ngood_jets","weight")
        histo[10][x] = dfwwcat[x] .Histo1D(("histo_{0}_{1}".format(10,x), "histo_{0}_{1}".format(10,x), 16,200,2600), "vbs_mjj","weight")
        histo[11][x] = dfwwbcat[x].Histo1D(("histo_{0}_{1}".format(11,x), "histo_{0}_{1}".format(11,x), 16,200,2600), "vbs_mjj","weight")

        for ltype in range(4):
            histo[70+ltype][x] = dfwwcat[x] .Filter("ltype == {0}".format(ltype)).Histo1D(("histo_{0}_{1}".format(70+ltype,x), "histo_{0}_{1}".format(70+ltype,x),20, 20, 120), "ptl2{0}".format(altMass),"weight")
            histo[74+ltype][x] = dfwwbcat[x].Filter("ltype == {0}".format(ltype)).Histo1D(("histo_{0}_{1}".format(74+ltype,x), "histo_{0}_{1}".format(74+ltype,x),20, 20, 120), "ptl2{0}".format(altMass),"weight")
            histo[78+ltype][x] = dfwwcat[x] .Filter("ltype == {0}".format(ltype)).Histo1D(("histo_{0}_{1}".format(78+ltype,x), "histo_{0}_{1}".format(78+ltype,x),12, 0, 2.4), "etal2","weight")
            histo[82+ltype][x] = dfwwbcat[x].Filter("ltype == {0}".format(ltype)).Histo1D(("histo_{0}_{1}".format(82+ltype,x), "histo_{0}_{1}".format(82+ltype,x),12, 0, 2.4), "etal2","weight")

        dfwwvbscat .append(dfwwcat[x] .Filter(VBSSEL, "VBS selection"))
        dfwwbvbscat.append(dfwwbcat[x].Filter(VBSSEL, "VBS selection"))
        histo[16][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(16,x), "histo_{0}_{1}".format(16,x),25,  0, 250), "PuppiMET_pt{0}".format(altMass),"weight")
        histo[17][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(17,x), "histo_{0}_{1}".format(17,x),25,  0, 250), "PuppiMET_pt{0}".format(altMass),"weight")
        histo[54][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(54,x), "histo_{0}_{1}".format(54,x),30, -3.16, 3.16), "PuppiMET_phi{0}".format(altMass),"weight")
        histo[55][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(55,x), "histo_{0}_{1}".format(55,x),30, -3.16, 3.16), "PuppiMET_phi{0}".format(altMass),"weight")

        dfwwvbscat[x]  = dfwwvbscat[x] .Filter("PuppiMET_pt{0} > {1}".format(altMass,metCut), "PuppiMET_pt > cut")
        dfwwbvbscat[x] = dfwwbvbscat[x].Filter("PuppiMET_pt{0} > {1}".format(altMass,metCut), "PuppiMET_pt > cut")
        histo[18][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(18,x), "histo_{0}_{1}".format(18,x), 4,-0.5, 3.5), "ltype","weight")
        histo[19][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(19,x), "histo_{0}_{1}".format(19,x), 4,-0.5, 3.5), "ltype","weight")
        histo[20][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(20,x), "histo_{0}_{1}".format(20,x), 4, 1.5, 5.5), "ngood_jets","weight")
        histo[21][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(21,x), "histo_{0}_{1}".format(21,x), 4, 1.5, 5.5), "ngood_jets","weight")

        histo[22][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(22,x), "histo_{0}_{1}".format(22,x), 25,500,3000), "vbs_mjj","weight")
        histo[23][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(23,x), "histo_{0}_{1}".format(23,x), 25,500,3000), "vbs_mjj","weight")
        histo[24][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(24,x), "histo_{0}_{1}".format(24,x), 14,2.5,9.5), "vbs_detajj","weight")
        histo[25][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(25,x), "histo_{0}_{1}".format(25,x), 14,2.5,9.5), "vbs_detajj","weight")
        histo[26][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(26,x), "histo_{0}_{1}".format(26,x), 10,0,3.1416), "vbs_dphijj","weight")
        histo[27][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(27,x), "histo_{0}_{1}".format(27,x), 10,0,3.1416), "vbs_dphijj","weight")
        histo[28][x] = dfwwvbscat[x] .Filter("vbs_zepvv<0.75").Histo1D(("histo_{0}_{1}".format(28,x), "histo_{0}_{1}".format(28,x), 10,0,0.75), "vbs_zepvv","weight")
        histo[29][x] = dfwwbvbscat[x].Filter("vbs_zepvv<0.75").Histo1D(("histo_{0}_{1}".format(29,x), "histo_{0}_{1}".format(29,x), 10,0,0.75), "vbs_zepvv","weight")
        histo[30][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(30,x), "histo_{0}_{1}".format(30,x), 20,-1,1), "bdt_vbfinc","weight")
        histo[31][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(31,x), "histo_{0}_{1}".format(31,x), 20,-1,1), "bdt_vbfinc","weight")
        histo[32][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(32,x), "histo_{0}_{1}".format(32,x),25, 50, 300), "vbs_ptj1","weight")
        histo[33][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(33,x), "histo_{0}_{1}".format(33,x),25, 50, 300), "vbs_ptj1","weight")
        histo[34][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(34,x), "histo_{0}_{1}".format(34,x),25, 50, 300), "vbs_ptj2","weight")
        histo[35][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(35,x), "histo_{0}_{1}".format(35,x),25, 50, 300), "vbs_ptj2","weight")
        histo[36][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(36,x), "histo_{0}_{1}".format(36,x),20, 0, 4.8), "vbs_etaj1","weight")
        histo[37][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(37,x), "histo_{0}_{1}".format(37,x),20, 0, 4.8), "vbs_etaj1","weight")
        histo[38][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(38,x), "histo_{0}_{1}".format(38,x),20, 0, 4.8), "vbs_etaj2","weight")
        histo[39][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(39,x), "histo_{0}_{1}".format(39,x),20, 0, 4.8), "vbs_etaj2","weight")
        histo[56][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(56,x), "histo_{0}_{1}".format(56,x),30, -3.16, 3.16), "vbs_phij1","weight")
        histo[57][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(57,x), "histo_{0}_{1}".format(57,x),30, -3.16, 3.16), "vbs_phij1","weight")
        histo[58][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(58,x), "histo_{0}_{1}".format(58,x),30, -3.16, 3.16), "vbs_phij2","weight")
        histo[59][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(59,x), "histo_{0}_{1}".format(59,x),30, -3.16, 3.16), "vbs_phij2","weight")

        histo[112][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(112,x), "histo_{0}_{1}".format(112,x), 20,-1,1), "bdt_vbfpol0","weight")
        histo[113][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(113,x), "histo_{0}_{1}".format(113,x), 20,-1,1), "bdt_vbfpol0","weight")
        histo[114][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(114,x), "histo_{0}_{1}".format(114,x), 20,-1,1), "bdt_vbfpol1","weight")
        histo[115][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(115,x), "histo_{0}_{1}".format(115,x), 20,-1,1), "bdt_vbfpol1","weight")

        histo[116][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(116,x), "histo_{0}_{1}".format(116,x), 4,-0.5, 3.5), "ltype","weightFakeAll0")
        histo[117][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(117,x), "histo_{0}_{1}".format(117,x), 4,-0.5, 3.5), "ltype","weightFakeAll1")
        histo[118][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(118,x), "histo_{0}_{1}".format(118,x), 4,-0.5, 3.5), "ltype","weightFakeAll2")
        histo[119][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(119,x), "histo_{0}_{1}".format(119,x), 4,-0.5, 3.5), "ltype","weightFakeAll3")
        histo[120][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(120,x), "histo_{0}_{1}".format(120,x), 4,-0.5, 3.5), "ltype","weightFakeAll4")
        histo[121][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(121,x), "histo_{0}_{1}".format(121,x), 4,-0.5, 3.5), "ltype","weightFakeAll5")
        histo[122][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(122,x), "histo_{0}_{1}".format(122,x), 4,-0.5, 3.5), "ltype","weightFakeAll6")
        histo[123][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(123,x), "histo_{0}_{1}".format(123,x), 4,-0.5, 3.5), "ltype","weightFakeAll7")
        histo[124][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(124,x), "histo_{0}_{1}".format(124,x), 4,-0.5, 3.5), "ltype","weightFakeAll8")

        histo[125][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(125,x), "histo_{0}_{1}".format(125,x), 4,-0.5, 3.5), "ltype","weightFakeAll0")
        histo[126][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(126,x), "histo_{0}_{1}".format(126,x), 4,-0.5, 3.5), "ltype","weightFakeAll1")
        histo[127][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(127,x), "histo_{0}_{1}".format(127,x), 4,-0.5, 3.5), "ltype","weightFakeAll2")
        histo[128][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(128,x), "histo_{0}_{1}".format(128,x), 4,-0.5, 3.5), "ltype","weightFakeAll3")
        histo[129][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(129,x), "histo_{0}_{1}".format(129,x), 4,-0.5, 3.5), "ltype","weightFakeAll4")
        histo[130][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(130,x), "histo_{0}_{1}".format(130,x), 4,-0.5, 3.5), "ltype","weightFakeAll5")
        histo[131][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(131,x), "histo_{0}_{1}".format(131,x), 4,-0.5, 3.5), "ltype","weightFakeAll6")
        histo[132][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(132,x), "histo_{0}_{1}".format(132,x), 4,-0.5, 3.5), "ltype","weightFakeAll7")
        histo[133][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(133,x), "histo_{0}_{1}".format(133,x), 4,-0.5, 3.5), "ltype","weightFakeAll8")

        histo[60][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(60,x), "histo_{0}_{1}".format(60,x),20, 25, 225), "ptl1{0}".format(altMass),"weight")
        histo[61][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(61,x), "histo_{0}_{1}".format(61,x),20, 25, 225), "ptl1{0}".format(altMass),"weight")
        histo[62][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(62,x), "histo_{0}_{1}".format(62,x),20, 20, 120), "ptl2{0}".format(altMass),"weight")
        histo[63][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(63,x), "histo_{0}_{1}".format(63,x),20, 20, 120), "ptl2{0}".format(altMass),"weight")
        histo[64][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(64,x), "histo_{0}_{1}".format(64,x),16, 20, 340), "mll{0}".format(altMass),"weight")
        histo[65][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(65,x), "histo_{0}_{1}".format(65,x),16, 20, 340), "mll{0}".format(altMass),"weight")
        histo[66][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(66,x), "histo_{0}_{1}".format(66,x),12, 0, 2.4), "etal1","weight")
        histo[67][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(67,x), "histo_{0}_{1}".format(67,x),12, 0, 2.4), "etal1","weight")
        histo[68][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(68,x), "histo_{0}_{1}".format(68,x),12, 0, 2.4), "etal2","weight")
        histo[69][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(69,x), "histo_{0}_{1}".format(69,x),12, 0, 2.4), "etal2","weight")

        histo[86][x] = dfwwvbscat[x].Filter("vbs_mjj < 900 && mll{0} < 140".format(altMass)).Histo1D(("histo_{0}_{1}".format(86,x), "histo_{0}_{1}".format(86,x),24, 20, 140), "mll{0}".format(altMass),"weight")
        histo[87][x] = dfwwvbscat[x].Filter("vbs_mjj > 900 && mll{0} < 140".format(altMass)).Histo1D(("histo_{0}_{1}".format(87,x), "histo_{0}_{1}".format(87,x),24, 20, 140), "mll{0}".format(altMass),"weight")
        histo[88][x] = dfwwvbscat[x].Filter("vbs_mjj < 900 && mll{0} <  80".format(altMass)).Histo1D(("histo_{0}_{1}".format(88,x), "histo_{0}_{1}".format(88,x),4,-0.5, 3.5), "ltype","weight")
        histo[89][x] = dfwwvbscat[x].Filter("vbs_mjj > 900 && mll{0} <  80".format(altMass)).Histo1D(("histo_{0}_{1}".format(89,x), "histo_{0}_{1}".format(89,x),4,-0.5, 3.5), "ltype","weight")
        histo[90][x] = dfwwvbscat[x].Filter("vbs_mjj < 900 && mll{0} <  80".format(altMass)).Histo1D(("histo_{0}_{1}".format(90,x), "histo_{0}_{1}".format(90,x),20, 0, 200), "ptll{0}".format(altMass),"weight")
        histo[91][x] = dfwwvbscat[x].Filter("vbs_mjj > 900 && mll{0} <  80".format(altMass)).Histo1D(("histo_{0}_{1}".format(91,x), "histo_{0}_{1}".format(91,x),20, 0, 200), "ptll{0}".format(altMass),"weight")
        histo[92][x] = dfwwvbscat[x].Filter("vbs_mjj < 900 && mll{0} <  80".format(altMass)).Histo1D(("histo_{0}_{1}".format(92,x), "histo_{0}_{1}".format(92,x),20,30, 230), "PuppiMET_pt{0}".format(altMass),"weight")
        histo[93][x] = dfwwvbscat[x].Filter("vbs_mjj > 900 && mll{0} <  80".format(altMass)).Histo1D(("histo_{0}_{1}".format(93,x), "histo_{0}_{1}".format(93,x),20,30, 230), "PuppiMET_pt{0}".format(altMass),"weight")
        histo[94][x] = dfwwvbscat[x].Filter("mll{0} < 140 && ltype == 0    ".format(altMass)).Histo1D(("histo_{0}_{1}".format(94,x), "histo_{0}_{1}".format(94,x),24, 20, 140), "mll{0}".format(altMass),"weight")
        histo[95][x] = dfwwvbscat[x].Filter("mll{0} < 140 && ltype == 1    ".format(altMass)).Histo1D(("histo_{0}_{1}".format(95,x), "histo_{0}_{1}".format(95,x),24, 20, 140), "mll{0}".format(altMass),"weight")
        histo[96][x] = dfwwvbscat[x].Filter("mll{0} < 140 && ltype == 2    ".format(altMass)).Histo1D(("histo_{0}_{1}".format(96,x), "histo_{0}_{1}".format(96,x),24, 20, 140), "mll{0}".format(altMass),"weight")
        histo[97][x] = dfwwvbscat[x].Filter("mll{0} < 140 && ltype == 3    ".format(altMass)).Histo1D(("histo_{0}_{1}".format(97,x), "histo_{0}_{1}".format(97,x),24, 20, 140), "mll{0}".format(altMass),"weight")

        dfwwjjcat .append(dfwwcat[x] .Filter("PuppiMET_pt{0} > {1}".format(altMass,metCut), "PuppiMET_pt > cut").Filter(VBSQCDSEL, "dijet non-vbf selection"))
        dfwwbjjcat.append(dfwwbcat[x].Filter("PuppiMET_pt{0} > {1}".format(altMass,metCut), "PuppiMET_pt > cut").Filter(VBSQCDSEL, "dijet non-vbf selection"))
        histo[40][x] = dfwwjjcat[x] .Histo1D(("histo_{0}_{1}".format(40,x), "histo_{0}_{1}".format(40,x), 14,0.0,7), "vbs_detajj","weight")
        histo[41][x] = dfwwbjjcat[x].Histo1D(("histo_{0}_{1}".format(41,x), "histo_{0}_{1}".format(41,x), 14,0.0,7), "vbs_detajj","weight")
        histo[42][x] = dfwwjjcat[x] .Histo1D(("histo_{0}_{1}".format(42,x), "histo_{0}_{1}".format(42,x), 4,-0.5, 3.5), "ltype","weight")
        histo[43][x] = dfwwbjjcat[x].Histo1D(("histo_{0}_{1}".format(43,x), "histo_{0}_{1}".format(43,x), 4,-0.5, 3.5), "ltype","weight")
        histo[44][x] = dfwwjjcat[x] .Histo1D(("histo_{0}_{1}".format(44,x), "histo_{0}_{1}".format(44,x), 4, 1.5, 5.5), "ngood_jets","weight")
        histo[45][x] = dfwwbjjcat[x].Histo1D(("histo_{0}_{1}".format(45,x), "histo_{0}_{1}".format(45,x), 4, 1.5, 5.5), "ngood_jets","weight")
        histo[46][x] = dfwwjjcat[x] .Histo1D(("histo_{0}_{1}".format(46,x), "histo_{0}_{1}".format(46,x),25, 50, 300), "vbs_ptj1","weight")
        histo[47][x] = dfwwbjjcat[x].Histo1D(("histo_{0}_{1}".format(47,x), "histo_{0}_{1}".format(47,x),25, 50, 300), "vbs_ptj1","weight")
        histo[48][x] = dfwwjjcat[x] .Histo1D(("histo_{0}_{1}".format(48,x), "histo_{0}_{1}".format(48,x),25, 50, 300), "vbs_ptj2","weight")
        histo[49][x] = dfwwbjjcat[x].Histo1D(("histo_{0}_{1}".format(49,x), "histo_{0}_{1}".format(49,x),25, 50, 300), "vbs_ptj2","weight")
        histo[50][x] = dfwwjjcat[x] .Histo1D(("histo_{0}_{1}".format(50,x), "histo_{0}_{1}".format(50,x),20, 0, 4.8), "vbs_etaj1","weight")
        histo[51][x] = dfwwbjjcat[x].Histo1D(("histo_{0}_{1}".format(51,x), "histo_{0}_{1}".format(51,x),20, 0, 4.8), "vbs_etaj1","weight")
        histo[52][x] = dfwwjjcat[x] .Histo1D(("histo_{0}_{1}".format(52,x), "histo_{0}_{1}".format(52,x),20, 0, 4.8), "vbs_etaj2","weight")
        histo[53][x] = dfwwbjjcat[x].Histo1D(("histo_{0}_{1}".format(53,x), "histo_{0}_{1}".format(53,x),20, 0, 4.8), "vbs_etaj2","weight")

        if(doNtuples == True and x == theCat):
            outputFile = "ntupleSSWWAna_sample{0}_year{1}_job{2}.root".format(count,year,whichJob)
            dfwwvbscat[x].Snapshot("events", outputFile, branchList)

        histo[ 99][x] = dfwwvbscat[x].Histo1D(("histo_{0}_{1}".format( 99,x), "histo_{0}_{1}".format( 99,x),12,500,3500), "vbs_mjj","weight")
        histo[100][x] = dfwwvbscat[x].Histo1D(("histo_{0}_{1}".format(100,x), "histo_{0}_{1}".format(100,x),12,500,3500), "vbs_mjj","weight0")
        histo[101][x] = dfwwvbscat[x].Histo1D(("histo_{0}_{1}".format(101,x), "histo_{0}_{1}".format(101,x),12,500,3500), "vbs_mjj","weight1")
        histo[102][x] = dfwwvbscat[x].Histo1D(("histo_{0}_{1}".format(102,x), "histo_{0}_{1}".format(102,x),12,500,3500), "vbs_mjj","weight2")
        histo[103][x] = dfwwvbscat[x].Histo1D(("histo_{0}_{1}".format(103,x), "histo_{0}_{1}".format(103,x),12,500,3500), "vbs_mjj","weight3")
        histo[104][x] = dfwwvbscat[x].Histo1D(("histo_{0}_{1}".format(104,x), "histo_{0}_{1}".format(104,x),12,500,3500), "vbs_mjj","weight4")
        histo[105][x] = dfwwvbscat[x].Histo1D(("histo_{0}_{1}".format(105,x), "histo_{0}_{1}".format(105,x),12,500,3500), "vbs_mjj","weight5")
        histo[106][x] = dfwwvbscat[x].Histo1D(("histo_{0}_{1}".format(106,x), "histo_{0}_{1}".format(106,x),12,500,3500), "vbs_mjj","weight6")
        histo[107][x] = dfwwvbscat[x].Histo1D(("histo_{0}_{1}".format(107,x), "histo_{0}_{1}".format(107,x),12,500,3500), "vbs_mjj","weight7")
        histo[108][x] = dfwwvbscat[x].Histo1D(("histo_{0}_{1}".format(108,x), "histo_{0}_{1}".format(108,x),12,500,3500), "vbs_mjj","weightWSUnc0")
        histo[109][x] = dfwwvbscat[x].Histo1D(("histo_{0}_{1}".format(109,x), "histo_{0}_{1}".format(109,x),12,500,3500), "vbs_mjj","weightWSUnc1")

        x1Bins = array('d', [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])
        x2Bins = array('d', [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])
        if(makeDataCards >= 1):
            yBins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5])

            varSel = makeDataCards
            if(makeDataCards == 6):
                varSel = 20
            elif(makeDataCards == 7):
                varSel = 21
            elif(makeDataCards == 8):
                varSel = 22
            elif(makeDataCards == 9):
                varSel = 23
            elif(makeDataCards == 10):
                varSel = 24
            elif(makeDataCards == 11):
                varSel = 25
            elif(makeDataCards == 12):
                varSel = 31
            elif(makeDataCards == 13):
                varSel = 32
            elif(makeDataCards == 14):
                varSel = 33

            # Begin redefine MVAs
            dfwwvbscatJes00Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes00Up	   [x],tmva_helperType0,"Jes00Up")
            dfwwvbscatJes01Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes01Up	   [x],tmva_helperType0,"Jes01Up")
            dfwwvbscatJes02Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes02Up	   [x],tmva_helperType0,"Jes02Up")
            dfwwvbscatJes03Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes03Up	   [x],tmva_helperType0,"Jes03Up")
            dfwwvbscatJes04Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes04Up	   [x],tmva_helperType0,"Jes04Up")
            dfwwvbscatJes05Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes05Up	   [x],tmva_helperType0,"Jes05Up")
            dfwwvbscatJes06Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes06Up	   [x],tmva_helperType0,"Jes06Up")
            dfwwvbscatJes07Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes07Up	   [x],tmva_helperType0,"Jes07Up")
            dfwwvbscatJes08Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes08Up	   [x],tmva_helperType0,"Jes08Up")
            dfwwvbscatJes09Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes09Up	   [x],tmva_helperType0,"Jes09Up")
            dfwwvbscatJes10Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes10Up	   [x],tmva_helperType0,"Jes10Up")
            dfwwvbscatJes11Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes11Up	   [x],tmva_helperType0,"Jes11Up")
            dfwwvbscatJes12Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes12Up	   [x],tmva_helperType0,"Jes12Up")
            dfwwvbscatJes13Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes13Up	   [x],tmva_helperType0,"Jes13Up")
            dfwwvbscatJes14Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes14Up	   [x],tmva_helperType0,"Jes14Up")
            dfwwvbscatJes15Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes15Up	   [x],tmva_helperType0,"Jes15Up")
            dfwwvbscatJes16Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes16Up	   [x],tmva_helperType0,"Jes16Up")
            dfwwvbscatJes17Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes17Up	   [x],tmva_helperType0,"Jes17Up")
            dfwwvbscatJes18Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes18Up	   [x],tmva_helperType0,"Jes18Up")
            dfwwvbscatJes19Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes19Up	   [x],tmva_helperType0,"Jes19Up")
            dfwwvbscatJes20Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes20Up	   [x],tmva_helperType0,"Jes20Up")
            dfwwvbscatJes21Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes21Up	   [x],tmva_helperType0,"Jes21Up")
            dfwwvbscatJes22Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes22Up	   [x],tmva_helperType0,"Jes22Up")
            dfwwvbscatJes23Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes23Up	   [x],tmva_helperType0,"Jes23Up")
            dfwwvbscatJes24Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes24Up	   [x],tmva_helperType0,"Jes24Up")
            dfwwvbscatJes25Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes25Up	   [x],tmva_helperType0,"Jes25Up")
            dfwwvbscatJes26Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes26Up	   [x],tmva_helperType0,"Jes26Up")
            dfwwvbscatJes27Up	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJes27Up	   [x],tmva_helperType0,"Jes27Up")
            dfwwvbscatJerUp	   [x] = redefineVBSIncMVAVariables(dfwwvbscatJerUp	   [x],tmva_helperType0,"JerUp"  )

            dfwwbvbscatJes00Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes00Up	     [x],tmva_helperType0,"Jes00Up")
            dfwwbvbscatJes01Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes01Up	     [x],tmva_helperType0,"Jes01Up")
            dfwwbvbscatJes02Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes02Up	     [x],tmva_helperType0,"Jes02Up")
            dfwwbvbscatJes03Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes03Up	     [x],tmva_helperType0,"Jes03Up")
            dfwwbvbscatJes04Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes04Up	     [x],tmva_helperType0,"Jes04Up")
            dfwwbvbscatJes05Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes05Up	     [x],tmva_helperType0,"Jes05Up")
            dfwwbvbscatJes06Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes06Up	     [x],tmva_helperType0,"Jes06Up")
            dfwwbvbscatJes07Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes07Up	     [x],tmva_helperType0,"Jes07Up")
            dfwwbvbscatJes08Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes08Up	     [x],tmva_helperType0,"Jes08Up")
            dfwwbvbscatJes09Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes09Up	     [x],tmva_helperType0,"Jes09Up")
            dfwwbvbscatJes10Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes10Up	     [x],tmva_helperType0,"Jes10Up")
            dfwwbvbscatJes11Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes11Up	     [x],tmva_helperType0,"Jes11Up")
            dfwwbvbscatJes12Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes12Up	     [x],tmva_helperType0,"Jes12Up")
            dfwwbvbscatJes13Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes13Up	     [x],tmva_helperType0,"Jes13Up")
            dfwwbvbscatJes14Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes14Up	     [x],tmva_helperType0,"Jes14Up")
            dfwwbvbscatJes15Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes15Up	     [x],tmva_helperType0,"Jes15Up")
            dfwwbvbscatJes16Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes16Up	     [x],tmva_helperType0,"Jes16Up")
            dfwwbvbscatJes17Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes17Up	     [x],tmva_helperType0,"Jes17Up")
            dfwwbvbscatJes18Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes18Up	     [x],tmva_helperType0,"Jes18Up")
            dfwwbvbscatJes19Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes19Up	     [x],tmva_helperType0,"Jes19Up")
            dfwwbvbscatJes20Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes20Up	     [x],tmva_helperType0,"Jes20Up")
            dfwwbvbscatJes21Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes21Up	     [x],tmva_helperType0,"Jes21Up")
            dfwwbvbscatJes22Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes22Up	     [x],tmva_helperType0,"Jes22Up")
            dfwwbvbscatJes23Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes23Up	     [x],tmva_helperType0,"Jes23Up")
            dfwwbvbscatJes24Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes24Up	     [x],tmva_helperType0,"Jes24Up")
            dfwwbvbscatJes25Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes25Up	     [x],tmva_helperType0,"Jes25Up")
            dfwwbvbscatJes26Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes26Up	     [x],tmva_helperType0,"Jes26Up")
            dfwwbvbscatJes27Up	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJes27Up	     [x],tmva_helperType0,"Jes27Up")
            dfwwbvbscatJerUp	    [x] = redefineVBSIncMVAVariables(dfwwbvbscatJerUp	     [x],tmva_helperType0,"JerUp"  )

            dfwwvbscatJes00Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes00Up	   [x],tmva_helperType1,tmva_helperType2,"Jes00Up",altMass,altMass)
            dfwwvbscatJes01Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes01Up	   [x],tmva_helperType1,tmva_helperType2,"Jes01Up",altMass,altMass)
            dfwwvbscatJes02Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes02Up	   [x],tmva_helperType1,tmva_helperType2,"Jes02Up",altMass,altMass)
            dfwwvbscatJes03Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes03Up	   [x],tmva_helperType1,tmva_helperType2,"Jes03Up",altMass,altMass)
            dfwwvbscatJes04Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes04Up	   [x],tmva_helperType1,tmva_helperType2,"Jes04Up",altMass,altMass)
            dfwwvbscatJes05Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes05Up	   [x],tmva_helperType1,tmva_helperType2,"Jes05Up",altMass,altMass)
            dfwwvbscatJes06Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes06Up	   [x],tmva_helperType1,tmva_helperType2,"Jes06Up",altMass,altMass)
            dfwwvbscatJes07Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes07Up	   [x],tmva_helperType1,tmva_helperType2,"Jes07Up",altMass,altMass)
            dfwwvbscatJes08Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes08Up	   [x],tmva_helperType1,tmva_helperType2,"Jes08Up",altMass,altMass)
            dfwwvbscatJes09Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes09Up	   [x],tmva_helperType1,tmva_helperType2,"Jes09Up",altMass,altMass)
            dfwwvbscatJes10Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes10Up	   [x],tmva_helperType1,tmva_helperType2,"Jes10Up",altMass,altMass)
            dfwwvbscatJes11Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes11Up	   [x],tmva_helperType1,tmva_helperType2,"Jes11Up",altMass,altMass)
            dfwwvbscatJes12Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes12Up	   [x],tmva_helperType1,tmva_helperType2,"Jes12Up",altMass,altMass)
            dfwwvbscatJes13Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes13Up	   [x],tmva_helperType1,tmva_helperType2,"Jes13Up",altMass,altMass)
            dfwwvbscatJes14Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes14Up	   [x],tmva_helperType1,tmva_helperType2,"Jes14Up",altMass,altMass)
            dfwwvbscatJes15Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes15Up	   [x],tmva_helperType1,tmva_helperType2,"Jes15Up",altMass,altMass)
            dfwwvbscatJes16Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes16Up	   [x],tmva_helperType1,tmva_helperType2,"Jes16Up",altMass,altMass)
            dfwwvbscatJes17Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes17Up	   [x],tmva_helperType1,tmva_helperType2,"Jes17Up",altMass,altMass)
            dfwwvbscatJes18Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes18Up	   [x],tmva_helperType1,tmva_helperType2,"Jes18Up",altMass,altMass)
            dfwwvbscatJes19Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes19Up	   [x],tmva_helperType1,tmva_helperType2,"Jes19Up",altMass,altMass)
            dfwwvbscatJes20Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes20Up	   [x],tmva_helperType1,tmva_helperType2,"Jes20Up",altMass,altMass)
            dfwwvbscatJes21Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes21Up	   [x],tmva_helperType1,tmva_helperType2,"Jes21Up",altMass,altMass)
            dfwwvbscatJes22Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes22Up	   [x],tmva_helperType1,tmva_helperType2,"Jes22Up",altMass,altMass)
            dfwwvbscatJes23Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes23Up	   [x],tmva_helperType1,tmva_helperType2,"Jes23Up",altMass,altMass)
            dfwwvbscatJes24Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes24Up	   [x],tmva_helperType1,tmva_helperType2,"Jes24Up",altMass,altMass)
            dfwwvbscatJes25Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes25Up	   [x],tmva_helperType1,tmva_helperType2,"Jes25Up",altMass,altMass)
            dfwwvbscatJes26Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes26Up	   [x],tmva_helperType1,tmva_helperType2,"Jes26Up",altMass,altMass)
            dfwwvbscatJes27Up	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJes27Up	   [x],tmva_helperType1,tmva_helperType2,"Jes27Up",altMass,altMass)
            dfwwvbscatJerUp	   [x] = redefineVBSPolMVAVariables(dfwwvbscatJerUp	   [x],tmva_helperType1,tmva_helperType2,"JerUp"  ,altMass,altMass)

            dfwwbvbscatJes00Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes00Up	     [x],tmva_helperType1,tmva_helperType2,"Jes00Up",altMass,altMass)
            dfwwbvbscatJes01Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes01Up	     [x],tmva_helperType1,tmva_helperType2,"Jes01Up",altMass,altMass)
            dfwwbvbscatJes02Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes02Up	     [x],tmva_helperType1,tmva_helperType2,"Jes02Up",altMass,altMass)
            dfwwbvbscatJes03Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes03Up	     [x],tmva_helperType1,tmva_helperType2,"Jes03Up",altMass,altMass)
            dfwwbvbscatJes04Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes04Up	     [x],tmva_helperType1,tmva_helperType2,"Jes04Up",altMass,altMass)
            dfwwbvbscatJes05Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes05Up	     [x],tmva_helperType1,tmva_helperType2,"Jes05Up",altMass,altMass)
            dfwwbvbscatJes06Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes06Up	     [x],tmva_helperType1,tmva_helperType2,"Jes06Up",altMass,altMass)
            dfwwbvbscatJes07Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes07Up	     [x],tmva_helperType1,tmva_helperType2,"Jes07Up",altMass,altMass)
            dfwwbvbscatJes08Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes08Up	     [x],tmva_helperType1,tmva_helperType2,"Jes08Up",altMass,altMass)
            dfwwbvbscatJes09Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes09Up	     [x],tmva_helperType1,tmva_helperType2,"Jes09Up",altMass,altMass)
            dfwwbvbscatJes10Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes10Up	     [x],tmva_helperType1,tmva_helperType2,"Jes10Up",altMass,altMass)
            dfwwbvbscatJes11Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes11Up	     [x],tmva_helperType1,tmva_helperType2,"Jes11Up",altMass,altMass)
            dfwwbvbscatJes12Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes12Up	     [x],tmva_helperType1,tmva_helperType2,"Jes12Up",altMass,altMass)
            dfwwbvbscatJes13Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes13Up	     [x],tmva_helperType1,tmva_helperType2,"Jes13Up",altMass,altMass)
            dfwwbvbscatJes14Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes14Up	     [x],tmva_helperType1,tmva_helperType2,"Jes14Up",altMass,altMass)
            dfwwbvbscatJes15Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes15Up	     [x],tmva_helperType1,tmva_helperType2,"Jes15Up",altMass,altMass)
            dfwwbvbscatJes16Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes16Up	     [x],tmva_helperType1,tmva_helperType2,"Jes16Up",altMass,altMass)
            dfwwbvbscatJes17Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes17Up	     [x],tmva_helperType1,tmva_helperType2,"Jes17Up",altMass,altMass)
            dfwwbvbscatJes18Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes18Up	     [x],tmva_helperType1,tmva_helperType2,"Jes18Up",altMass,altMass)
            dfwwbvbscatJes19Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes19Up	     [x],tmva_helperType1,tmva_helperType2,"Jes19Up",altMass,altMass)
            dfwwbvbscatJes20Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes20Up	     [x],tmva_helperType1,tmva_helperType2,"Jes20Up",altMass,altMass)
            dfwwbvbscatJes21Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes21Up	     [x],tmva_helperType1,tmva_helperType2,"Jes21Up",altMass,altMass)
            dfwwbvbscatJes22Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes22Up	     [x],tmva_helperType1,tmva_helperType2,"Jes22Up",altMass,altMass)
            dfwwbvbscatJes23Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes23Up	     [x],tmva_helperType1,tmva_helperType2,"Jes23Up",altMass,altMass)
            dfwwbvbscatJes24Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes24Up	     [x],tmva_helperType1,tmva_helperType2,"Jes24Up",altMass,altMass)
            dfwwbvbscatJes25Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes25Up	     [x],tmva_helperType1,tmva_helperType2,"Jes25Up",altMass,altMass)
            dfwwbvbscatJes26Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes26Up	     [x],tmva_helperType1,tmva_helperType2,"Jes26Up",altMass,altMass)
            dfwwbvbscatJes27Up	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJes27Up	     [x],tmva_helperType1,tmva_helperType2,"Jes27Up",altMass,altMass)
            dfwwbvbscatJerUp	    [x] = redefineVBSPolMVAVariables(dfwwbvbscatJerUp	     [x],tmva_helperType1,tmva_helperType2,"JerUp"  ,altMass,altMass)
            # End redefine MVAs

            dfwwvbscat             [x] = dfwwvbscat             [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mll{0},ngood_jets,{1},bdt_vbfpol0[0],bdt_vbfpol1[0])".format(altMass,varSel))
            dfwwvbscatMuonMomUp    [x] = dfwwvbscatMuonMomUp    [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mllMuonMomUp,ngood_jets,{1},bdt_vbfpol0[0],bdt_vbfpol1[0])".format(altMass,varSel))
            dfwwvbscatElectronMomUp[x] = dfwwvbscatElectronMomUp[x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mllElectronMomUp,ngood_jets,{1},bdt_vbfpol0[0],bdt_vbfpol1[0])".format(altMass,varSel))
            dfwwvbscatJes00Up      [x] = dfwwvbscatJes00Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes00Up,vbs_detajjJes00Up,vbs_dphijjJes00Up,vbs_zepvvJes00Up,bdt_vbfincJes00Up[0],mll{0},ngood_jetsJes00Up,{1},bdt_vbfpol0Jes00Up[0],bdt_vbfpol1Jes00Up[0])".format(altMass,varSel))
            dfwwvbscatJes01Up      [x] = dfwwvbscatJes01Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes01Up,vbs_detajjJes01Up,vbs_dphijjJes01Up,vbs_zepvvJes01Up,bdt_vbfincJes01Up[0],mll{0},ngood_jetsJes01Up,{1},bdt_vbfpol0Jes01Up[0],bdt_vbfpol1Jes01Up[0])".format(altMass,varSel))
            dfwwvbscatJes02Up      [x] = dfwwvbscatJes02Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes02Up,vbs_detajjJes02Up,vbs_dphijjJes02Up,vbs_zepvvJes02Up,bdt_vbfincJes02Up[0],mll{0},ngood_jetsJes02Up,{1},bdt_vbfpol0Jes02Up[0],bdt_vbfpol1Jes02Up[0])".format(altMass,varSel))
            dfwwvbscatJes03Up      [x] = dfwwvbscatJes03Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes03Up,vbs_detajjJes03Up,vbs_dphijjJes03Up,vbs_zepvvJes03Up,bdt_vbfincJes03Up[0],mll{0},ngood_jetsJes03Up,{1},bdt_vbfpol0Jes03Up[0],bdt_vbfpol1Jes03Up[0])".format(altMass,varSel))
            dfwwvbscatJes04Up      [x] = dfwwvbscatJes04Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes04Up,vbs_detajjJes04Up,vbs_dphijjJes04Up,vbs_zepvvJes04Up,bdt_vbfincJes04Up[0],mll{0},ngood_jetsJes04Up,{1},bdt_vbfpol0Jes04Up[0],bdt_vbfpol1Jes04Up[0])".format(altMass,varSel))
            dfwwvbscatJes05Up      [x] = dfwwvbscatJes05Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes05Up,vbs_detajjJes05Up,vbs_dphijjJes05Up,vbs_zepvvJes05Up,bdt_vbfincJes05Up[0],mll{0},ngood_jetsJes05Up,{1},bdt_vbfpol0Jes05Up[0],bdt_vbfpol1Jes05Up[0])".format(altMass,varSel))
            dfwwvbscatJes06Up      [x] = dfwwvbscatJes06Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes06Up,vbs_detajjJes06Up,vbs_dphijjJes06Up,vbs_zepvvJes06Up,bdt_vbfincJes06Up[0],mll{0},ngood_jetsJes06Up,{1},bdt_vbfpol0Jes06Up[0],bdt_vbfpol1Jes06Up[0])".format(altMass,varSel))
            dfwwvbscatJes07Up      [x] = dfwwvbscatJes07Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes07Up,vbs_detajjJes07Up,vbs_dphijjJes07Up,vbs_zepvvJes07Up,bdt_vbfincJes07Up[0],mll{0},ngood_jetsJes07Up,{1},bdt_vbfpol0Jes07Up[0],bdt_vbfpol1Jes07Up[0])".format(altMass,varSel))
            dfwwvbscatJes08Up      [x] = dfwwvbscatJes08Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes08Up,vbs_detajjJes08Up,vbs_dphijjJes08Up,vbs_zepvvJes08Up,bdt_vbfincJes08Up[0],mll{0},ngood_jetsJes08Up,{1},bdt_vbfpol0Jes08Up[0],bdt_vbfpol1Jes08Up[0])".format(altMass,varSel))
            dfwwvbscatJes09Up      [x] = dfwwvbscatJes09Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes09Up,vbs_detajjJes09Up,vbs_dphijjJes09Up,vbs_zepvvJes09Up,bdt_vbfincJes09Up[0],mll{0},ngood_jetsJes09Up,{1},bdt_vbfpol0Jes09Up[0],bdt_vbfpol1Jes09Up[0])".format(altMass,varSel))
            dfwwvbscatJes10Up      [x] = dfwwvbscatJes10Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes10Up,vbs_detajjJes10Up,vbs_dphijjJes10Up,vbs_zepvvJes10Up,bdt_vbfincJes10Up[0],mll{0},ngood_jetsJes10Up,{1},bdt_vbfpol0Jes10Up[0],bdt_vbfpol1Jes10Up[0])".format(altMass,varSel))
            dfwwvbscatJes11Up      [x] = dfwwvbscatJes11Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes11Up,vbs_detajjJes11Up,vbs_dphijjJes11Up,vbs_zepvvJes11Up,bdt_vbfincJes11Up[0],mll{0},ngood_jetsJes11Up,{1},bdt_vbfpol0Jes11Up[0],bdt_vbfpol1Jes11Up[0])".format(altMass,varSel))
            dfwwvbscatJes12Up      [x] = dfwwvbscatJes12Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes12Up,vbs_detajjJes12Up,vbs_dphijjJes12Up,vbs_zepvvJes12Up,bdt_vbfincJes12Up[0],mll{0},ngood_jetsJes12Up,{1},bdt_vbfpol0Jes12Up[0],bdt_vbfpol1Jes12Up[0])".format(altMass,varSel))
            dfwwvbscatJes13Up      [x] = dfwwvbscatJes13Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes13Up,vbs_detajjJes13Up,vbs_dphijjJes13Up,vbs_zepvvJes13Up,bdt_vbfincJes13Up[0],mll{0},ngood_jetsJes13Up,{1},bdt_vbfpol0Jes13Up[0],bdt_vbfpol1Jes13Up[0])".format(altMass,varSel))
            dfwwvbscatJes14Up      [x] = dfwwvbscatJes14Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes14Up,vbs_detajjJes14Up,vbs_dphijjJes14Up,vbs_zepvvJes14Up,bdt_vbfincJes14Up[0],mll{0},ngood_jetsJes14Up,{1},bdt_vbfpol0Jes14Up[0],bdt_vbfpol1Jes14Up[0])".format(altMass,varSel))
            dfwwvbscatJes15Up      [x] = dfwwvbscatJes15Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes15Up,vbs_detajjJes15Up,vbs_dphijjJes15Up,vbs_zepvvJes15Up,bdt_vbfincJes15Up[0],mll{0},ngood_jetsJes15Up,{1},bdt_vbfpol0Jes15Up[0],bdt_vbfpol1Jes15Up[0])".format(altMass,varSel))
            dfwwvbscatJes16Up      [x] = dfwwvbscatJes16Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes16Up,vbs_detajjJes16Up,vbs_dphijjJes16Up,vbs_zepvvJes16Up,bdt_vbfincJes16Up[0],mll{0},ngood_jetsJes16Up,{1},bdt_vbfpol0Jes16Up[0],bdt_vbfpol1Jes16Up[0])".format(altMass,varSel))
            dfwwvbscatJes17Up      [x] = dfwwvbscatJes17Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes17Up,vbs_detajjJes17Up,vbs_dphijjJes17Up,vbs_zepvvJes17Up,bdt_vbfincJes17Up[0],mll{0},ngood_jetsJes17Up,{1},bdt_vbfpol0Jes17Up[0],bdt_vbfpol1Jes17Up[0])".format(altMass,varSel))
            dfwwvbscatJes18Up      [x] = dfwwvbscatJes18Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes18Up,vbs_detajjJes18Up,vbs_dphijjJes18Up,vbs_zepvvJes18Up,bdt_vbfincJes18Up[0],mll{0},ngood_jetsJes18Up,{1},bdt_vbfpol0Jes18Up[0],bdt_vbfpol1Jes18Up[0])".format(altMass,varSel))
            dfwwvbscatJes19Up      [x] = dfwwvbscatJes19Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes19Up,vbs_detajjJes19Up,vbs_dphijjJes19Up,vbs_zepvvJes19Up,bdt_vbfincJes19Up[0],mll{0},ngood_jetsJes19Up,{1},bdt_vbfpol0Jes19Up[0],bdt_vbfpol1Jes19Up[0])".format(altMass,varSel))
            dfwwvbscatJes20Up      [x] = dfwwvbscatJes20Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes20Up,vbs_detajjJes20Up,vbs_dphijjJes20Up,vbs_zepvvJes20Up,bdt_vbfincJes20Up[0],mll{0},ngood_jetsJes20Up,{1},bdt_vbfpol0Jes20Up[0],bdt_vbfpol1Jes20Up[0])".format(altMass,varSel))
            dfwwvbscatJes21Up      [x] = dfwwvbscatJes21Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes21Up,vbs_detajjJes21Up,vbs_dphijjJes21Up,vbs_zepvvJes21Up,bdt_vbfincJes21Up[0],mll{0},ngood_jetsJes21Up,{1},bdt_vbfpol0Jes21Up[0],bdt_vbfpol1Jes21Up[0])".format(altMass,varSel))
            dfwwvbscatJes22Up      [x] = dfwwvbscatJes22Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes22Up,vbs_detajjJes22Up,vbs_dphijjJes22Up,vbs_zepvvJes22Up,bdt_vbfincJes22Up[0],mll{0},ngood_jetsJes22Up,{1},bdt_vbfpol0Jes22Up[0],bdt_vbfpol1Jes22Up[0])".format(altMass,varSel))
            dfwwvbscatJes23Up      [x] = dfwwvbscatJes23Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes23Up,vbs_detajjJes23Up,vbs_dphijjJes23Up,vbs_zepvvJes23Up,bdt_vbfincJes23Up[0],mll{0},ngood_jetsJes23Up,{1},bdt_vbfpol0Jes23Up[0],bdt_vbfpol1Jes23Up[0])".format(altMass,varSel))
            dfwwvbscatJes24Up      [x] = dfwwvbscatJes24Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes24Up,vbs_detajjJes24Up,vbs_dphijjJes24Up,vbs_zepvvJes24Up,bdt_vbfincJes24Up[0],mll{0},ngood_jetsJes24Up,{1},bdt_vbfpol0Jes24Up[0],bdt_vbfpol1Jes24Up[0])".format(altMass,varSel))
            dfwwvbscatJes25Up      [x] = dfwwvbscatJes25Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes25Up,vbs_detajjJes25Up,vbs_dphijjJes25Up,vbs_zepvvJes25Up,bdt_vbfincJes25Up[0],mll{0},ngood_jetsJes25Up,{1},bdt_vbfpol0Jes25Up[0],bdt_vbfpol1Jes25Up[0])".format(altMass,varSel))
            dfwwvbscatJes26Up      [x] = dfwwvbscatJes26Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes26Up,vbs_detajjJes26Up,vbs_dphijjJes26Up,vbs_zepvvJes26Up,bdt_vbfincJes26Up[0],mll{0},ngood_jetsJes26Up,{1},bdt_vbfpol0Jes26Up[0],bdt_vbfpol1Jes26Up[0])".format(altMass,varSel))
            dfwwvbscatJes27Up      [x] = dfwwvbscatJes27Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes27Up,vbs_detajjJes27Up,vbs_dphijjJes27Up,vbs_zepvvJes27Up,bdt_vbfincJes27Up[0],mll{0},ngood_jetsJes27Up,{1},bdt_vbfpol0Jes27Up[0],bdt_vbfpol1Jes27Up[0])".format(altMass,varSel))
            dfwwvbscatJerUp        [x] = dfwwvbscatJerUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJerUp  ,vbs_detajjJerUp  ,vbs_dphijjJerUp  ,vbs_zepvvJerUp  ,bdt_vbfincJerUp  [0],mll{0},ngood_jetsJerUp  ,{1},bdt_vbfpol0JerUp  [0],bdt_vbfpol1JerUp  [0])".format(altMass,varSel))
            dfwwvbscatJERUp        [x] = dfwwvbscatJERUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj       ,vbs_zepvv	,bdt_vbfinc	  [0],mll{0},ngood_jets       ,{1},bdt_vbfpol0       [0],bdt_vbfpol1	   [0])".format(altMass,varSel))
            dfwwvbscatJESUp        [x] = dfwwvbscatJESUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj       ,vbs_zepvv	,bdt_vbfinc	  [0],mll{0},ngood_jets       ,{1},bdt_vbfpol0	     [0],bdt_vbfpol1	   [0])".format(altMass,varSel))
            dfwwvbscatUnclusteredUp[x] = dfwwvbscatUnclusteredUp[x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj       ,vbs_zepvv	,bdt_vbfinc	  [0],mll{0},ngood_jets       ,{1},bdt_vbfpol0	     [0],bdt_vbfpol1	   [0])".format(altMass,varSel))

            varSel = 9
            if(makeDataCards == 6):
                varSel = 20
            elif(makeDataCards == 7):
                varSel = 21
            elif(makeDataCards == 8):
                varSel = 22
            elif(makeDataCards == 9):
                varSel = 23
            elif(makeDataCards == 10):
                varSel = 24
            elif(makeDataCards == 11):
                varSel = 25
            elif(makeDataCards == 12):
                varSel = 31
                varSel = 9
            elif(makeDataCards == 13):
                varSel = 32
                varSel = 9
            elif(makeDataCards == 14):
                varSel = 33
                varSel = 9
            dfwwbvbscat             [x] = dfwwbvbscat             [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mll{0},ngood_jets,{1},bdt_vbfpol0[0],bdt_vbfpol1[0])".format(altMass,varSel))
            dfwwbvbscatMuonMomUp    [x] = dfwwbvbscatMuonMomUp    [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mllMuonMomUp,ngood_jets,{1},bdt_vbfpol0[0],bdt_vbfpol1[0])".format(altMass,varSel))
            dfwwbvbscatElectronMomUp[x] = dfwwbvbscatElectronMomUp[x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj,vbs_detajj,vbs_dphijj,vbs_zepvv,bdt_vbfinc[0],mllElectronMomUp,ngood_jets,{1},bdt_vbfpol0[0],bdt_vbfpol1[0])".format(altMass,varSel))
            dfwwbvbscatJes00Up      [x] = dfwwbvbscatJes00Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes00Up,vbs_detajjJes00Up,vbs_dphijjJes00Up,vbs_zepvvJes00Up,bdt_vbfincJes00Up[0],mll{0},ngood_jetsJes00Up,{1},bdt_vbfpol0Jes00Up[0],bdt_vbfpol1Jes00Up[0])".format(altMass,varSel))
            dfwwbvbscatJes01Up      [x] = dfwwbvbscatJes01Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes01Up,vbs_detajjJes01Up,vbs_dphijjJes01Up,vbs_zepvvJes01Up,bdt_vbfincJes01Up[0],mll{0},ngood_jetsJes01Up,{1},bdt_vbfpol0Jes01Up[0],bdt_vbfpol1Jes01Up[0])".format(altMass,varSel))
            dfwwbvbscatJes02Up      [x] = dfwwbvbscatJes02Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes02Up,vbs_detajjJes02Up,vbs_dphijjJes02Up,vbs_zepvvJes02Up,bdt_vbfincJes02Up[0],mll{0},ngood_jetsJes02Up,{1},bdt_vbfpol0Jes02Up[0],bdt_vbfpol1Jes02Up[0])".format(altMass,varSel))
            dfwwbvbscatJes03Up      [x] = dfwwbvbscatJes03Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes03Up,vbs_detajjJes03Up,vbs_dphijjJes03Up,vbs_zepvvJes03Up,bdt_vbfincJes03Up[0],mll{0},ngood_jetsJes03Up,{1},bdt_vbfpol0Jes03Up[0],bdt_vbfpol1Jes03Up[0])".format(altMass,varSel))
            dfwwbvbscatJes04Up      [x] = dfwwbvbscatJes04Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes04Up,vbs_detajjJes04Up,vbs_dphijjJes04Up,vbs_zepvvJes04Up,bdt_vbfincJes04Up[0],mll{0},ngood_jetsJes04Up,{1},bdt_vbfpol0Jes04Up[0],bdt_vbfpol1Jes04Up[0])".format(altMass,varSel))
            dfwwbvbscatJes05Up      [x] = dfwwbvbscatJes05Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes05Up,vbs_detajjJes05Up,vbs_dphijjJes05Up,vbs_zepvvJes05Up,bdt_vbfincJes05Up[0],mll{0},ngood_jetsJes05Up,{1},bdt_vbfpol0Jes05Up[0],bdt_vbfpol1Jes05Up[0])".format(altMass,varSel))
            dfwwbvbscatJes06Up      [x] = dfwwbvbscatJes06Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes06Up,vbs_detajjJes06Up,vbs_dphijjJes06Up,vbs_zepvvJes06Up,bdt_vbfincJes06Up[0],mll{0},ngood_jetsJes06Up,{1},bdt_vbfpol0Jes06Up[0],bdt_vbfpol1Jes06Up[0])".format(altMass,varSel))
            dfwwbvbscatJes07Up      [x] = dfwwbvbscatJes07Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes07Up,vbs_detajjJes07Up,vbs_dphijjJes07Up,vbs_zepvvJes07Up,bdt_vbfincJes07Up[0],mll{0},ngood_jetsJes07Up,{1},bdt_vbfpol0Jes07Up[0],bdt_vbfpol1Jes07Up[0])".format(altMass,varSel))
            dfwwbvbscatJes08Up      [x] = dfwwbvbscatJes08Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes08Up,vbs_detajjJes08Up,vbs_dphijjJes08Up,vbs_zepvvJes08Up,bdt_vbfincJes08Up[0],mll{0},ngood_jetsJes08Up,{1},bdt_vbfpol0Jes08Up[0],bdt_vbfpol1Jes08Up[0])".format(altMass,varSel))
            dfwwbvbscatJes09Up      [x] = dfwwbvbscatJes09Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes09Up,vbs_detajjJes09Up,vbs_dphijjJes09Up,vbs_zepvvJes09Up,bdt_vbfincJes09Up[0],mll{0},ngood_jetsJes09Up,{1},bdt_vbfpol0Jes09Up[0],bdt_vbfpol1Jes09Up[0])".format(altMass,varSel))
            dfwwbvbscatJes10Up      [x] = dfwwbvbscatJes10Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes10Up,vbs_detajjJes10Up,vbs_dphijjJes10Up,vbs_zepvvJes10Up,bdt_vbfincJes10Up[0],mll{0},ngood_jetsJes10Up,{1},bdt_vbfpol0Jes10Up[0],bdt_vbfpol1Jes10Up[0])".format(altMass,varSel))
            dfwwbvbscatJes11Up      [x] = dfwwbvbscatJes11Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes11Up,vbs_detajjJes11Up,vbs_dphijjJes11Up,vbs_zepvvJes11Up,bdt_vbfincJes11Up[0],mll{0},ngood_jetsJes11Up,{1},bdt_vbfpol0Jes11Up[0],bdt_vbfpol1Jes11Up[0])".format(altMass,varSel))
            dfwwbvbscatJes12Up      [x] = dfwwbvbscatJes12Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes12Up,vbs_detajjJes12Up,vbs_dphijjJes12Up,vbs_zepvvJes12Up,bdt_vbfincJes12Up[0],mll{0},ngood_jetsJes12Up,{1},bdt_vbfpol0Jes12Up[0],bdt_vbfpol1Jes12Up[0])".format(altMass,varSel))
            dfwwbvbscatJes13Up      [x] = dfwwbvbscatJes13Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes13Up,vbs_detajjJes13Up,vbs_dphijjJes13Up,vbs_zepvvJes13Up,bdt_vbfincJes13Up[0],mll{0},ngood_jetsJes13Up,{1},bdt_vbfpol0Jes13Up[0],bdt_vbfpol1Jes13Up[0])".format(altMass,varSel))
            dfwwbvbscatJes14Up      [x] = dfwwbvbscatJes14Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes14Up,vbs_detajjJes14Up,vbs_dphijjJes14Up,vbs_zepvvJes14Up,bdt_vbfincJes14Up[0],mll{0},ngood_jetsJes14Up,{1},bdt_vbfpol0Jes14Up[0],bdt_vbfpol1Jes14Up[0])".format(altMass,varSel))
            dfwwbvbscatJes15Up      [x] = dfwwbvbscatJes15Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes15Up,vbs_detajjJes15Up,vbs_dphijjJes15Up,vbs_zepvvJes15Up,bdt_vbfincJes15Up[0],mll{0},ngood_jetsJes15Up,{1},bdt_vbfpol0Jes15Up[0],bdt_vbfpol1Jes15Up[0])".format(altMass,varSel))
            dfwwbvbscatJes16Up      [x] = dfwwbvbscatJes16Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes16Up,vbs_detajjJes16Up,vbs_dphijjJes16Up,vbs_zepvvJes16Up,bdt_vbfincJes16Up[0],mll{0},ngood_jetsJes16Up,{1},bdt_vbfpol0Jes16Up[0],bdt_vbfpol1Jes16Up[0])".format(altMass,varSel))
            dfwwbvbscatJes17Up      [x] = dfwwbvbscatJes17Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes17Up,vbs_detajjJes17Up,vbs_dphijjJes17Up,vbs_zepvvJes17Up,bdt_vbfincJes17Up[0],mll{0},ngood_jetsJes17Up,{1},bdt_vbfpol0Jes17Up[0],bdt_vbfpol1Jes17Up[0])".format(altMass,varSel))
            dfwwbvbscatJes18Up      [x] = dfwwbvbscatJes18Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes18Up,vbs_detajjJes18Up,vbs_dphijjJes18Up,vbs_zepvvJes18Up,bdt_vbfincJes18Up[0],mll{0},ngood_jetsJes18Up,{1},bdt_vbfpol0Jes18Up[0],bdt_vbfpol1Jes18Up[0])".format(altMass,varSel))
            dfwwbvbscatJes19Up      [x] = dfwwbvbscatJes19Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes19Up,vbs_detajjJes19Up,vbs_dphijjJes19Up,vbs_zepvvJes19Up,bdt_vbfincJes19Up[0],mll{0},ngood_jetsJes19Up,{1},bdt_vbfpol0Jes19Up[0],bdt_vbfpol1Jes19Up[0])".format(altMass,varSel))
            dfwwbvbscatJes20Up      [x] = dfwwbvbscatJes20Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes20Up,vbs_detajjJes20Up,vbs_dphijjJes20Up,vbs_zepvvJes20Up,bdt_vbfincJes20Up[0],mll{0},ngood_jetsJes20Up,{1},bdt_vbfpol0Jes20Up[0],bdt_vbfpol1Jes20Up[0])".format(altMass,varSel))
            dfwwbvbscatJes21Up      [x] = dfwwbvbscatJes21Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes21Up,vbs_detajjJes21Up,vbs_dphijjJes21Up,vbs_zepvvJes21Up,bdt_vbfincJes21Up[0],mll{0},ngood_jetsJes21Up,{1},bdt_vbfpol0Jes21Up[0],bdt_vbfpol1Jes21Up[0])".format(altMass,varSel))
            dfwwbvbscatJes22Up      [x] = dfwwbvbscatJes22Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes22Up,vbs_detajjJes22Up,vbs_dphijjJes22Up,vbs_zepvvJes22Up,bdt_vbfincJes22Up[0],mll{0},ngood_jetsJes22Up,{1},bdt_vbfpol0Jes22Up[0],bdt_vbfpol1Jes22Up[0])".format(altMass,varSel))
            dfwwbvbscatJes23Up      [x] = dfwwbvbscatJes23Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes23Up,vbs_detajjJes23Up,vbs_dphijjJes23Up,vbs_zepvvJes23Up,bdt_vbfincJes23Up[0],mll{0},ngood_jetsJes23Up,{1},bdt_vbfpol0Jes23Up[0],bdt_vbfpol1Jes23Up[0])".format(altMass,varSel))
            dfwwbvbscatJes24Up      [x] = dfwwbvbscatJes24Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes24Up,vbs_detajjJes24Up,vbs_dphijjJes24Up,vbs_zepvvJes24Up,bdt_vbfincJes24Up[0],mll{0},ngood_jetsJes24Up,{1},bdt_vbfpol0Jes24Up[0],bdt_vbfpol1Jes24Up[0])".format(altMass,varSel))
            dfwwbvbscatJes25Up      [x] = dfwwbvbscatJes25Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes25Up,vbs_detajjJes25Up,vbs_dphijjJes25Up,vbs_zepvvJes25Up,bdt_vbfincJes25Up[0],mll{0},ngood_jetsJes25Up,{1},bdt_vbfpol0Jes25Up[0],bdt_vbfpol1Jes25Up[0])".format(altMass,varSel))
            dfwwbvbscatJes26Up      [x] = dfwwbvbscatJes26Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes26Up,vbs_detajjJes26Up,vbs_dphijjJes26Up,vbs_zepvvJes26Up,bdt_vbfincJes26Up[0],mll{0},ngood_jetsJes26Up,{1},bdt_vbfpol0Jes26Up[0],bdt_vbfpol1Jes26Up[0])".format(altMass,varSel))
            dfwwbvbscatJes27Up      [x] = dfwwbvbscatJes27Up      [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJes27Up,vbs_detajjJes27Up,vbs_dphijjJes27Up,vbs_zepvvJes27Up,bdt_vbfincJes27Up[0],mll{0},ngood_jetsJes27Up,{1},bdt_vbfpol0Jes27Up[0],bdt_vbfpol1Jes27Up[0])".format(altMass,varSel))
            dfwwbvbscatJerUp        [x] = dfwwbvbscatJerUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjjJerUp  ,vbs_detajjJerUp  ,vbs_dphijjJerUp  ,vbs_zepvvJerUp  ,bdt_vbfincJerUp  [0],mll{0},ngood_jetsJerUp  ,{1},bdt_vbfpol0JerUp  [0],bdt_vbfpol1JerUp  [0])".format(altMass,varSel))
            dfwwbvbscatJERUp        [x] = dfwwbvbscatJERUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj       ,vbs_zepvv	  ,bdt_vbfinc	    [0],mll{0},ngood_jets	,{1},bdt_vbfpol0       [0],bdt_vbfpol1       [0])".format(altMass,varSel))
            dfwwbvbscatJESUp        [x] = dfwwbvbscatJESUp        [x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj       ,vbs_zepvv	  ,bdt_vbfinc	    [0],mll{0},ngood_jets	,{1},bdt_vbfpol0       [0],bdt_vbfpol1       [0])".format(altMass,varSel))
            dfwwbvbscatUnclusteredUp[x] = dfwwbvbscatUnclusteredUp[x].Define("finalVar", "compute_jet_lepton_final_var(vbs_mjj       ,vbs_detajj       ,vbs_dphijj       ,vbs_zepvv	  ,bdt_vbfinc	    [0],mll{0},ngood_jets	,{1},bdt_vbfpol0       [0],bdt_vbfpol1       [0])".format(altMass,varSel))

            njString2JCut = " >= 2"
            njString3JCut = " >= 3" # not used
            njString4JCut = " >= 4" # not used
            dfwwvbs2Jcat .append(dfwwvbscat[x] .Filter("ngood_jets{0}".format(njString2JCut)))
            dfwwvbs3Jcat .append(dfwwvbscat[x] .Filter("ngood_jets{0}".format(njString3JCut)))
            dfwwvbs4Jcat .append(dfwwvbscat[x] .Filter("ngood_jets{0}".format(njString4JCut)))
            dfwwbvbs2Jcat.append(dfwwbvbscat[x].Filter("ngood_jets{0}".format(njString2JCut)))
            dfwwbvbs3Jcat.append(dfwwbvbscat[x].Filter("ngood_jets{0}".format(njString3JCut)))
            dfwwbvbs4Jcat.append(dfwwbvbscat[x].Filter("ngood_jets{0}".format(njString4JCut)))

            if(makeDataCards == 1 or makeDataCards == 2 or makeDataCards == 5):
                x1Bins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5])
            elif(makeDataCards == 3):
                x1Bins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5])
            elif(makeDataCards == 4):
                x1Bins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5])
            elif(makeDataCards == 6):
                x1Bins = array('d', [500,700,900,1100,1300,1650,2000,2450,2900])
            elif(makeDataCards == 7):
                x1Bins = array('d', [20,50,80,110,140,180,220,280,340])
            elif(makeDataCards == 8):
                x1Bins = array('d', [1.5,2.5,3.5,4.5])
            elif(makeDataCards == 9):
                x1Bins = array('d', [2.5,3.0,3.6,4.0,4.5,5.0,5.5,6.0,7.0])
            elif(makeDataCards == 10):
                x1Bins = array('d', [0.0,0.9,1.8,2.1,2.5,2.7,2.9,3.0,3.1416])
            elif(makeDataCards == 11):
                x1Bins = array('d', [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.75])
            elif(makeDataCards == 12):
                #x1Bins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5,24.5,25.5,26.5,27.5,28.5,29.5,30.5,31.5,32.5,33.5,34.5,35.5,36.5,37.5,38.5,39.5,40.5,41.5,42.5,43.5,44.5,45.5,46.5,47.5,48.5,49.5,50.5,51.5,52.5,53.5,54.5,55.5,56.5,57.5,58.5,59.5,60.5,61.5,62.5,63.5])
                x1Bins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5,24.5,25.5,26.5,27.5,28.5,29.5,30.5,31.5,32.5,33.5,34.5,35.5,36.5,37.5,38.5,39.5,40.5,41.5,42.5,43.5,44.5,45.5,46.5,47.5])
            elif(makeDataCards == 13 or makeDataCards == 14):
                #x1Bins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5,24.5])
                x1Bins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5])
            histo[110][x] = dfwwvbscat[x] .Histo1D(("histo_{0}_{1}".format(110,x), "histo_{0}_{1}".format(110,x),len(x1Bins)-1,x1Bins), "finalVar","weight")

            x2Bins = array('d', [-0.5,0.5,1.5,2.5,3.5])
            if(makeDataCards == 6 or makeDataCards == 7 or makeDataCards == 8 or makeDataCards == 9 or makeDataCards == 10 or makeDataCards == 11):
                x2Bins = x1Bins
            elif(makeDataCards == 12):
                #x2Bins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5,24.5,25.5,26.5,27.5,28.5,29.5,30.5,31.5,32.5,33.5,34.5,35.5,36.5,37.5,38.5,39.5,40.5,41.5,42.5,43.5,44.5,45.5,46.5,47.5,48.5,49.5,50.5,51.5,52.5,53.5,54.5,55.5,56.5,57.5,58.5,59.5,60.5,61.5,62.5,63.5])
                #x2Bins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5,24.5,25.5,26.5,27.5,28.5,29.5,30.5,31.5,32.5,33.5,34.5,35.5,36.5,37.5,38.5,39.5,40.5,41.5,42.5,43.5,44.5,45.5,46.5,47.5])
                x2Bins = array('d', [-0.5,0.5,1.5,2.5,3.5])
            elif(makeDataCards == 13 or makeDataCards == 14):
                #x2Bins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5,24.5])
                #x2Bins = array('d', [-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5,10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5])
                x2Bins = array('d', [-0.5,0.5,1.5,2.5,3.5])
            histo[111][x] = dfwwbvbscat[x].Histo1D(("histo_{0}_{1}".format(111,x), "histo_{0}_{1}".format(111,x),len(x2Bins)-1,x2Bins), "finalVar","weight")

            # loop over Njets for ssww and sswwb regions (njets >= 2)
            for nj in range(0,1):
                njStringCut = njString2JCut
                if(nj == 1):   njStringCut = njString3JCut
                elif(nj == 2): njStringCut = njString4JCut

                startF = 0+nj*400
                if(nj == 0):
                    for nv in range(0,136):
                        histo2D[startF+nv][x] = makeFinalVariable2DVar(dfwwvbs2Jcat[x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,nv)
                elif(nj == 1):
                    for nv in range(0,136):
                        histo2D[startF+nv][x] = makeFinalVariable2DVar(dfwwvbs3Jcat[x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,nv)
                elif(nj == 2):
                    for nv in range(0,136):
                        histo2D[startF+nv][x] = makeFinalVariable2DVar(dfwwvbs4Jcat[x],"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,nv)
                histo2D[startF+136][x]    = makeFinalVariable2DVar(dfwwvbscatMuonMomUp    [x].Filter("ngood_jets       {0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,136)
                histo2D[startF+137][x]    = makeFinalVariable2DVar(dfwwvbscatElectronMomUp[x].Filter("ngood_jets       {0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,137)
                histo2D[startF+138][x]    = makeFinalVariable2DVar(dfwwvbscatJes00Up      [x].Filter("ngood_jetsJes00Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,138)
                histo2D[startF+139][x]    = makeFinalVariable2DVar(dfwwvbscatJes01Up      [x].Filter("ngood_jetsJes01Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,139)
                histo2D[startF+140][x]    = makeFinalVariable2DVar(dfwwvbscatJes02Up      [x].Filter("ngood_jetsJes02Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,140)
                histo2D[startF+141][x]    = makeFinalVariable2DVar(dfwwvbscatJes03Up      [x].Filter("ngood_jetsJes03Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,141)
                histo2D[startF+142][x]    = makeFinalVariable2DVar(dfwwvbscatJes04Up      [x].Filter("ngood_jetsJes04Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,142)
                histo2D[startF+143][x]    = makeFinalVariable2DVar(dfwwvbscatJes05Up      [x].Filter("ngood_jetsJes05Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,143)
                histo2D[startF+144][x]    = makeFinalVariable2DVar(dfwwvbscatJes06Up      [x].Filter("ngood_jetsJes06Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,144)
                histo2D[startF+145][x]    = makeFinalVariable2DVar(dfwwvbscatJes07Up      [x].Filter("ngood_jetsJes07Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,145)
                histo2D[startF+146][x]    = makeFinalVariable2DVar(dfwwvbscatJes08Up      [x].Filter("ngood_jetsJes08Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,146)
                histo2D[startF+147][x]    = makeFinalVariable2DVar(dfwwvbscatJes09Up      [x].Filter("ngood_jetsJes09Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,147)
                histo2D[startF+148][x]    = makeFinalVariable2DVar(dfwwvbscatJes10Up      [x].Filter("ngood_jetsJes10Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,148)
                histo2D[startF+149][x]    = makeFinalVariable2DVar(dfwwvbscatJes11Up      [x].Filter("ngood_jetsJes11Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,149)
                histo2D[startF+150][x]    = makeFinalVariable2DVar(dfwwvbscatJes12Up      [x].Filter("ngood_jetsJes12Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,150)
                histo2D[startF+151][x]    = makeFinalVariable2DVar(dfwwvbscatJes13Up      [x].Filter("ngood_jetsJes13Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,151)
                histo2D[startF+152][x]    = makeFinalVariable2DVar(dfwwvbscatJes14Up      [x].Filter("ngood_jetsJes14Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,152)
                histo2D[startF+153][x]    = makeFinalVariable2DVar(dfwwvbscatJes15Up      [x].Filter("ngood_jetsJes15Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,153)
                histo2D[startF+154][x]    = makeFinalVariable2DVar(dfwwvbscatJes16Up      [x].Filter("ngood_jetsJes16Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,154)
                histo2D[startF+155][x]    = makeFinalVariable2DVar(dfwwvbscatJes17Up      [x].Filter("ngood_jetsJes17Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,155)
                histo2D[startF+156][x]    = makeFinalVariable2DVar(dfwwvbscatJes18Up      [x].Filter("ngood_jetsJes18Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,156)
                histo2D[startF+157][x]    = makeFinalVariable2DVar(dfwwvbscatJes19Up      [x].Filter("ngood_jetsJes19Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,157)
                histo2D[startF+158][x]    = makeFinalVariable2DVar(dfwwvbscatJes20Up      [x].Filter("ngood_jetsJes20Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,158)
                histo2D[startF+159][x]    = makeFinalVariable2DVar(dfwwvbscatJes21Up      [x].Filter("ngood_jetsJes21Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,159)
                histo2D[startF+160][x]    = makeFinalVariable2DVar(dfwwvbscatJes22Up      [x].Filter("ngood_jetsJes22Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,160)
                histo2D[startF+161][x]    = makeFinalVariable2DVar(dfwwvbscatJes23Up      [x].Filter("ngood_jetsJes23Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,161)
                histo2D[startF+162][x]    = makeFinalVariable2DVar(dfwwvbscatJes24Up      [x].Filter("ngood_jetsJes24Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,162)
                histo2D[startF+163][x]    = makeFinalVariable2DVar(dfwwvbscatJes25Up      [x].Filter("ngood_jetsJes25Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,163)
                histo2D[startF+164][x]    = makeFinalVariable2DVar(dfwwvbscatJes26Up      [x].Filter("ngood_jetsJes26Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,164)
                histo2D[startF+165][x]    = makeFinalVariable2DVar(dfwwvbscatJes27Up      [x].Filter("ngood_jetsJes27Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,165)
                histo2D[startF+166][x]    = makeFinalVariable2DVar(dfwwvbscatJerUp        [x].Filter("ngood_jetsJerUp  {0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,166)
                histo2D[startF+167][x]    = makeFinalVariable2DVar(dfwwvbscatJERUp        [x].Filter("ngood_jets       {0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,167)
                histo2D[startF+168][x]    = makeFinalVariable2DVar(dfwwvbscatJESUp        [x].Filter("ngood_jets       {0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,168)
                histo2D[startF+169][x]    = makeFinalVariable2DVar(dfwwvbscatUnclusteredUp[x].Filter("ngood_jets       {0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x1Bins,yBins,169)
                if(x == plotCategory("kPlotWS")):
                    startWS = 0+nj*4
                    if(nj == 0):
                        histoWS[0+startWS] = dfwwvbs2Jcat[x].Histo1D(("histoWS_{0}".format(0+startWS), "histoWS_{0}".format(0+startWS), len(x1Bins)-1,x1Bins), "finalVar","weightWSUnc0")
                        histoWS[1+startWS] = dfwwvbs2Jcat[x].Histo1D(("histoWS_{0}".format(1+startWS), "histoWS_{0}".format(1+startWS), len(x1Bins)-1,x1Bins), "finalVar","weightWSUnc1")
                    elif(nj == 1):
                        histoWS[0+startWS] = dfwwvbs3Jcat[x].Histo1D(("histoWS_{0}".format(0+startWS), "histoWS_{0}".format(0+startWS), len(x1Bins)-1,x1Bins), "finalVar","weightWSUnc0")
                        histoWS[1+startWS] = dfwwvbs3Jcat[x].Histo1D(("histoWS_{0}".format(1+startWS), "histoWS_{0}".format(1+startWS), len(x1Bins)-1,x1Bins), "finalVar","weightWSUnc1")
                    elif(nj == 2):
                        histoWS[0+startWS] = dfwwvbs4Jcat[x].Histo1D(("histoWS_{0}".format(0+startWS), "histoWS_{0}".format(0+startWS), len(x1Bins)-1,x1Bins), "finalVar","weightWSUnc0")
                        histoWS[1+startWS] = dfwwvbs4Jcat[x].Histo1D(("histoWS_{0}".format(1+startWS), "histoWS_{0}".format(1+startWS), len(x1Bins)-1,x1Bins), "finalVar","weightWSUnc1")
                if(x == plotCategory("kPlotNonPrompt")):
                    startNonPrompt = 0+nj*12
                    if(nj == 0):
                        histoNonPrompt[0+startNonPrompt] = dfwwvbs2Jcat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm0")
                        histoNonPrompt[1+startNonPrompt] = dfwwvbs2Jcat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm1")
                        histoNonPrompt[2+startNonPrompt] = dfwwvbs2Jcat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm2")
                        histoNonPrompt[3+startNonPrompt] = dfwwvbs2Jcat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte0")
                        histoNonPrompt[4+startNonPrompt] = dfwwvbs2Jcat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte1")
                        histoNonPrompt[5+startNonPrompt] = dfwwvbs2Jcat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte2")
                    elif(nj == 1):
                        histoNonPrompt[0+startNonPrompt] = dfwwvbs3Jcat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm0")
                        histoNonPrompt[1+startNonPrompt] = dfwwvbs3Jcat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm1")
                        histoNonPrompt[2+startNonPrompt] = dfwwvbs3Jcat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm2")
                        histoNonPrompt[3+startNonPrompt] = dfwwvbs3Jcat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte0")
                        histoNonPrompt[4+startNonPrompt] = dfwwvbs3Jcat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte1")
                        histoNonPrompt[5+startNonPrompt] = dfwwvbs3Jcat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte2")
                    elif(nj == 2):
                        histoNonPrompt[0+startNonPrompt] = dfwwvbs4Jcat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm0")
                        histoNonPrompt[1+startNonPrompt] = dfwwvbs4Jcat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm1")
                        histoNonPrompt[2+startNonPrompt] = dfwwvbs4Jcat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAltm2")
                        histoNonPrompt[3+startNonPrompt] = dfwwvbs4Jcat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte0")
                        histoNonPrompt[4+startNonPrompt] = dfwwvbs4Jcat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte1")
                        histoNonPrompt[5+startNonPrompt] = dfwwvbs4Jcat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(x1Bins)-1,x1Bins), "finalVar","weightFakeAlte2")

                startF = 200+nj*400
                if(nj == 0):
                    for nv in range(0,136):
                        histo2D[startF+nv][x] = makeFinalVariable2DVar(dfwwbvbs2Jcat[x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,nv)
                elif(nj == 1):
                    for nv in range(0,136):
                        histo2D[startF+nv][x] = makeFinalVariable2DVar(dfwwbvbs3Jcat[x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,nv)
                elif(nj == 2):
                    for nv in range(0,136):
                        histo2D[startF+nv][x] = makeFinalVariable2DVar(dfwwbvbs4Jcat[x],"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,nv)
                histo2D[startF+136][x]    = makeFinalVariable2DVar(dfwwbvbscatMuonMomUp    [x].Filter("ngood_jets       {0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,136)
                histo2D[startF+137][x]    = makeFinalVariable2DVar(dfwwbvbscatElectronMomUp[x].Filter("ngood_jets       {0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,137)
                histo2D[startF+138][x]    = makeFinalVariable2DVar(dfwwbvbscatJes00Up      [x].Filter("ngood_jetsJes00Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,138)
                histo2D[startF+139][x]    = makeFinalVariable2DVar(dfwwbvbscatJes01Up      [x].Filter("ngood_jetsJes01Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,139)
                histo2D[startF+140][x]    = makeFinalVariable2DVar(dfwwbvbscatJes02Up      [x].Filter("ngood_jetsJes02Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,140)
                histo2D[startF+141][x]    = makeFinalVariable2DVar(dfwwbvbscatJes03Up      [x].Filter("ngood_jetsJes03Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,141)
                histo2D[startF+142][x]    = makeFinalVariable2DVar(dfwwbvbscatJes04Up      [x].Filter("ngood_jetsJes04Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,142)
                histo2D[startF+143][x]    = makeFinalVariable2DVar(dfwwbvbscatJes05Up      [x].Filter("ngood_jetsJes05Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,143)
                histo2D[startF+144][x]    = makeFinalVariable2DVar(dfwwbvbscatJes06Up      [x].Filter("ngood_jetsJes06Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,144)
                histo2D[startF+145][x]    = makeFinalVariable2DVar(dfwwbvbscatJes07Up      [x].Filter("ngood_jetsJes07Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,145)
                histo2D[startF+146][x]    = makeFinalVariable2DVar(dfwwbvbscatJes08Up      [x].Filter("ngood_jetsJes08Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,146)
                histo2D[startF+147][x]    = makeFinalVariable2DVar(dfwwbvbscatJes09Up      [x].Filter("ngood_jetsJes09Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,147)
                histo2D[startF+148][x]    = makeFinalVariable2DVar(dfwwbvbscatJes10Up      [x].Filter("ngood_jetsJes10Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,148)
                histo2D[startF+149][x]    = makeFinalVariable2DVar(dfwwbvbscatJes11Up      [x].Filter("ngood_jetsJes11Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,149)
                histo2D[startF+150][x]    = makeFinalVariable2DVar(dfwwbvbscatJes12Up      [x].Filter("ngood_jetsJes12Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,150)
                histo2D[startF+151][x]    = makeFinalVariable2DVar(dfwwbvbscatJes13Up      [x].Filter("ngood_jetsJes13Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,151)
                histo2D[startF+152][x]    = makeFinalVariable2DVar(dfwwbvbscatJes14Up      [x].Filter("ngood_jetsJes14Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,152)
                histo2D[startF+153][x]    = makeFinalVariable2DVar(dfwwbvbscatJes15Up      [x].Filter("ngood_jetsJes15Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,153)
                histo2D[startF+154][x]    = makeFinalVariable2DVar(dfwwbvbscatJes16Up      [x].Filter("ngood_jetsJes16Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,154)
                histo2D[startF+155][x]    = makeFinalVariable2DVar(dfwwbvbscatJes17Up      [x].Filter("ngood_jetsJes17Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,155)
                histo2D[startF+156][x]    = makeFinalVariable2DVar(dfwwbvbscatJes18Up      [x].Filter("ngood_jetsJes18Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,156)
                histo2D[startF+157][x]    = makeFinalVariable2DVar(dfwwbvbscatJes19Up      [x].Filter("ngood_jetsJes19Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,157)
                histo2D[startF+158][x]    = makeFinalVariable2DVar(dfwwbvbscatJes20Up      [x].Filter("ngood_jetsJes20Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,158)
                histo2D[startF+159][x]    = makeFinalVariable2DVar(dfwwbvbscatJes21Up      [x].Filter("ngood_jetsJes21Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,159)
                histo2D[startF+160][x]    = makeFinalVariable2DVar(dfwwbvbscatJes22Up      [x].Filter("ngood_jetsJes22Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,160)
                histo2D[startF+161][x]    = makeFinalVariable2DVar(dfwwbvbscatJes23Up      [x].Filter("ngood_jetsJes23Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,161)
                histo2D[startF+162][x]    = makeFinalVariable2DVar(dfwwbvbscatJes24Up      [x].Filter("ngood_jetsJes24Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,162)
                histo2D[startF+163][x]    = makeFinalVariable2DVar(dfwwbvbscatJes25Up      [x].Filter("ngood_jetsJes25Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,163)
                histo2D[startF+164][x]    = makeFinalVariable2DVar(dfwwbvbscatJes26Up      [x].Filter("ngood_jetsJes26Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,164)
                histo2D[startF+165][x]    = makeFinalVariable2DVar(dfwwbvbscatJes27Up      [x].Filter("ngood_jetsJes27Up{0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,165)
                histo2D[startF+166][x]    = makeFinalVariable2DVar(dfwwbvbscatJerUp        [x].Filter("ngood_jetsJerUp  {0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,166)
                histo2D[startF+167][x]    = makeFinalVariable2DVar(dfwwbvbscatJERUp        [x].Filter("ngood_jets       {0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,167)
                histo2D[startF+168][x]    = makeFinalVariable2DVar(dfwwbvbscatJESUp        [x].Filter("ngood_jets       {0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,168)
                histo2D[startF+169][x]    = makeFinalVariable2DVar(dfwwbvbscatUnclusteredUp[x].Filter("ngood_jets       {0}".format(njStringCut)),"finalVar","theGenCat",theCat,startF,x,x2Bins,yBins,169)
                if(x == plotCategory("kPlotWS")):
                    startWS = 2+nj*4
                    if(nj == 0):
                        histoWS[0+startWS] = dfwwbvbs2Jcat[x].Histo1D(("histoWS_{0}".format(0+startWS), "histoWS_{0}".format(0+startWS), len(x2Bins)-1,x2Bins), "finalVar","weightWSUnc0")
                        histoWS[1+startWS] = dfwwbvbs2Jcat[x].Histo1D(("histoWS_{0}".format(1+startWS), "histoWS_{0}".format(1+startWS), len(x2Bins)-1,x2Bins), "finalVar","weightWSUnc1")
                    elif(nj == 1):
                        histoWS[0+startWS] = dfwwbvbs3Jcat[x].Histo1D(("histoWS_{0}".format(0+startWS), "histoWS_{0}".format(0+startWS), len(x2Bins)-1,x2Bins), "finalVar","weightWSUnc0")
                        histoWS[1+startWS] = dfwwbvbs3Jcat[x].Histo1D(("histoWS_{0}".format(1+startWS), "histoWS_{0}".format(1+startWS), len(x2Bins)-1,x2Bins), "finalVar","weightWSUnc1")
                    elif(nj == 2):
                        histoWS[0+startWS] = dfwwbvbs4Jcat[x].Histo1D(("histoWS_{0}".format(0+startWS), "histoWS_{0}".format(0+startWS), len(x2Bins)-1,x2Bins), "finalVar","weightWSUnc0")
                        histoWS[1+startWS] = dfwwbvbs4Jcat[x].Histo1D(("histoWS_{0}".format(1+startWS), "histoWS_{0}".format(1+startWS), len(x2Bins)-1,x2Bins), "finalVar","weightWSUnc1")
                if(x == plotCategory("kPlotNonPrompt")):
                    startNonPrompt = 6+nj*12
                    if(nj == 0):
                        histoNonPrompt[0+startNonPrompt] = dfwwbvbs2Jcat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm0")
                        histoNonPrompt[1+startNonPrompt] = dfwwbvbs2Jcat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm1")
                        histoNonPrompt[2+startNonPrompt] = dfwwbvbs2Jcat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm2")
                        histoNonPrompt[3+startNonPrompt] = dfwwbvbs2Jcat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte0")
                        histoNonPrompt[4+startNonPrompt] = dfwwbvbs2Jcat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte1")
                        histoNonPrompt[5+startNonPrompt] = dfwwbvbs2Jcat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte2")
                    elif(nj == 1):
                        histoNonPrompt[0+startNonPrompt] = dfwwbvbs3Jcat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm0")
                        histoNonPrompt[1+startNonPrompt] = dfwwbvbs3Jcat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm1")
                        histoNonPrompt[2+startNonPrompt] = dfwwbvbs3Jcat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm2")
                        histoNonPrompt[3+startNonPrompt] = dfwwbvbs3Jcat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte0")
                        histoNonPrompt[4+startNonPrompt] = dfwwbvbs3Jcat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte1")
                        histoNonPrompt[5+startNonPrompt] = dfwwbvbs3Jcat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte2")
                    elif(nj == 2):
                        histoNonPrompt[0+startNonPrompt] = dfwwbvbs4Jcat[x].Histo1D(("histoNonPrompt_{0}".format(0+startNonPrompt), "histoNonPrompt_{0}".format(0+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm0")
                        histoNonPrompt[1+startNonPrompt] = dfwwbvbs4Jcat[x].Histo1D(("histoNonPrompt_{0}".format(1+startNonPrompt), "histoNonPrompt_{0}".format(1+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm1")
                        histoNonPrompt[2+startNonPrompt] = dfwwbvbs4Jcat[x].Histo1D(("histoNonPrompt_{0}".format(2+startNonPrompt), "histoNonPrompt_{0}".format(2+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAltm2")
                        histoNonPrompt[3+startNonPrompt] = dfwwbvbs4Jcat[x].Histo1D(("histoNonPrompt_{0}".format(3+startNonPrompt), "histoNonPrompt_{0}".format(3+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte0")
                        histoNonPrompt[4+startNonPrompt] = dfwwbvbs4Jcat[x].Histo1D(("histoNonPrompt_{0}".format(4+startNonPrompt), "histoNonPrompt_{0}".format(4+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte1")
                        histoNonPrompt[5+startNonPrompt] = dfwwbvbs4Jcat[x].Histo1D(("histoNonPrompt_{0}".format(5+startNonPrompt), "histoNonPrompt_{0}".format(5+startNonPrompt), len(x2Bins)-1,x2Bins), "finalVar","weightFakeAlte2")

    report = []
    for x in range(nCat):
        report.append(dfwwvbscat[x].Report())
        if(x != theCat): continue
        print("---------------- SUMMARY {0} -------------".format(x))
        report[x].Print()

    if(makeDataCards >= 1):
        for j in range(0,nHistoMVA):
            if((j >= 0 and j < 200) or (j >= 400 and j < 600) or (j >= 800 and j < 1000)):
                for x in range(nCat):
                    histoMVA[j][x] = ROOT.TH1D("histoMVA_{0}_{1}".format(j,x), "histoMVA_{0}_{1}".format(j,x), len(x1Bins)-1,x1Bins)
            else:
                for x in range(nCat):
                    histoMVA[j][x] = ROOT.TH1D("histoMVA_{0}_{1}".format(j,x), "histoMVA_{0}_{1}".format(j,x), len(x2Bins)-1,x2Bins)

        for j in range(nHistoMVA):
            for x in range(nCat):
                if(histo2D[j][x] == 0):
                    histoMVA[j][x] = 0
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

                if(x == plotCategory("kPlotEWKSSWW") or (x == plotCategory("kPlotQCDSSWW") and versionDoEWKQCD == True)):
                    histoMVA[j][plotCategory("kPlotEWKSSWW")].SetBinError(1,0.0)
                    histoMVA[j][plotCategory("kPlotSignal0")].SetBinError(1,0.0)
                    histoMVA[j][plotCategory("kPlotSignal1")].SetBinError(1,0.0)
                    histoMVA[j][plotCategory("kPlotSignal2")].SetBinError(1,0.0)
                    histoMVA[j][plotCategory("kPlotSignal3")].SetBinError(1,0.0)
                    for i in range(histoMVA[j][x].GetNbinsX()):
                        histoMVA[j][plotCategory("kPlotEWKSSWW")].SetBinContent(i+1,        histoMVA[j][plotCategory("kPlotEWKSSWW")].GetBinContent(i+1)+       histo2D[j][x].GetBinContent(i+1,1))
                        histoMVA[j][plotCategory("kPlotEWKSSWW")].SetBinError  (i+1,pow(pow(histoMVA[j][plotCategory("kPlotEWKSSWW")].GetBinError  (i+1),2)+pow(histo2D[j][x].GetBinError  (i+1,1),2),0.5))

                        histoMVA[j][plotCategory("kPlotSignal0")].SetBinContent(i+1,        histoMVA[j][plotCategory("kPlotSignal0")].GetBinContent(i+1)+       histo2D[j][x].GetBinContent(i+1,2))
                        histoMVA[j][plotCategory("kPlotSignal0")].SetBinError  (i+1,pow(pow(histoMVA[j][plotCategory("kPlotSignal0")].GetBinError  (i+1),2)+pow(histo2D[j][x].GetBinError  (i+1,2),2),0.5))

                        histoMVA[j][plotCategory("kPlotSignal1")].SetBinContent(i+1,        histoMVA[j][plotCategory("kPlotSignal1")].GetBinContent(i+1)+       histo2D[j][x].GetBinContent(i+1,3))
                        histoMVA[j][plotCategory("kPlotSignal1")].SetBinError  (i+1,pow(pow(histoMVA[j][plotCategory("kPlotSignal1")].GetBinError  (i+1),2)+pow(histo2D[j][x].GetBinError  (i+1,3),2),0.5))

                        histoMVA[j][plotCategory("kPlotSignal2")].SetBinContent(i+1,        histoMVA[j][plotCategory("kPlotSignal2")].GetBinContent(i+1)+       histo2D[j][x].GetBinContent(i+1,4))
                        histoMVA[j][plotCategory("kPlotSignal2")].SetBinError  (i+1,pow(pow(histoMVA[j][plotCategory("kPlotSignal2")].GetBinError  (i+1),2)+pow(histo2D[j][x].GetBinError  (i+1,4),2),0.5))

                        histoMVA[j][plotCategory("kPlotSignal3")].SetBinContent(i+1,        histoMVA[j][plotCategory("kPlotSignal3")].GetBinContent(i+1)+       histo2D[j][x].GetBinContent(i+1,5))
                        histoMVA[j][plotCategory("kPlotSignal3")].SetBinError  (i+1,pow(pow(histoMVA[j][plotCategory("kPlotSignal3")].GetBinError  (i+1),2)+pow(histo2D[j][x].GetBinError  (i+1,5),2),0.5))

                else:
                    for i in range(histoMVA[j][x].GetNbinsX()):
                        histoMVA[j][x].SetBinContent(i+1,        histoMVA[j][x].GetBinContent(i+1)+       histo2D[j][x].GetBinContent(i+1,1))
                        histoMVA[j][x].SetBinError  (i+1,pow(pow(histoMVA[j][x].GetBinError  (i+1),2)+pow(histo2D[j][x].GetBinError  (i+1,1),2),0.5))

    myfile = ROOT.TFile("fillhisto_sswwAnalysis_sample{0}_year{1}_job{2}.root".format(count,year,whichJob),'RECREATE')
    for i in range(nCat):
        for j in range(nHisto):
            if(histo[j][i] == 0): continue
            histo[j][i].Write()
        for j in range(nHistoMVA):
            if(histoMVA[j][i] == 0): continue
            histoMVA[j][i].Write()
    for i in range(nhistoWS):
        if(histoWS[i] == 0): continue
        histoWS[i].Write()
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
    if(SwitchSample(sampleNOW,skimType)[2] == plotCategory("kPlotQCDSSWW") or
       SwitchSample(sampleNOW,skimType)[2] == plotCategory("kPlotEWKSSWW") or
       SwitchSample(sampleNOW,skimType)[2] == plotCategory("kPlotWZ") or
       SwitchSample(sampleNOW,skimType)[2] == plotCategory("kPlotEWKWZ")):
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

    group = 4

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
    if(whichAna == 3):
        fakePath = "data/histoFakeEtaPt_ptlcone_{0}.root".format(year)
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
        # Need to scale fake rate
        if(versionWG == True):
            histoFakeEtaPt_el[x].Scale(3.8)
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
