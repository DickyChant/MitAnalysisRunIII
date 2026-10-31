#!/usr/bin/env python3
"""Offline catalog audit, from repo root:

python3 rdf/macros/crab/validate_run2.py --survey ../run2/run2_survey.out

Executes the real sample functions with file discovery intercepted. No ROOT,
network, DAS, or CRAB installation is needed; no files are written.
"""
import argparse
import ast
import collections
import csv
import math
import os
from pathlib import Path
import re
import types


MACROS = Path(__file__).resolve().parent.parent


def catalog():
    tree = ast.parse((MACROS / 'utilsAna.py').read_text())
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name in ('SwitchSample', 'getDATAlist')]
    switch = next(n for n in functions if n.name == 'SwitchSample')
    keys = [ast.literal_eval(k) for n in ast.walk(switch)
            if isinstance(n, ast.Dict) for k in n.keys]
    duplicates = [k for k, n in collections.Counter(keys).items() if n > 1]
    assert not duplicates, f'Duplicate MC ids: {duplicates}'

    class Vector(list):
        push_back = list.append

    directories = []

    def record(path):
        directories.append(path)
        return Vector()

    scope = dict(os=os, ROOT=types.SimpleNamespace(vector=lambda _: Vector),
                 SKIM_BASE_DIR='/skims', SCRATCH_SAMPLE_DIR='/scratch',
                 USE_DIRECT_NANOAOD=False, plotCategory=lambda x: x,
                 findDIR=record, loadJSON=lambda _: None,
                 concatenate=lambda a, b: a.extend(b))
    exec(compile(ast.Module(body=functions, type_ignores=[]), 'utilsAna.py', 'exec'), scope)
    return scope, directories, set(keys)


def validate(survey_path):
    survey = survey_path.read_text()
    scope, dirs, ids = catalog()
    submit_tree = ast.parse((MACROS / 'crab/submit_crab.py').read_text())
    regex_expr = next(n.value for n in submit_tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'DAS_DIR' for t in n.targets))
    das_dir = eval(compile(ast.Expression(regex_expr), 'submit_crab.py', 'eval'), {'re': re})
    manifest = list(csv.DictReader((MACROS / 'crab/run2_samples.csv').open()))
    expected_ids = {int(r['id']) for r in manifest}
    assert len(manifest) == len(expected_ids) == 144
    assert not expected_ids.intersection(range(600, 644))
    assert not expected_ids.intersection(range(700, 720))
    assert expected_ids <= ids
    for row in manifest:
        sid = int(row['id'])
        directory, fb, category = scope['SwitchSample'](sid, '3l')
        name = os.path.basename(directory)
        assert das_dir.fullmatch(name), (sid, name)
        dataset = '/' + name.replace('+', '/')
        assert dataset == row['dataset'] and dataset in survey, (sid, dataset)
        assert math.isclose(fb, 1000 * float(row['xsec_pb']), rel_tol=1e-9), sid
        assert category == row['plot_category'] == scope['SwitchSample'](int(row['run3_equivalent']), '3l')[2]
        polarized = re.search(r'_(LL|LT|TL|TT)Polarization_', dataset)
        assert ('v9-106X' if polarized else 'v15-150X') in dataset, sid

    entries = []
    data_datasets = []
    cfg = (MACROS / 'wzAnalysis_input_condor_jobs.cfg').read_text()
    for line in cfg.splitlines():
        tok = line.split()
        if not tok or tok[0].startswith('#'):
            continue
        sid, year = map(int, tok[:2])
        entries.append((sid, year))
        if sid < 1000:
            assert sid in ids, (sid, year, 'undefined MC')
            if sid in expected_ids:
                row = next(r for r in manifest if int(r['id']) == sid)
                assert year == int(row['year'])
                assert (len(tok) < 3 or tok[2] != 'no') == (row['default_active'] == 'True')
        else:
            dirs.clear()
            scope['getDATAlist'](sid, year, '3l')
            assert dirs, (sid, year, 'undefined data')
            for directory in dirs:
                name = os.path.basename(directory)
                assert das_dir.fullmatch(name), (sid, year, name)
                if year not in (20160, 20161, 20170, 20180):
                    continue
                dataset = '/' + name.replace('+', '/')
                assert dataset in survey, (sid, year, dataset)
                assert '/MET/' not in dataset
                if year in (20160, 20161):
                    assert ('HIPM' in dataset) == (year == 20160), (sid, year, dataset)
                data_datasets.append(dataset)
    assert len(entries) == len(set(entries)), 'Duplicate cfg id/year'
    assert expected_ids <= {sid for sid, _ in entries}
    assert len(data_datasets) == len(set(data_datasets)) == 86
    print(f'PASS: {len(ids)} unique MC ids; all {len(entries)} cfg id/year pairs resolve.')
    print('PASS: 144 new MC + 86 lepton data DAS names appear verbatim in survey.')
    print('PASS: era/version, fb normalization, categories, HIPM split, reserved ids.')
    print('NOTE: validates catalog/schema only; does not validate physics normalization or corrections.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--survey', type=Path, required=True)
    validate(parser.parse_args().survey)
