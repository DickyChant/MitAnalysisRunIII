#!/usr/bin/env python3
"""Audit WZ's constructed graph against the supplied schemas, from repo root:

python3 rdf/macros/crab/validate_run2_compat.py --inputs ../run2
python3 rdf/macros/crab/validate_run2_compat.py --inputs ../run2 --root

The default is a ROOT-free column dependency audit, not a C++ compilation.
--root additionally evaluates the adapter expressions with synthetic RDataFrame
vectors (no correctionlib, NanoAOD file, network, or grid access required).
"""
import argparse
import ast
import contextlib
import io
import json
from pathlib import Path
import re
import runpy

MACROS = Path(__file__).resolve().parent.parent


def functions_from(path, scope, names=None):
    functions = [n for n in ast.parse(path.read_text()).body
                 if isinstance(n, ast.FunctionDef) and (names is None or n.name in names)]
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), scope)


class Graph:
    """Record the actual formatted expressions and reject missing raw branches."""
    def __init__(self, columns, raw_names):
        self.columns = set(columns)
        self.prefixes = {n.split('_', 1)[0] for n in raw_names if '_' in n}
        self.expressions = {}

    def HasColumn(self, name):
        return name in self.columns

    def GetColumnType(self, name):
        if name not in self.columns:
            raise ValueError(name)
        return 'test-only'

    def check(self, expression):
        names = set(re.findall(r'\b[A-Za-z_]\w*\b', expression))
        raw = {n for n in names if '_' in n and n.split('_', 1)[0] in self.prefixes}
        assert not raw - self.columns, (raw - self.columns, expression)

    def Define(self, name, expression):
        assert name not in self.columns, ('duplicate', name)
        self.check(expression)
        self.columns.add(name)
        self.expressions[name] = expression
        return self

    def Alias(self, target, source):
        assert source in self.columns and target not in self.columns, (target, source)
        return self.Define(target, source)

    def Filter(self, expression, *args):
        self.check(expression)
        return self


def audit(inputs):
    v9 = set((inputs / 'branches_v9.txt').read_text().split())
    v15 = set((inputs / 'branches_v15.txt').read_text().split())
    only15 = set((inputs / 'only_in_v15.txt').read_text().split())
    assert v15 - v9 == only15
    scope = runpy.run_path(str(MACROS / 'utilsNanoAOD.py'))
    functions_from(MACROS / 'utilsCategory.py', scope)
    functions_from(MACROS / 'utilsAna.py', scope, {'getLeptomSelFromJson', 'getTriggerFromJson'})
    functions_from(MACROS / 'utilsSelection.py', scope)
    functions_from(MACROS / 'wzAnalysis.py', scope, {'selectionLL'})
    config = json.loads((MACROS / 'config/selection.json').read_text())
    scope.update(jsonObject=config, JSON=config['JSON'], muSelChoice=8, elSelChoice=8,
                 useFR=1, bTagSel=0, jetEtaCut=4.7,
                 BARRELphotons=config['BARRELphotons'], ENDCAPphotons=config['ENDCAPphotons'])
    # Cover all four year branches and both data/MC graphs against each schema.
    for version, columns in [(9, v9), (15, v15)]:
        for year in (20160, 20161, 20170, 20180):
            for data in ('true', 'false'):
                df = Graph(columns, v9 | v15)
                with contextlib.redirect_stdout(io.StringIO()):
                    df = scope['selectionLL'](df, year, 'MuonEG' if data == 'true' else 'WZJJ', data, 1021 if data == 'true' else 802)
                    if data == 'false':
                        df = scope['selectionGenLepJet'](df, 15, 30, 5.0)
                    df.Define('mjjGen', '0.f')
                    df = scope['selectionWeigths'](df, data, year, 'WZJJ', 1., 1, 0, 1, [103,9,4], [1]*6, [1]*4, 'Medium', 'wp80iso', '_correction', 2)
                assert 'Jet_btagDeepFlavB' in df.expressions['clean_Jet_btagUnifiedParTB']
                if version == 9:
                    assert df.expressions['jet_SelMask0'] == '(Jet_jetId & 2) != 0'
                    assert '> 0.0' in df.expressions['tight_el']
                else:
                    assert not only15.intersection(df.expressions), 'v15 inputs were overwritten'
                    assert '> 0.8' in df.expressions['tight_el']
    # Idempotent adaptation and missing-trigger behavior.
    df = Graph(v9, v9 | v15)
    scope['prepareWZNanoAOD'](df, 20180)
    before = dict(df.expressions)
    scope['prepareWZNanoAOD'](df, 20180)
    assert df.expressions == before
    assert scope['pruneWZTrigger'](df, '(HLT_definitely_missing)') == '(false)'
    df = Graph(v15, v9 | v15)
    scope['prepareWZNanoAOD'](df, 20180)
    assert not df.expressions
    print('PASS: 16 v9/v15 x era x data/MC WZ selection/weight graphs have no missing raw columns.')
    print('PASS: existing v15 columns preserved; adapter idempotent; unavailable HLT paths become false.')
    return scope


