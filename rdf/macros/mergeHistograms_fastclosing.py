import ROOT
from ROOT import TFile
import os, sys, getopt, glob
from collections import defaultdict
from utilsCategory import plotCategory

ROOT.PyConfig.DisableRootLogon = True


def merge_histograms(files, pattern_func):
    merged = {}

    for f in files:
        for key in pattern_func():
            h = f.Get(key)
            if not h:
                continue

            if key not in merged:
                merged[key] = h.Clone()
                merged[key].SetDirectory(0)
            else:
                merged[key].Add(h)

    return merged


def fix_overflow_1d(h):
    nb = h.GetNbinsX()
    h.SetBinContent(nb, h.GetBinContent(nb) + h.GetBinContent(nb + 1))
    h.SetBinError(nb, (h.GetBinError(nb)**2 + h.GetBinError(nb + 1)**2)**0.5)
    h.SetBinContent(nb + 1, 0.0)
    h.SetBinError(nb + 1, 0.0)


def fix_overflow_2d(h):
    nx, ny = h.GetNbinsX(), h.GetNbinsY()

    for i in range(nx):
        h.SetBinContent(i+1, ny, h.GetBinContent(i+1, ny) + h.GetBinContent(i+1, ny+1))
        h.SetBinError(i+1, ny, (h.GetBinError(i+1, ny)**2 + h.GetBinError(i+1, ny+1)**2)**0.5)
        h.SetBinContent(i+1, ny+1, 0.0)
        h.SetBinError(i+1, ny+1, 0.0)

    for i in range(ny):
        h.SetBinContent(nx, i+1, h.GetBinContent(nx, i+1) + h.GetBinContent(nx+1, i+1))
        h.SetBinError(nx, i+1, (h.GetBinError(nx, i+1)**2 + h.GetBinError(nx+1, i+1)**2)**0.5)
        h.SetBinContent(nx+1, i+1, 0.0)
        h.SetBinError(nx+1, i+1, 0.0)


if __name__ == "__main__":

    path = "fillhisto_zAnalysis"
    year = 2018
    output = "anaZ"

    opts, _ = getopt.getopt(sys.argv[1:], "", ["path=", "year=", "output=", "help"])
    for opt, arg in opts:
        if opt == "--path": path = arg
        if opt == "--year": year = int(arg)
        if opt == "--output": output = arg

    pattern = f"{path}_sample*_year{year}_job*.root"
    files_list = glob.glob(pattern)

    print(f"Found {len(files_list)} files")
    if not files_list:
        sys.exit(1)

    files = [TFile(f) for f in files_list]

    if not os.path.exists(output):
        os.makedirs(output)

    nCat = plotCategory("kPlotCategories")
    nHisto = 1600
    nhistoNonPrompt = 50
    nhistoWS = 20

    # -------- NON PROMPT --------
    print("Merging nonprompt...")
    merged = merge_histograms(
        files,
        lambda: (f"histoNonPrompt_{i}" for i in range(nhistoNonPrompt))
    )

    if merged:
        out = TFile(f"{output}/{os.path.basename(path)}_{year}_nonprompt.root", "RECREATE")
        for name, h in merged.items():
            fix_overflow_1d(h)
            h.SetNameTitle(name, name)
            h.Write()
        out.Close()

    # -------- WRONG SIGN --------
    print("Merging wrongsign...")
    merged = merge_histograms(
        files,
        lambda: (f"histoWS_{i}" for i in range(nhistoWS))
    )

    if merged:
        out = TFile(f"{output}/{os.path.basename(path)}_{year}_wrongsign.root", "RECREATE")
        for name, h in merged.items():
            fix_overflow_1d(h)
            h.SetNameTitle(name, name)
            h.Write()
        out.Close()

    # -------- MAIN HISTOGRAMS --------
    for nh in range(nHisto):

        # --- 1D ---
        merged = merge_histograms(
            files,
            lambda nh=nh: (f"histo_{nh}_{nc}" for nc in range(nCat))
        )

        if merged:
            out = TFile(f"{output}/{os.path.basename(path)}_{year}_{nh}.root", "RECREATE")
            print("Making 1D {0}".format(f"{output}/{os.path.basename(path)}_{year}_{nh}.root"))
            for nc in range(nCat):
                name = f"histo_{nh}_{nc}"
                if name in merged:
                    h = merged[name]
                    fix_overflow_1d(h)
                    h.SetNameTitle(f"histo{nc}", f"histo{nc}")
                    h.Write()
            out.Close()

        # --- MVA ---
        merged = merge_histograms(
            files,
            lambda nh=nh: (f"histoMVA_{nh}_{nc}" for nc in range(nCat))
        )

        if merged:
            out = TFile(f"{output}/{os.path.basename(path)}_{year}_{nh}_mva.root", "RECREATE")
            print("Making 1D {0}".format(f"{output}/{os.path.basename(path)}_{year}_{nh}_mva.root"))
            for nc in range(nCat):
                name = f"histoMVA_{nh}_{nc}"
                if name in merged:
                    h = merged[name]
                    fix_overflow_1d(h)
                    h.SetNameTitle(f"histoMVA{nc}", f"histoMVA{nc}")
                    h.Write()
            out.Close()

        # --- 2D ---
        merged = merge_histograms(
            files,
            lambda nh=nh: (f"histo2d_{nh}_{nc}" for nc in range(nCat))
        )

        if merged:
            out = TFile(f"{output}/{os.path.basename(path)}_{year}_{nh}_2d.root", "RECREATE")
            print("Making 1D {0}".format(f"{output}/{os.path.basename(path)}_{year}_{nh}_2d.root"))
            for nc in range(nCat):
                name = f"histo2d_{nh}_{nc}"
                if name in merged:
                    h = merged[name]
                    fix_overflow_2d(h)
                    h.SetNameTitle(f"histo2d{nc}", f"histo2d{nc}")
                    h.Write()
            out.Close()

    for f in files:
        f.Close()

    print("DONE")
