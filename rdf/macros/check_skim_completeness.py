#!/usr/bin/env python3
"""
Pre-submission check: verify that all skim files required by an analysis exist.

For each sample/year in the analysis job config, this script resolves the expected
skim file paths (using the same SwitchSample/getMClist/getDATAlist logic as the
analysis itself) and checks that files are present and non-empty.

Usage:
    python3 check_skim_completeness.py --ana=wz [--group=1] [--verbose]
    python3 check_skim_completeness.py --ana=fake --group=9
    python3 check_skim_completeness.py --ana=trigger
    python3 check_skim_completeness.py --ana=all   # check all analyses

Exit code:
    0 = all skims present
    1 = some skims missing (details printed to stdout)
"""

import os
import sys
import getopt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utilsAna import SwitchSample, getMClist, getDATAlist, groupFiles

# Analysis code → (name, skimType, default group)
ANALYSIS_MAP = {
    "wz":      ("wzAnalysis",      "3l",  1),
    "fake":    ("fakeAnalysis",    "1l",  9),
    "trigger": ("triggerAnalysis", "2l",  9),
    "met":     ("metAnalysis",     "met", 9),
    "pu":      ("puAnalysis",      "2l",  9),
}


def check_sample_files(sampleID, year, skimType, group, verbose=False):
    """
    Check that skim files exist for a given sample/year/skimType.

    Returns:
        (total_files, missing_files, missing_list)
    """
    isData = (sampleID >= 1000)

    try:
        if isData:
            allFilesVec = getDATAlist(sampleID, year, skimType)
        else:
            allFilesVec = getMClist(sampleID, skimType, year)
    except Exception as e:
        return (0, 1, [f"ERROR resolving sample {sampleID}: {e}"])

    allFiles = [str(allFilesVec[i]) for i in range(allFilesVec.size())]

    if len(allFiles) == 0:
        # SwitchSample returned a directory, but no files found inside it
        try:
            sampleInfo = SwitchSample(sampleID, skimType)
            directory = sampleInfo[0]
        except Exception:
            directory = "UNKNOWN"
        return (0, 1, [f"NO FILES found in {directory}"])

    total = len(allFiles)
    missing = []

    for f in allFiles:
        if not os.path.exists(f):
            missing.append(f)
        elif os.path.getsize(f) < 1000:
            missing.append(f + " (too small: {} bytes)".format(os.path.getsize(f)))

    if verbose and missing:
        for m in missing[:5]:
            print(f"    MISSING: {m}")
        if len(missing) > 5:
            print(f"    ... and {len(missing) - 5} more")

    return (total, len(missing), missing)


def check_analysis(ana_name, skimType, default_group, group_override=None, verbose=False):
    """
    Check all samples in an analysis config file.

    Returns:
        (n_ok, n_problems, problem_details)
    """
    cfg_file = f"{ana_name}_input_condor_jobs.cfg"

    if not os.path.exists(cfg_file):
        print(f"  Config file not found: {cfg_file}")
        return (0, 1, [f"Config file {cfg_file} not found"])

    group = group_override if group_override is not None else default_group

    n_ok = 0
    n_problems = 0
    problem_details = []

    with open(cfg_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            sampleID = int(parts[0])
            year = int(parts[1])
            skip = parts[2] if len(parts) > 2 else ""

            if skip == "no":
                if verbose:
                    print(f"  [{sampleID:>5d} {year}] SKIPPED (marked 'no')")
                continue

            total, n_missing, missing_list = check_sample_files(
                sampleID, year, skimType, group + 1, verbose
            )

            if n_missing > 0:
                n_problems += 1
                status = f"MISSING {n_missing}/{total} files"
                problem_details.append((sampleID, year, total, n_missing, missing_list))
                print(f"  [{sampleID:>5d} {year}] {status}")
            else:
                n_ok += 1
                if verbose:
                    print(f"  [{sampleID:>5d} {year}] OK ({total} files)")

    return (n_ok, n_problems, problem_details)


def main():
    ana = "wz"
    group_override = None
    verbose = False

    valid = ["ana=", "group=", "verbose", "help"]
    usage = (
        "Usage: check_skim_completeness.py --ana=<wz|fake|trigger|met|pu|all> "
        "[--group=N] [--verbose]\n"
        "\nChecks that all skim files required by the analysis exist locally.\n"
        "Run this BEFORE submitting Condor jobs to catch missing skims early.\n"
    )

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", valid)
    except getopt.GetoptError as ex:
        print(usage)
        print(str(ex))
        sys.exit(1)

    for opt, arg in opts:
        if opt == "--help":
            print(usage)
            sys.exit(0)
        if opt == "--ana":
            ana = str(arg)
        if opt == "--group":
            group_override = int(arg)
        if opt == "--verbose":
            verbose = True

    # Determine which analyses to check
    if ana == "all":
        analyses_to_check = list(ANALYSIS_MAP.keys())
    elif ana in ANALYSIS_MAP:
        analyses_to_check = [ana]
    else:
        print(f"Unknown analysis: {ana}")
        print(f"Valid options: {', '.join(ANALYSIS_MAP.keys())}, all")
        sys.exit(1)

    total_ok = 0
    total_problems = 0
    all_problem_details = {}

    for ana_key in analyses_to_check:
        ana_name, skimType, default_group = ANALYSIS_MAP[ana_key]
        print(f"\n{'='*60}")
        print(f"Checking {ana_name} (skimType={skimType})")
        print(f"{'='*60}")

        n_ok, n_problems, details = check_analysis(
            ana_name, skimType, default_group, group_override, verbose
        )
        total_ok += n_ok
        total_problems += n_problems
        if details:
            all_problem_details[ana_key] = details

        print(f"\n  Result: {n_ok} OK, {n_problems} with problems")

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"  Total samples OK:       {total_ok}")
    print(f"  Total samples MISSING:  {total_problems}")

    if all_problem_details:
        print(f"\nMissing samples by analysis:")
        for ana_key, details in all_problem_details.items():
            ana_name = ANALYSIS_MAP[ana_key][0]
            print(f"\n  {ana_name}:")
            for sampleID, year, total, n_missing, missing_list in details:
                print(f"    sample={sampleID} year={year}: "
                      f"{n_missing}/{total} files missing")
        print(f"\nSkims must be produced before submitting analysis jobs.")
        print(f"See rdf/skimming/ for skimming instructions.")
        return 1
    else:
        print(f"\nAll skims present. Ready to submit.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
