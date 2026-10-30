#!/usr/bin/env python3
"""Merge histograms produced by parallel jobs.

The output naming convention and overflow-bin treatment follow the original
mergeHistograms.py. Histograms read from input files are detached and released
immediately after they have been added, so closing a large input ROOT file does
not have to destroy thousands of cached histograms at process shutdown.

Use --year=all to process every year in ALL_YEARS one after another.
"""

import getopt
import glob
import os
import sys
import time

import ROOT
from utilsCategory import plotCategory

ROOT.PyConfig.DisableRootLogon = True
# Do not let ROOT's global/current directory accumulate every histogram read
# or cloned during the merge. We detach and manage the histograms explicitly.
ROOT.TH1.AddDirectory(False)

OUTPUT_FILE_CLOSE_SECONDS = 0.0
OUTPUT_FILE_COUNT = 0

# Years used when --year=all is given.
ALL_YEARS = [20220, 20221, 20230, 20231, 20240, 20250]


def parse_years(value):
    """Return the list of years to process for the --year argument."""
    if value.strip().lower() == "all":
        return list(ALL_YEARS)
    return [int(value)]  # raises ValueError if not an integer


def release_input_histogram(hist):
    """Detach a histogram loaded from a TFile and transfer ownership to Python."""
    if not hist:
        return
    hist.SetDirectory(0)
    ROOT.SetOwnership(hist, True)


def merge_histogram(input_files, key, expected_dimension=None):
    """Return a detached sum of the histogram named *key*, or None if absent.

    Source histograms are detached and released immediately. This is important
    for avoiding a large directory-owned object list when input files contain
    many histograms.
    """
    total = None

    for input_file in input_files:
        source = input_file.Get(key)
        if not source:
            continue

        if not source.InheritsFrom("TH1"):
            print("WARNING: {0} in {1} is not a TH1; skipping".format(
                key, input_file.GetName()), file=sys.stderr)
            continue

        if expected_dimension is not None and source.GetDimension() != expected_dimension:
            print("WARNING: {0} in {1} has dimension {2}, expected {3}; skipping".format(
                key, input_file.GetName(), source.GetDimension(), expected_dimension),
                file=sys.stderr)
            release_input_histogram(source)
            del source
            continue

        if total is None:
            total = source.Clone()
            total.SetDirectory(0)
            ROOT.SetOwnership(total, True)
        else:
            if not total.Add(source):
                print("WARNING: could not add {0} from {1} (incompatible histogram?)".format(
                    key, input_file.GetName()), file=sys.stderr)

        # TFile.Get() normally associates the loaded histogram with its input
        # TDirectory. Detach it and make Python responsible for its lifetime.
        release_input_histogram(source)
        del source

    return total


def fold_overflow_1d(hist):
    """Add the overflow bin to the last visible bin and clear the overflow."""
    nbin = hist.GetNbinsX()
    hist.SetBinContent(nbin, hist.GetBinContent(nbin) + hist.GetBinContent(nbin + 1))
    hist.SetBinError(nbin, (hist.GetBinError(nbin) ** 2 +
                            hist.GetBinError(nbin + 1) ** 2) ** 0.5)
    hist.SetBinContent(nbin + 1, 0.0)
    hist.SetBinError(nbin + 1, 0.0)


def fold_overflow_2d(hist):
    """Fold each axis overflow into the last visible bin, matching the old macro."""
    nx = hist.GetNbinsX()
    ny = hist.GetNbinsY()

    # First fold y overflow for visible x bins.
    for ix in range(1, nx + 1):
        old = hist.GetBinContent(ix, ny)
        over = hist.GetBinContent(ix, ny + 1)
        err = (hist.GetBinError(ix, ny) ** 2 +
               hist.GetBinError(ix, ny + 1) ** 2) ** 0.5
        hist.SetBinContent(ix, ny, old + over)
        hist.SetBinError(ix, ny, err)
        hist.SetBinContent(ix, ny + 1, 0.0)
        hist.SetBinError(ix, ny + 1, 0.0)

    # Then fold x overflow for visible y bins. The overflow/overflow corner is
    # treated as in the original macro (it is not folded into the visible area).
    for iy in range(1, ny + 1):
        old = hist.GetBinContent(nx, iy)
        over = hist.GetBinContent(nx + 1, iy)
        err = (hist.GetBinError(nx, iy) ** 2 +
               hist.GetBinError(nx + 1, iy) ** 2) ** 0.5
        hist.SetBinContent(nx, iy, old + over)
        hist.SetBinError(nx, iy, err)
        hist.SetBinContent(nx + 1, iy, 0.0)
        hist.SetBinError(nx + 1, iy, 0.0)


