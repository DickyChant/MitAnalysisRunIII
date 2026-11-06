# Placeholder CMSSW configuration required by CRAB's scriptExe mode.
# CRAB rewrites process.source.fileNames with the LFNs assigned to each job;
# crab_script.sh reads them back and hands them to the RDataFrame analysis.
# cmsRun is never executed.
import FWCore.ParameterSet.Config as cms

process = cms.Process("WZNTUPLE")
process.source = cms.Source("PoolSource", fileNames=cms.untracked.vstring())
process.maxEvents = cms.untracked.PSet(input=cms.untracked.int32(-1))
