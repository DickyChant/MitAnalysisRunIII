# Steps to Run Analysis on Skims

This guide explains the necessary steps to run analysis on skimmed ROOT files.

## Overview

The analysis workflow consists of several key steps:
1. **Setup and Preparation**
2. **File Discovery and Validation**
3. **Weight Calculation** (for MC)
4. **DataFrame Creation**
5. **Event Selection and Processing**
6. **Histogram Filling**
7. **Output Writing**

---

## Step-by-Step Process

### Step 1: Setup and Preparation

#### 1.1 Load Required Libraries and Modules
```python
import ROOT
import os, sys, getopt, json, time

ROOT.ROOT.EnableImplicitMT(4)  # Enable multi-threading
from utilsCategory import plotCategory
from utilsAna import getMClist, getDATAlist, findDIR
from utilsAna import SwitchSample, groupFiles, getLumi
```

#### 1.2 Load Auxiliary Files (Weights, Scale Factors)

**For MC samples, you typically need:**

- **Pileup Weights**: `data/puWeights_UL_{year}.root`
  - Contains: `puWeights`, `puWeightsUp`, `puWeightsDown`

- **Lepton Scale Factors**: `data/histoLepSFEtaPt_{year}.root`
  - Contains: `histoLepSFEtaPt_0_{muSelChoice}` (muons)
  - Contains: `histoLepSFEtaPt_1_{elSelChoice}` (electrons)

- **Trigger Scale Factors**: `data/histoTriggerSFEtaPt_{year}.root`
  - Contains: Multiple trigger SF histograms (e.g., `histoTriggerV1SFEtaPt_0_0`, etc.)

- **Fake Rate Histograms**: `data/histoFakeEtaPt_{year}.root`
  - Contains: Fake rate histograms for muons and electrons

- **W/Z Scale Factors** (if applicable): `data/histoWSSF_{year}.root`
  - Contains: W/Z SF histograms

**Example:**
```python
# Load pileup weights
puWeights = []
puPath = "data/puWeights_UL_{}.root".format(year)
fPuFile = ROOT.TFile(puPath)
puWeights.append(fPuFile.Get("puWeights"))
puWeights.append(fPuFile.Get("puWeightsUp"))
puWeights.append(fPuFile.Get("puWeightsDown"))
for x in range(3):
    puWeights[x].SetDirectory(0)  # Prevent deletion when file closes
fPuFile.Close()
```

#### 1.3 Load Configuration Files

- **Selection JSON**: `config/selection.json` or `selection.json`
  - Contains trigger definitions, lepton selections, etc.

```python
selectionJsonPath = "config/selection.json"
if not os.path.exists(selectionJsonPath):
    selectionJsonPath = "selection.json"

with open(selectionJsonPath) as jsonFile:
    jsonObject = json.load(jsonFile)
    jsonFile.close()

JSON = jsonObject['JSON']  # Golden JSON for data
triggers = jsonObject['triggers']
leptonSel = jsonObject['leptonSel']
```

---

### Step 2: File Discovery and Validation

#### 2.1 Get File List

**For MC samples:**
```python
files = getMClist(switchSample, skimType)
# OR for custom paths:
files = findDIR(samplePath)
```

**For Data samples:**
```python
files = getDATAlist(switchSample, year, skimType)
```

#### 2.2 Validate Files Exist
```python
if len(files) == 0:
    print("Warning: No files found, retrying...")
    time.sleep(10)
    files = getMClist(switchSample, skimType)  # Retry
    
if len(files) == 0:
    print("Error: No files found after retry")
    sys.exit(1)

print("Total files found: {}".format(len(files)))
```

#### 2.3 Group Files (if using job splitting)
```python
if whichJob != -1:
    group = 10  # Number of groups to split files into
    groupedFile = groupFiles(files, group)
    if whichJob >= len(groupedFile):
        print("Error: whichJob out of range")
        sys.exit(1)
    files = groupedFile[whichJob]
    print("Using {} files for job {}".format(len(files), whichJob))
```

---

### Step 3: Weight Calculation (MC Only)

#### 3.1 Get Generator Information from Runs Tree
```python
dfRuns = ROOT.RDataFrame("Runs", files)
genEventSumWeight = dfRuns.Sum("genEventSumw").GetValue()
genEventSumNoWeight = dfRuns.Sum("genEventCount").GetValue()
runGetEntries = dfRuns.Count().GetValue()
```