def write_histogram_file(filename, histograms, output_names, is_2d=False):
    """Write the available histograms to one output file; skip empty outputs."""
    available = [(hist, name) for hist, name in zip(histograms, output_names) if hist]
    if not available:
        return False

    out = ROOT.TFile.Open(filename, "RECREATE")
    if not out or out.IsZombie():
        if out:
            out.Close()
        raise OSError("Could not create output ROOT file: {0}".format(filename))

    try:
        out.cd()
        for hist, name in available:
            hist.SetNameTitle(name, name)
            if is_2d:
                fold_overflow_2d(hist)
            else:
                fold_overflow_1d(hist)
            if hist.Write() <= 0:
                raise OSError("Failed to write histogram {0} to {1}".format(name, filename))
    finally:
        global OUTPUT_FILE_CLOSE_SECONDS, OUTPUT_FILE_COUNT
        close_start = time.perf_counter()
        out.Close()
        close_elapsed = time.perf_counter() - close_start
        OUTPUT_FILE_CLOSE_SECONDS += close_elapsed
        OUTPUT_FILE_COUNT += 1
        if close_elapsed > 1.0:
            print("WARNING: closing output file took {0:.1f} s: {1}".format(
                close_elapsed, filename))

    # Drop the detached histograms promptly instead of retaining them until exit.
    for hist, _ in available:
        del hist
    return True


def process_single_family(input_files, output_dir, base, year, suffix,
                          key_pattern, name_pattern, count, dimension=1):
    """Merge the nonprompt or wrong-sign histogram family."""
    output_name = os.path.join(output_dir, "{0}_{1}_{2}.root".format(base, year, suffix))
    histograms = []
    names = []
    for index in range(count):
        key = key_pattern.format(index)
        histograms.append(merge_histogram(input_files, key, dimension))
        names.append(name_pattern.format(index))

    if not write_histogram_file(output_name, histograms, names):
        # The original macro removed an empty output file for these families.
        if os.path.exists(output_name):
            os.remove(output_name)

    del histograms


def process_index_family(input_files, output_dir, base, year, index,
                         key_pattern, name_pattern, suffix, n_categories,
                         dimension, verbose=False):
    histograms = []
    names = []
    found = False

    for category in range(n_categories):
        key = key_pattern.format(index, category)
        hist = merge_histogram(input_files, key, dimension)
        histograms.append(hist)
        names.append(name_pattern.format(category))
        found = found or bool(hist)

    if found:
        output_name = os.path.join(
            output_dir, "{0}_{1}_{2}{3}.root".format(base, year, index, suffix))
        if verbose:
            print("Writing {0}".format(output_name))
        write_histogram_file(output_name, histograms, names, is_2d=(dimension == 2))

    del histograms


