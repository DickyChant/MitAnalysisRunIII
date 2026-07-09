import ROOT
import os, json

def redefineVBSIncMVAVariables(df,tmva_helper,varString):

    dftag = df

    doUpdate = False

    if(doUpdate == True):
        dftag =(dftag.Redefine("ngood_jets"   ,"ngood_jets{0}".format(varString))
                     .Redefine("vbs_mjj"      ,"vbs_mjj{0}".format(varString))
                     .Redefine("vbs_ptjj"     ,"vbs_ptjj{0}".format(varString))
                     .Redefine("vbs_detajj"   ,"vbs_detajj{0}".format(varString))
                     .Redefine("vbs_dphijj"   ,"vbs_dphijj{0}".format(varString))
                     .Redefine("vbs_ptj1"     ,"vbs_ptj1{0}".format(varString))
                     .Redefine("vbs_ptj2"     ,"vbs_ptj2{0}".format(varString))
                     .Redefine("vbs_etaj1"    ,"vbs_etaj1{0}".format(varString))
                     .Redefine("vbs_etaj2"    ,"vbs_etaj2{0}".format(varString))
                     .Redefine("vbs_zepvv"    ,"vbs_zepvv{0}".format(varString))
                     .Redefine("vbs_zepmax"   ,"vbs_zepmax{0}".format(varString))
                     .Redefine("vbs_sumHT"    ,"vbs_sumHT{0}".format(varString))
                     .Redefine("vbs_ptvv"     ,"vbs_ptvv{0}".format(varString))
                     .Redefine("vbs_pttot"    ,"vbs_pttot{0}".format(varString))
                     .Redefine("vbs_detavvj1" ,"vbs_detavvj1{0}".format(varString))
                     .Redefine("vbs_detavvj2" ,"vbs_detavvj2{0}".format(varString))
                     .Redefine("vbs_ptbalance","vbs_ptbalance{0}".format(varString))
                     )
        dftag = tmva_helper.run_inference(dftag,"bdt_vbfinc{0}".format(varString),1)

    else:
        dftag = dftag.Define("bdt_vbfinc{0}".format(varString),"bdt_vbfinc")

    return dftag

def redefineVBSPolMVAVariables(df,tmva_helper0,tmva_helper1,varString0,altMass,varString1):

    dftag = df

    doUpdate = False

    targetString = varString0
    if(targetString == ""):
        targetString = varString1

    if(doUpdate == True):
        dftag =(dftag.Redefine("ngood_jets"   ,"ngood_jets{0}".format(varString0))
                     .Redefine("vbs_mjj"      ,"vbs_mjj{0}".format(varString0))
                     .Redefine("vbs_ptjj"     ,"vbs_ptjj{0}".format(varString0))
                     .Redefine("vbs_detajj"   ,"vbs_detajj{0}".format(varString0))
                     .Redefine("vbs_dphijj"   ,"vbs_dphijj{0}".format(varString0))
                     .Redefine("vbs_ptj1"     ,"vbs_ptj1{0}".format(varString0))
                     .Redefine("vbs_ptj2"     ,"vbs_ptj2{0}".format(varString0))
                     .Redefine("vbs_etaj1"    ,"vbs_etaj1{0}".format(varString0))
                     .Redefine("vbs_etaj2"    ,"vbs_etaj2{0}".format(varString0))
                     .Redefine("vbs_zepvv"    ,"vbs_zepvv{0}".format(varString0))
                     .Redefine("vbs_zepmax"   ,"vbs_zepmax{0}".format(varString0))
                     .Redefine("vbs_sumHT"    ,"vbs_sumHT{0}".format(varString0))
                     .Redefine("vbs_ptvv"     ,"vbs_ptvv{0}".format(varString0))
                     .Redefine("vbs_pttot"    ,"vbs_pttot{0}".format(varString0))
                     .Redefine("vbs_detavvj1" ,"vbs_detavvj1{0}".format(varString0))
                     .Redefine("vbs_detavvj2" ,"vbs_detavvj2{0}".format(varString0))
                     .Redefine("vbs_ptbalance","vbs_ptbalance{0}".format(varString0))
                     .Redefine("vbs_dphijjll" ,"vbs_dphijjll{0}".format(varString0))
                     .Redefine("vbs_rpt"      ,"vbs_rpt{0}".format(varString0))
                     #.Redefine("mll{0}".format(altMass)	    ,"mll{0}".format(varString1))
                     #.Redefine("ptll{0}".format(altMass)	    ,"ptll{0}".format(varString1))
                     #.Redefine("drll{0}".format(altMass)	    ,"drll{0}".format(varString1))
                     #.Redefine("dphill{0}".format(altMass)      ,"dphill{0}".format(varString1))
                     #.Redefine("ptl1{0}".format(altMass)	    ,"ptl1{0}".format(varString1))
                     #.Redefine("ptl2{0}".format(altMass)	    ,"ptl2{0}".format(varString1))
                     #.Redefine("dPhilMETMin{0}".format(altMass) ,"dPhilMETMin{0}".format(varString1))
                     #.Redefine("minPMET{0}".format(altMass)     ,"minPMET{0}".format(varString1))
                     #.Redefine("ptww{0}".format(altMass)	    ,"ptww{0}".format(varString1))
                     #.Redefine("mcoll{0}".format(altMass)	    ,"mcoll{0}".format(varString1))
                     #.Redefine("mtwmax{0}".format(altMass)      ,"mtwmax{0}".format(varString1))
                     #.Redefine("mtwmin{0}".format(altMass)      ,"mtwmin{0}".format(varString1))
                     )
        dftag = tmva_helper0.run_inference(dftag,"bdt_vbfpol0{0}".format(targetString),1)
        dftag = tmva_helper1.run_inference(dftag,"bdt_vbfpol1{0}".format(targetString),1)

    else:
        dftag = dftag.Define("bdt_vbfpol0{0}".format(targetString),"bdt_vbfpol0")
        dftag = dftag.Define("bdt_vbfpol1{0}".format(targetString),"bdt_vbfpol1")

    return dftag
