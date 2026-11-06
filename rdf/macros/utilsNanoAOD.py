"""WZ NanoAOD schema adapters, exercised from the repository root with:

python3 rdf/macros/crab/validate_run2_compat.py --inputs ../run2

Only missing columns are supplied. Physics differences between legacy and new
classifiers are documented in crab/README.md; these aliases do not retrain them.
"""


def hasLegacyLeptonMVA(df):
    return not df.HasColumn('Electron_promptMVA') and df.HasColumn('Electron_mvaTTH')


def prepareWZNanoAOD(df, year):
    """Adapt official Run 2 v9 columns before constructing the WZ selections."""
    if year not in (20160, 20161, 20170, 20180):
        return df

    aliases = {
        'Rho_fixedGridRhoFastjetAll': 'fixedGridRhoFastjetAll',
        'Electron_mvaIso': 'Electron_mvaFall17V2Iso',
        'Electron_mvaNoIso': 'Electron_mvaFall17V2noIso',
        'Electron_mvaIso_WP80': 'Electron_mvaFall17V2Iso_WP80',
        'Electron_mvaIso_WP90': 'Electron_mvaFall17V2Iso_WP90',
        'Electron_mvaNoIso_WP80': 'Electron_mvaFall17V2noIso_WP80',
        # Different trainings: selectionLL also selects the existing mvaTTH WPs.
        'Electron_promptMVA': 'Electron_mvaTTH',
        'Muon_promptMVA': 'Muon_mvaTTH',
    }
    for target, source in aliases.items():
        if not df.HasColumn(target):
            if not df.HasColumn(source):
                raise ValueError('WZ NanoAOD: missing {} and legacy {}'.format(target, source))
            df = df.Alias(target, source)

    if not df.HasColumn('Electron_superclusterEta'):
        df = df.Define('Electron_superclusterEta', 'Electron_eta + Electron_deltaEtaSC')

    # No equivalent continuous muon-ID score in v9: mvaId is a WP bit field.
    # This diagnostic is not used by the WZ loose/fake/tight selections.
    if not df.HasColumn('Muon_mvaMuID'):
        df = df.Define('Muon_mvaMuID', 'ROOT::VecOps::RVec<float>(nMuon, -1.f)')

    # v9 DeepTau2017v2p1 stores cumulative WP bits; v15 uses ordinal WP codes.
    # Preserve the WP name (e.g. Tight = 6/6/4), not the raw integer cut on bits.
    for discriminator in ('VSjet', 'VSe', 'VSmu'):
        target = 'Tau_idDeepTau2018v2p5' + discriminator
        source = 'Tau_idDeepTau2017v2p1' + discriminator
        if not df.HasColumn(target):
            if not df.HasColumn(source):
                raise ValueError('WZ NanoAOD: no DeepTau discriminator for ' + discriminator)
            df = df.Define(target, 'return ROOT::VecOps::Map(' + source + ', [](unsigned char bits) {'
                           ' int wp = 0; for (; bits; bits >>= 1) ++wp; return wp; });')
    return df


_triggerPaths = None


def setTriggerFiles(files):
    """Record the HLT paths stored in every input file; the menu can change between files of one job."""
    import ROOT
    global _triggerPaths
    _triggerPaths = None
    for name in files:
        f = ROOT.TFile.Open(str(name))
        paths = {b.GetName() for b in f.Get("Events").GetListOfBranches() if b.GetName().startswith("HLT_")}
        f.Close()
        _triggerPaths = paths if _triggerPaths is None else _triggerPaths & paths


def pruneWZTrigger(df, expression):
    """Unavailable HLT paths are false, including an entirely absent trigger group
    and paths missing from any input file recorded by setTriggerFiles."""
    import re
    return re.sub(r'\bHLT_\w+\b', lambda m: m[0] if df.HasColumn(m[0]) and
                  (_triggerPaths is None or m[0] in _triggerPaths) else 'false', expression)