#### 3.2 Get Cross Section and Luminosity
```python
# Get cross section from SwitchSample
xsec = SwitchSample(switchSample, skimType)[1]  # Cross section in pb

# Get luminosity for the year
lumi = getLumi(year)  # Luminosity in fb^-1
```

#### 3.3 Calculate Event Weight
```python
# Exact weight using genEventSumWeight
weight = (xsec * 1000 / genEventSumWeight) * lumi  # xsec in pb, convert to fb

# Approximate weight (for validation)
weightApprox = (xsec * 1000 / genEventSumNoWeight) * lumi

print("Weight (exact/approx): {} / {}".format(weight, weightApprox))
print("Cross section: {} pb".format(xsec))
```

#### 3.4 Get Theory Uncertainties (Optional, for some analyses)
```python
# For theory uncertainties (LHE scale, PS weights, PDF)
nTheoryReplicas = [103, 9, 4]  # PDF, LHE scale, PS

# Get LHE scale weights
genEventSumLHEScaleWeight = []
for n in range(9):
    try:
        dfRuns = dfRuns.Define("genEventSumLHEScaleWeight{}".format(n),
                               "LHEScaleSumw[{}]".format(n))
        genEventSumLHEScaleWeight.append(
            dfRuns.Sum("genEventSumLHEScaleWeight{}".format(n)).GetValue()
        )
    except:
        genEventSumLHEScaleWeight.append(dfRuns.Count().GetValue())

# Get PS weights
genEventSumPSWeight = []
for n in range(4):
    try:
        dfRuns = dfRuns.Define("genEventSumPSWeight{}".format(n),
                               "PSSumw[{}]".format(n))
        genEventSumPSWeight.append(
            dfRuns.Sum("genEventSumPSWeight{}".format(n)).GetValue()
        )
    except:
        genEventSumPSWeight.append(dfRuns.Count().GetValue())
```

---

### Step 4: Create RDataFrame

#### 4.1 Create DataFrame from Events Tree
```python
df = ROOT.RDataFrame("Events", files)
nevents = df.Count().GetValue()
print("Total events in files: {}".format(nevents))
```

#### 4.2 Get Sample Information
```python
# Get sample directory path
sample_dir = SwitchSample(switchSample, skimType)[0]

# Extract PDType (Physics Dataset Type) from directory name
PDType = os.path.basename(sample_dir).split("+")[0]

# Get category
category = SwitchSample(switchSample, skimType)[2]

# Determine if Data or MC
isData = (switchSample >= 1000)  # Data samples have IDs >= 1000
```

---

### Step 5: Event Selection and Processing

#### 5.1 Apply Event Selection

The selection typically includes:
- **Trigger selection**: Apply trigger requirements
- **Lepton selection**: Select tight/loose leptons
- **Object quality cuts**: Apply quality requirements
- **Event-level cuts**: Apply event-level requirements (e.g., charge, mass)

**Example (simplified):**
```python
# Apply trigger selection
df = df.Filter("HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8", "Trigger selection")

# Apply lepton selection
df = df.Filter("nLoose >= 2", "At least 2 loose leptons")
df = df.Filter("nTight >= 2", "At least 2 tight leptons")

# Apply charge requirement
df = df.Filter("Sum(loose_charge) == 0", "Opposite charge")
```

#### 5.2 Define Additional Variables

```python
# Define analysis-specific variables
df = df.Define("mll", "InvariantMass(loose_pt, loose_eta, loose_phi, loose_mass)")
df = df.Define("ptll", "TransverseMomentum(loose_pt, loose_phi)")
# ... more variable definitions
```

#### 5.3 Apply Scale Factors and Weights

```python
# Apply pileup weight
df = df.Define("puWeight", "puWeights->GetBinContent(puBin)")

# Apply lepton scale factors
df = df.Define("lepSF", "lepSF_mu * lepSF_el")

# Apply trigger scale factors
df = df.Define("triggerSF", "triggerSF->GetBinContent(etaBin, ptBin)")

# Combine all weights
df = df.Define("totalWeight", "weight * puWeight * lepSF * triggerSF")
```

---

### Step 6: Histogram Filling