def root_smoke(scope):
    import ROOT
    df = ROOT.RDataFrame(1)
    definitions = {
        'nMuon': '2u', 'fixedGridRhoFastjetAll': '12.f',
        'Electron_eta': 'ROOT::VecOps::RVec<float>{1.f, -1.f}',
        'Electron_deltaEtaSC': 'ROOT::VecOps::RVec<float>{0.1f, -0.2f}',
        'Electron_mvaFall17V2Iso': 'ROOT::VecOps::RVec<float>{0.2f, 0.8f}',
        'Electron_mvaFall17V2noIso': 'ROOT::VecOps::RVec<float>{0.3f, 0.9f}',
        'Electron_mvaFall17V2Iso_WP80': 'ROOT::VecOps::RVec<bool>{false, true}',
        'Electron_mvaFall17V2Iso_WP90': 'ROOT::VecOps::RVec<bool>{true, true}',
        'Electron_mvaFall17V2noIso_WP80': 'ROOT::VecOps::RVec<bool>{false, true}',
        'Electron_mvaTTH': 'ROOT::VecOps::RVec<float>{-0.1f, 0.1f}',
        'Muon_mvaTTH': 'ROOT::VecOps::RVec<float>{0.6f, 0.8f}',
        'Jet_jetId': 'ROOT::VecOps::RVec<int>{0, 2, 6}',
    }
    for kind in ('VSjet', 'VSe', 'VSmu'):
        definitions['Tau_idDeepTau2017v2p1' + kind] = 'ROOT::VecOps::RVec<unsigned char>{0, 1, 3, 7, 15, 31, 63, 127, 255}'
    for name, expression in definitions.items():
        df = df.Define(name, expression)
    df = scope['prepareWZNanoAOD'](df, 20180)
    df = (df.Define('check', 'abs(Electron_superclusterEta[0]-1.1f)<1e-5 && abs(Electron_superclusterEta[1]+1.2f)<1e-5 && Muon_mvaMuID[0]==-1.f && Rho_fixedGridRhoFastjetAll==12.f')
          .Define('tau_pass', 'Tau_idDeepTau2018v2p5VSjet >= 6')
          .Define('jet_pass', '(Jet_jetId & 2) != 0'))
    assert df.Filter('check && Sum(tau_pass)==3 && Sum(jet_pass)==2').Count().GetValue() == 1
    # Ensure actual RDF's Alias/Define behavior preserves already-created columns.
    df = scope['prepareWZNanoAOD'](df, 20180)
    assert df.Count().GetValue() == 1
    print('PASS: real ROOT RDataFrame evaluates SC eta, aliases, score sentinel, DeepTau WP decoding and jet-ID bits.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--root', action='store_true')
    args = parser.parse_args()
    scope = audit(args.inputs)
    if args.root:
        root_smoke(scope)