def run_one_year(year, path, output, verbose, n_categories):
    """Run the full merge for a single year exactly as the script did before.

    Raises an exception on any failure so the caller can decide whether to
    continue with the remaining years.
    """
    n_histograms = 1600
    n_nonprompt = 50
    n_wrong_sign = 20

    pattern = "{0}_sample*_year{1}_job*.root".format(path, year)
    input_paths = sorted(glob.glob(pattern))

    print("\n=== Year {0} ===".format(year))
    print("Input pattern: {0}".format(pattern))
    print("Input files found: {0}".format(len(input_paths)))
    if not input_paths:
        raise FileNotFoundError(
            "no input files found for year {0} (pattern: {1})".format(year, pattern))

    base = os.path.basename(os.path.normpath(path))
    os.makedirs(output, exist_ok=True)

    input_files = []
    start_year = time.perf_counter()
    try:
        # Reject bad input files early, and close already-open files on failure.
        for filename in input_paths:
            root_file = ROOT.TFile.Open(filename, "READ")
            if not root_file or root_file.IsZombie():
                if root_file:
                    root_file.Close()
                raise OSError("Could not open input ROOT file: {0}".format(filename))
            input_files.append(root_file)

        print("Categories: {0}; histogram indices: {1}".format(
            n_categories, n_histograms))

        t0 = time.perf_counter()
        process_single_family(input_files, output, base, year, "nonprompt",
                              "histoNonPrompt_{0}", "histoNonPrompt_{0}", n_nonprompt)
        print("Nonprompt family: {0:.1f} s".format(time.perf_counter() - t0))

        t0 = time.perf_counter()
        process_single_family(input_files, output, base, year, "wrongsign",
                              "histoWS_{0}", "histoWS_{0}", n_wrong_sign)
        print("Wrong-sign family: {0:.1f} s".format(time.perf_counter() - t0))

        t0 = time.perf_counter()
        for index in range(n_histograms):
            process_index_family(
                input_files, output, base, year, index,
                "histo_{0}_{1}", "histo{0}", "", n_categories, 1, verbose)
            process_index_family(
                input_files, output, base, year, index,
                "histoMVA_{0}_{1}", "histoMVA{0}", "_mva", n_categories, 1, verbose)
            process_index_family(
                input_files, output, base, year, index,
                "histo2d_{0}_{1}", "histo2d{0}", "_2d", n_categories, 2, verbose)

            if (index + 1) % 100 == 0 or index + 1 == n_histograms:
                elapsed = time.perf_counter() - t0
                print("Processed {0}/{1} indices ({2:.1f} s elapsed)".format(
                    index + 1, n_histograms, elapsed))

        print("Histogram processing: {0:.1f} s".format(time.perf_counter() - t0))

    finally:
        # Always close this year's input files before moving to the next year.
        close_start = time.perf_counter()
        for index, root_file in enumerate(input_files):
            one_close_start = time.perf_counter()
            root_file.Close()
            close_elapsed = time.perf_counter() - one_close_start
            if close_elapsed > 1.0:
                print("WARNING: closing input {0} took {1:.1f} s: {2}".format(
                    index + 1, close_elapsed, root_file.GetName()))
        print("Closing {0} input files: {1:.1f} s".format(
            len(input_files), time.perf_counter() - close_start))

    print("Year {0} DONE in {1:.1f} s".format(year, time.perf_counter() - start_year))


def main(argv=None):
    path = "fillhisto_zAnalysis"
    year_arg = "2018"
    output = "anaZ"
    verbose = False

    valid = ["path=", "year=", "output=", "verbose", "help"]
    usage = (
        "Usage: mergeHistograms.py [--path=<path>] [--year=<year>|all] "
        "[--output=<directory>] [--verbose]\n"
        "Defaults: --path={0} --year={1} --output={2}\n"
        "--year=all processes the years {3}"
    ).format(path, year_arg, output, ALL_YEARS)

    try:
        opts, _ = getopt.getopt(sys.argv[1:] if argv is None else argv, "", valid)
    except getopt.GetoptError as exc:
        print(usage)
        print(str(exc), file=sys.stderr)
        return 2

    for opt, arg in opts:
        if opt == "--help":
            print(usage)
            return 0
        if opt == "--path":
            path = arg
        elif opt == "--year":
            year_arg = arg
        elif opt == "--output":
            output = arg
        elif opt == "--verbose":
            verbose = True

    try:
        years = parse_years(year_arg)
    except ValueError:
        print("ERROR: --year must be an integer or 'all'", file=sys.stderr)
        return 2

    n_categories = int(plotCategory("kPlotCategories"))

    start_all = time.perf_counter()
    succeeded = []
    failed = []  # list of (year, error message)

    for year in years:
        try:
            run_one_year(year, path, output, verbose, n_categories)
            succeeded.append(year)
        except Exception as exc:
            # Record the failure and continue with the remaining years.
            failed.append((year, str(exc)))
            print("ERROR: year {0} failed: {1}".format(year, exc), file=sys.stderr)
            if len(years) > 1:
                print("Continuing with the remaining years...", file=sys.stderr)

    # Summary (most useful when several years were requested).
    print("\n==================== SUMMARY ====================")
    print("Years requested: {0}".format(years))
    print("Succeeded ({0}): {1}".format(len(succeeded), succeeded))
    print("Failed ({0}): {1}".format(len(failed), [y for y, _ in failed]))
    for year, msg in failed:
        print("  - year {0}: {1}".format(year, msg), file=sys.stderr)
    print("Output files closed: {0}; cumulative output-close time: {1:.1f} s".format(
        OUTPUT_FILE_COUNT, OUTPUT_FILE_CLOSE_SECONDS))
    print("DONE in {0:.1f} s".format(time.perf_counter() - start_all))

    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("ERROR: {0}".format(exc), file=sys.stderr)
        sys.exit(1)