#### 6.1 Create Histograms
```python
# Define histogram bins
bins_mll = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250, 300, 400, 500]

# Create histograms
histo_mll = df.Histo1D(
    ("mll", "m_{ll}", len(bins_mll)-1, array.array('d', bins_mll)),
    "mll",
    "totalWeight"
)
```

#### 6.2 Fill Histograms
```python
# Histograms are filled automatically when you call GetValue()
histo_mll_value = histo_mll.GetValue()
```

---

### Step 7: Output Writing

#### 7.1 Create Output File
```python
outputFile = "fillhisto_analysis_sample{}_year{}_job{}.root".format(
    switchSample, year, whichJob
)
myfile = ROOT.TFile(outputFile, "RECREATE")
```

#### 7.2 Write Histograms
```python
# Write histograms to file
histo_mll_value.Write()

# Write other histograms...
# histo_ptll.Write()
# histo_met.Write()
# etc.

myfile.Close()
print("Output written to: {}".format(outputFile))
```

---

## Complete Example Workflow

Here's a complete example combining all steps:

```python
def readMCSample(switchSample, year, skimType, whichJob, group, 
                 puWeights, histoLepSFEtaPt_mu, histoLepSFEtaPt_el):
    
    # Step 1: Get files
    files = getMClist(switchSample, skimType)
    if len(files) == 0:
        time.sleep(10)
        files = getMClist(switchSample, skimType)
    if len(files) == 0:
        print("Error: No files found")
        return 0
    
    # Step 2: Get generator info and calculate weights
    dfRuns = ROOT.RDataFrame("Runs", files)
    genEventSumWeight = dfRuns.Sum("genEventSumw").GetValue()
    genEventSumNoWeight = dfRuns.Sum("genEventCount").GetValue()
    
    xsec = SwitchSample(switchSample, skimType)[1]
    lumi = getLumi(year)
    weight = (xsec * 1000 / genEventSumWeight) * lumi
    
    # Step 3: Group files if needed
    if whichJob != -1:
        groupedFile = groupFiles(files, group)
        files = groupedFile[whichJob]
        if len(files) == 0:
            return 0
    
    # Step 4: Create DataFrame
    df = ROOT.RDataFrame("Events", files)
    nevents = df.Count().GetValue()
    
    # Step 5: Apply selection and define variables
    df = df.Filter("nLoose >= 2", "At least 2 leptons")
    df = df.Define("mll", "InvariantMass(...)")
    
    # Step 6: Apply weights
    df = df.Define("totalWeight", "{} * puWeight * lepSF".format(weight))
    
    # Step 7: Fill histograms
    histo_mll = df.Histo1D(("mll", "m_{ll}", 50, 0, 200), "mll", "totalWeight")
    
    # Step 8: Write output
    outputFile = "fillhisto_sample{}_year{}_job{}.root".format(switchSample, year, whichJob)
    myfile = ROOT.TFile(outputFile, "RECREATE")
    histo_mll.GetValue().Write()
    myfile.Close()
    
    return 1
```

---

## Key Points to Remember

1. **Always check if files exist** before processing
2. **Use the "Runs" tree** to get generator information for MC
3. **Calculate weights correctly**: `weight = (xsec * 1000 / genEventSumWeight) * lumi`
4. **Set histograms to SetDirectory(0)** when loading from files to prevent deletion
5. **Use RDataFrame operations** (Filter, Define, Histo1D) for efficient processing
6. **Handle job splitting** if processing large datasets
7. **Validate output files** are created and contain expected histograms

---

## Common Issues and Solutions

### Issue: "No files found"
- **Check**: File paths are correct
- **Check**: Sample names match between skimming and analysis
- **Check**: Files actually exist in the directory

### Issue: "genEventSumWeight is 0"
- **Check**: Files contain "Runs" tree
- **Check**: Files are not corrupted
- **Solution**: Use approximate weight or skip weight calculation

### Issue: "Histogram not found in output"
- **Check**: Histogram was actually filled (has entries)
- **Check**: Histogram.Write() was called
- **Check**: File was closed properly

### Issue: "Memory errors"
- **Solution**: Process files in smaller groups
- **Solution**: Use whichJob to split processing
- **Solution**: Reduce number of histograms or bins

---

## Next Steps

After running analysis on all samples:
1. **Merge output files** from different jobs
2. **Combine MC samples** by category
3. **Create plots** and perform statistical analysis
4. **Compare with data** and calculate limits

