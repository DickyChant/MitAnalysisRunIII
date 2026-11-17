#!/usr/bin/env python3
"""Merge the chunk outputs of one copy-mode condor job into the job's fillhisto file.

    python3 wzz_merge_chunks.py <out.root> <mc|data> chunk_0.root chunk_1.root ...

The wrapper (submit_wzz.py) copies a job's files in chunks and runs wzzAnalysis once per chunk;
each run is normalised to its own files (hJobNorm bin 1 = 1/w_c = sum(genWeight_c) / (xs lumi)).
The merge is the harvest's own (wzz/harvest.merge), done per job so the harvest sees one file per
job and the result equals one run over all the job's files:
    MC    H = sum_c f_c H_c, f_c = inv_c / sum(inv) (sumw2 with f_c^2); hJobNorm = (sum inv, 1/sum inv)
    data  H = sum_c H_c; hJobNorm of the first chunk (weight 1)
Objects that are not histograms are taken from the first chunk.
"""
import sys

import ROOT


def merge(out, kind, paths):
    files = [ROOT.TFile.Open(p) for p in paths]
    if any(not f or f.IsZombie() for f in files):
        raise SystemExit("cannot open a chunk among {0}".format(paths))
    invs = []
    for p, f in zip(paths, files):
        h = f.Get("hJobNorm")
        # a chunk whose wzzAnalysis run failed can leave an empty file: never merge it
        if not h or f.GetListOfKeys().GetSize() < 2:
            raise SystemExit("chunk without hJobNorm or histograms: {0}".format(p))
        invs.append(h.GetBinContent(1))
    if kind == "mc":
        tot = sum(invs)
        if not all(i > 0 for i in invs):
            raise SystemExit("chunk without a positive hJobNorm: {0}".format(invs))
        fac = [i / tot for i in invs]
    else:
        fac = [1.0] * len(files)
    names = []
    for f in files:
        for k in f.GetListOfKeys():
            if k.GetName() not in names:
                names.append(k.GetName())
    fout = ROOT.TFile(out, "RECREATE")
    for name in names:
        if name == "hJobNorm":
            continue
        acc = None
        for f, c in zip(files, fac):
            h = f.Get(name)
            if not h:
                continue
            if not h.InheritsFrom("TH1"):
                if acc is None:
                    acc = h.Clone(name)
                continue
            if acc is None:
                acc = h.Clone(name)
                acc.SetDirectory(0)
                if acc.GetSumw2N() == 0:
                    acc.Sumw2()
                acc.Reset()
            acc.Add(h, c)
        if acc is not None:
            fout.cd()
            acc.Write(name)
    fout.cd()
    hj = ROOT.TH1D("hJobNorm", "hJobNorm", 2, 0, 2)
    if kind == "mc":
        hj.SetBinContent(1, tot)
        hj.SetBinContent(2, 1.0 / tot)
    else:
        h0 = files[0].Get("hJobNorm")
        for b in (1, 2):
            hj.SetBinContent(b, h0.GetBinContent(b) if h0 else 1.0)
    hj.Write()
    fout.Close()
    print("merged {0} chunks into {1} ({2} objects)".format(len(paths), out, len(names)))


if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[2] not in ("mc", "data"):
        raise SystemExit(__doc__)
    merge(sys.argv[1], sys.argv[2], sys.argv[3:])
