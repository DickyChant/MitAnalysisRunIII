import ROOT
import os, json, sys, fnmatch
from utilsCategory import plotCategory
from subprocess import call,check_output
#from correctionlib import _core
import correctionlib
correctionlib.register_pyroot_binding()
#ROOT.gInterpreter.Declare('#include "mysf.h"')
#ROOT.gInterpreter.Load("mysf.so")

useXROOTD = False

# CMS Connect mode: resolve local paths to accessible paths for remote Condor jobs
# Set via environment variable CMS_CONNECT_MODE=1 or in code
CMS_CONNECT_MODE = os.environ.get('CMS_CONNECT_MODE', '0') == '1'
CMS_CONNECT_FILES_TRANSFERRED = os.environ.get('CMS_CONNECT_FILES_TRANSFERRED', '0') == '1'

# File path mapping for transferred files (loaded on demand)
_file_path_mapping = None

def loadFileMapping():
    """Load file path mapping for transferred files."""
    global _file_path_mapping
    if _file_path_mapping is not None:
        return _file_path_mapping
    
    _file_path_mapping = {}
    mappingFile = os.environ.get('CMS_CONNECT_FILE_MAPPING', 'file_path_mapping.txt')
    
    if os.path.exists(mappingFile):
        try:
            with open(mappingFile, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '\t' in line:
                        orig, trans = line.split('\t', 1)
                        _file_path_mapping[orig] = trans
            print(f"Loaded {len(_file_path_mapping)} file path mappings from {mappingFile}")
        except Exception as e:
            print(f"Error loading file mapping: {e}")
    
    return _file_path_mapping

def resolvePathForRemote(localPath):
    """
    Resolve local file paths to accessible paths for remote Condor jobs on CMS Connect.
    
    This function converts local paths (like /home/scratch/...) to paths accessible
    from remote worker nodes. Options include:
    1. xrootd URLs (if files are accessible via xrootd)
    2. Network paths (if accessible via shared filesystem)
    3. Keep original path if already accessible
    
    Args:
        localPath: Local file or directory path
        
    Returns:
        Resolved path accessible from remote nodes
    """
    # First check if files were transferred and use mapping
    if CMS_CONNECT_FILES_TRANSFERRED:
        mapping = loadFileMapping()
        if localPath in mapping:
            mappedPath = mapping[localPath]
            if os.path.exists(mappedPath):
                return mappedPath
            # Try to find file by basename in transferred_data
            filename = os.path.basename(localPath)
            transferredDir = os.environ.get('CMS_CONNECT_DATA_DIR', 'transferred_data')
            candidatePath = os.path.join(transferredDir, filename)
            if os.path.exists(candidatePath):
                return candidatePath
    
    if not CMS_CONNECT_MODE:
        return localPath
    
    # If path is already an xrootd URL, return as-is
    if localPath.startswith('root://'):
        return localPath
    
    # Map local paths to accessible paths
    # Common patterns for CMS Connect:
    
    # MIT T2/T3 paths - convert to xrootd if available
    if '/mnt/T2_US_MIT/' in localPath or '/mnt/T3_US_MIT/' in localPath:
        # Convert to xrootd URL
        if '/mnt/T2_US_MIT/' in localPath:
            xrdPath = localPath.replace('/mnt/T2_US_MIT/', '')
            return f'root://t2serv007.mit.edu/{xrdPath}'
        elif '/mnt/T3_US_MIT/' in localPath:
            xrdPath = localPath.replace('/mnt/T3_US_MIT/', '')
            return f'root://t3serv017.mit.edu/{xrdPath}'
    
    # Ceph submit paths - may be accessible via xrootd
    if '/ceph/submit/data/group/cms' in localPath:
        xrdPath = localPath.replace('/ceph/submit/data/group/cms', '')
        return f'root://submit50.mit.edu{xrdPath}'
    
    # Home/scratch paths - these typically need special handling
    # For CMS Connect, these may need to be:
    # 1. Converted to xrootd if available
    # 2. Or kept as-is if accessible via network mount
    # 3. Or files need to be transferred (handled separately)
    if '/home/scratch/' in localPath:
        # Try to find if there's an xrootd equivalent
        # For now, return as-is and let findDIR handle it
        # In practice, you may need to configure this based on your setup
        return localPath
    
    # Default: return as-is (may work if accessible via network mount)
    return localPath

def getLumi(year):
    lumi = [36.1, 41.5, 60.0, 8.1, 26.7, 18.1, 9.7, 108.5, 81.5]

    lumiBit = -999
    if(year == 2016): lumiBit = 0
    elif(year == 2017): lumiBit = 1
    elif(year == 2018): lumiBit = 2
    elif(year == 20220): lumiBit = 3
    elif(year == 20221): lumiBit = 4
    elif(year == 20230): lumiBit = 5
    elif(year == 20231): lumiBit = 6
    elif(year == 20240): lumiBit = 7
    elif(year == 20250): lumiBit = 8

    print("lumi({0}/{1}) = {2}".format(year,lumiBit,lumi[lumiBit]))

    return lumi[lumiBit]

#if "/functions.so" not in ROOT.gSystem.GetLibraries():
#    ROOT.gSystem.CompileMacro("functions.cc","k")
ROOT.gInterpreter.ProcessLine('#include "functions.h"')

#def loadCorrectionSet(year):
#    ROOT.gInterpreter.Load("mysf.so")
#    ROOT.gInterpreter.Declare('#include "mysf.h"')
#    ROOT.gInterpreter.ProcessLine('auto corr_sf = MyCorrections(%d);' % (year))

def loadJSON(fIn):

    if not os.path.isfile(fIn):
        print("JSON file %s does not exist" % fIn)
        return

    if not hasattr(ROOT, "jsonMap"):
        print("jsonMap not found in ROOT dict")
        return

    info = json.load(open(fIn))
    print("JSON file %s loaded" % fIn)
    for k,v in info.items():

        vec = ROOT.std.vector["std::pair<unsigned int, unsigned int>"]()
        for combo in v:
            pair = ROOT.std.pair["unsigned int", "unsigned int"](*[int(c) for c in combo])
            vec.push_back(pair)
            ROOT.jsonMap[int(k)] = vec

def getTriggerFromJson(overall, type, year):

    if(year > 10000): year = year // 10

    for trigger in overall:
        if(trigger['name'] == type and trigger['year'] == year): return trigger['definition']

def getLeptomSelFromJson(overall, type, year, debug = 0):

    if(year > 10000): year = year // 10
    version = 12
    if(year >= 2024): version = 15

    for leptonSel in overall:
        if(leptonSel['name'] == type and leptonSel['version'] == version):
            if(debug == 1):
                print("{0}({1}): {2}".format(leptonSel['name'],leptonSel['version'],leptonSel['definition']))
            return leptonSel['definition']

def getMesonFromJson(overall, type, cat ):

    for meson in overall:
        if meson['name'] == type and meson['type'] == cat: return meson['definition']

def findDataset(name):

    DASclient = "dasgoclient -query '%(query)s'"
    cmd= DASclient%{'query':'file dataset=%s'%name}
    print(cmd)
    check_output(cmd,shell=True)
    fileList=[ 'root://xrootd-cms.infn.it//'+x for x in check_output(cmd,shell=True).split() ]

    files_ROOT = ROOT.vector('string')()
    for f in fileList: files_ROOT.push_back(f)

    return files_ROOT

def findDIR(directory):

    # Print to stderr to avoid contaminating file lists when called from collect_files_for_job.py
    print(directory, file=sys.stderr)

    # Resolve path for remote access if in CMS Connect mode
    resolvedDir = resolvePathForRemote(directory)
    if resolvedDir != directory:
        print(f"Resolved path for remote access: {resolvedDir}")

    maxFiles = 1000000000
    if("/1l/" in directory and "NANOAODSIM" in directory and
       "TTto4Q" not in directory and "WWto4Q" not in directory):
        maxFiles = 200

    # HACK!
    #if("/2l/" in directory and "NANOAODSIM" in directory and
    #   ("DY" in directory or "TT" in directory)):
    #    maxFiles = 100

    counter = 0
    rootFiles = ROOT.vector('string')()

    # Check if this is an xrootd URL
    if resolvedDir.startswith('root://'):
        # Use xrdfs to list files recursively
        try:
            # Extract server and path from xrootd URL
            # Format: root://server/path
            parts = resolvedDir.replace('root://', '').split('/', 1)
            if len(parts) == 2:
                server = parts[0]
                xrdpath = '/' + parts[1]
            else:
                server = parts[0]
                xrdpath = '/'
            
            print(f"Listing xrootd files from root://{server}{xrdpath}")
            
            # Recursively list files using xrdfs
            def list_xrootd_recursive(server, path):
                """Recursively list files in xrootd directory"""
                files = []
                try:
                    # List directory contents
                    output = check_output(['xrdfs', f'root://{server}', 'ls', path], 
                                        stderr=sys.stderr).decode(sys.stdout.encoding)
                    entries = [line.strip() for line in output.split('\n') if line.strip()]
                    
                    for entry in entries:
                        # Check if it's a directory (xrdfs ls shows directories with trailing /)
                        if entry.endswith('/'):
                            # Recursively list subdirectory
                            subdir = entry.rstrip('/')
                            files.extend(list_xrootd_recursive(server, subdir))
                        else:
                            # It's a file
                            if entry.endswith('.root'):
                                files.append(entry)
                except Exception as e:
                    print(f"Error listing {path}: {e}")
                return files
            
            stringFiles = list_xrootd_recursive(server, xrdpath)
            
            for filePath in stringFiles:
                # Construct full xrootd URL
                fullPath = f'root://{server}{filePath}'
                if "failed/" in fullPath: continue
                if "log/" in fullPath: continue
                if ".txt" in fullPath: continue
                if(("XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" in fullPath) or
                   ("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" in fullPath)):
                    print("Bad file: {0}".format(fullPath))
                    continue
                counter+=1
                if(counter > maxFiles): break
                rootFiles.push_back(fullPath)
            
            print(f"Found {len(rootFiles)} files via xrootd")
            return rootFiles
        except Exception as e:
            print(f"Error listing xrootd files: {e}")
            print(f"Falling back to local path access")
            # Fall through to local file access
    
    # Handle local xrootd access (original code)
    if(useXROOTD == True and "/ceph/submit/data/group/cms" in directory):
        xrd = "root://submit50.mit.edu/"
        xrdpath = directory.replace("/ceph/submit/data/group/cms","")
        f = check_output(['xrdfs', f'{xrd}', 'ls', xrdpath]).decode(sys.stdout.encoding)
        stringFiles = f.split()
        for e in range(len(stringFiles)):
            filePath = xrd + stringFiles[e]
            if "failed/" in filePath: continue
            if "log/" in filePath: continue
            if ".txt" in filePath: continue
            counter+=1
            if(counter > maxFiles): break
            rootFiles.push_back(filePath)

    # Local file system access
    else:
        # Use resolved directory for file access
        accessDir = resolvedDir if not resolvedDir.startswith('root://') else directory
        
        # If files were transferred, use file mapping to find them
        if CMS_CONNECT_FILES_TRANSFERRED and not os.path.exists(accessDir):
            mapping = loadFileMapping()
            if mapping:
                # Use mapping to find transferred files
                print(f"Using file mapping to find transferred files ({len(mapping)} entries)")
                print(f"Looking for files matching directory: {directory}")
                
                # Normalize directory path for matching (remove trailing slash)
                normDir = directory.rstrip('/')
                
                # For directory-based access, we need to find files that match the directory
                # Match files whose original path starts with the directory path
                matchedCount = 0
                for origPath, transPath in mapping.items():
                    # Check if this file belongs to the requested directory
                    # Normalize original path for comparison
                    normOrigPath = origPath.rstrip('/')
                    
                    # Match if original path starts with directory, or directory is in the path
                    if normOrigPath.startswith(normDir) or normDir in normOrigPath:
                        # Verify the transferred file exists
                        if os.path.exists(transPath) and transPath.endswith('.root'):
                            if "failed/" in transPath: continue
                            if "log/" in transPath: continue
                            if ".txt" in transPath: continue
                            if(("XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" in transPath) or
                               ("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" in transPath)):
                                continue
                            rootFiles.push_back(transPath)
                            matchedCount += 1
                            counter += 1
                            if(counter > maxFiles): break
                
                if len(rootFiles) > 0:
                    print(f"Found {len(rootFiles)} files via file mapping (matched {matchedCount} files)")
                    return rootFiles
                else:
                    print(f"Warning: No files matched directory {directory} in mapping")
                
                # Fallback: search current directory for ROOT files
                print("Searching current directory for transferred ROOT files...")
                for root, directories, filenames in os.walk('.'):
                    for f in filenames:
                        if f.endswith('.root'):
                            filePath = os.path.join(os.path.abspath(root), f)
                            if "failed/" in filePath: continue
                            if "log/" in filePath: continue
                            if ".txt" in filePath: continue
                            if(("XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" in filePath) or
                               ("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" in filePath)):
                                continue
                            counter+=1
                            if(counter > maxFiles): break
                            rootFiles.push_back(filePath)
                if len(rootFiles) > 0:
                    print(f"Found {len(rootFiles)} files in current directory")
                    return rootFiles
        
        if not os.path.exists(accessDir):
            print(f"Warning: Directory does not exist: {accessDir}")
            print(f"Original directory: {directory}")
            print(f"Resolved directory: {resolvedDir}")
            # Return empty list if directory doesn't exist
            return rootFiles
        
        for root, directories, filenames in os.walk(accessDir):
            for f in filenames:

                isBadFile = False
                filePath = os.path.join(os.path.abspath(root), f)
                if "failed/" in filePath: continue
                if "log/" in filePath: continue
                if ".txt" in filePath: continue
                if(("XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" in filePath) or

                   ("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" in filePath)
                   ): isBadFile = True

                if(isBadFile == True):
                    print("Bad file: {0}".format(filePath))
                    continue
                counter+=1
                if(counter > maxFiles): break
                rootFiles.push_back(filePath)

    #print(rootFiles)
    return rootFiles

def findMany(basedir, regex):

    if basedir[-1] == "/": basedir = basedir[:-1]
    regex = basedir + "/" + regex

    rootFiles = ROOT.vector('string')()
    for root, directories, filenames in os.walk(basedir):

        for f in filenames:

            filePath = os.path.join(os.path.abspath(root), f)
            if "failed/" in filePath: continue
            if "log/" in filePath: continue
            if fnmatch.fnmatch(filePath, regex): rootFiles.push_back(filePath)

    return rootFiles

# split fIns files in group files
def groupFiles(fIns, group):

    ret =  [fIns[i::group] for i in range(group)]

    return ret

def concatenate(result, tmp1):
    for f in tmp1:
        result.push_back(f)

def getMClist(sampleNOW, skimType, year=None):
    # If files were transferred, findDIR will use the file mapping automatically
    # So we can just call findDIR normally - it will handle the mapping
    files = findDIR("{}".format(SwitchSample(sampleNOW, skimType, year)[0]))
    return files

def getDATAlist(type, year, skimType):

    if(year > 10000): year = year // 10

    #dirT2 = "/mnt/T2_US_MIT/hadoop/cms/store/user/paus/nanohr/D00/"
    #dirT2 = "/mnt/T3_US_MIT/hadoop/scratch/ceballos/nanoaod/skims_submit/" + skimType
    dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType

    if year == 2022:
        dirT2 = "/home/scratch/stqian/wz_guillermo_2022a_2022b_2022d_2023a/skims_2022d/" + skimType
    elif year == 2023:
        dirT2 = "/home/scratch/stqian/wz_guillermo/skims_2023d/" + skimType
    elif year == 2024:
        dirT2 = "/home/scratch/stqian/wz_guillermo/skims_2024d/" + skimType
    elif year == 2025:
        dirT2 = "/home/scratch/stqian/wz_guillermo/skims_2025d/" + skimType

    dirTest = "/ceph/submit/data/group/cms/store/user/ceballos/test/test/"

    jsnName = ""
    if(year == 2016):
        jsnName = "Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt"
    elif(year == 2017):
        jsnName = "Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt"
    elif(year == 2018):
        jsnName = "Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt"
    elif(year == 2022):
        jsnName = "Cert_Collisions2022_355100_362760_Golden.json"
    elif(year == 2023):
        jsnName = "Cert_Collisions2023_366442_370790_Golden.json"
    elif(year == 2024):
        jsnName = "Cert_Collisions2024_378981_386951_Golden.json"
    elif(year == 2025):
        jsnName = "Cert_Collisions2025_391658_398860_Golden.json"

    if os.path.exists(os.path.join("jsns",jsnName)):
        loadJSON(os.path.join("jsns",jsnName))
    else:
        loadJSON(jsnName)

    filesL = []
    ##### 2018 ####
    if(year == 2018 and type == 1000):
        filesL = findDIR("{0}/SingleMuon+Run2018A-UL2018_MiniAODv2-v2+MINIAOD".format(dirT2))
    elif(year == 2018 and type == 1001):
        filesL = findDIR("{0}/SingleMuon+Run2018B-UL2018_MiniAODv2-v2+MINIAOD".format(dirT2))
    elif(year == 2018 and type == 1002):
        filesL = findDIR("{0}/SingleMuon+Run2018C-UL2018_MiniAODv2-v2+MINIAOD".format(dirT2))
    elif(year == 2018 and type == 1003):
        filesL = findDIR("{0}/SingleMuon+Run2018D-UL2018_MiniAODv2-v3+MINIAOD".format(dirT2))

    elif(year == 2018 and type == 1010):
        filesL = findDIR("{0}/DoubleMuon+Run2018A-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2))
    elif(year == 2018 and type == 1011):
        filesL = findDIR("{0}/DoubleMuon+Run2018B-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2))
    elif(year == 2018 and type == 1012):
        filesL = findDIR("{0}/DoubleMuon+Run2018C-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2))
    elif(year == 2018 and type == 1013):
        filesL = findDIR("{0}/DoubleMuon+Run2018D-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2))

    elif(year == 2018 and type == 1020):
        filesL = findDIR("{0}/MuonEG+Run2018A-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2))
    elif(year == 2018 and type == 1021):
        filesL = findDIR("{0}/MuonEG+Run2018B-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2))
    elif(year == 2018 and type == 1022):
        filesL = findDIR("{0}/MuonEG+Run2018C-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2))
    elif(year == 2018 and type == 1023):
        filesL = findDIR("{0}/MuonEG+Run2018D-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2))

    elif(year == 2018 and type == 1030):
        filesL = findDIR("{0}/EGamma+Run2018A-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2))
    elif(year == 2018 and type == 1031):
        filesL = findDIR("{0}/EGamma+Run2018B-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2))
    elif(year == 2018 and type == 1032):
        filesL = findDIR("{0}/EGamma+Run2018C-UL2018_MiniAODv2-v1+MINIAOD".format(dirT2))
    elif(year == 2018 and type == 1033):
        filesL = findDIR("{0}/EGamma+Run2018D-UL2018_MiniAODv2-v2+MINIAOD".format(dirT2))

    elif(year == 2018 and type == 1050):
        filesL = findDIR("{0}/MET+Run2018A-UL2018_MiniAODv2_NanoAODv9-v2+NANOAOD".format(dirT2))
    elif(year == 2018 and type == 1051):
        filesL = findDIR("{0}/MET+Run2018B-UL2018_MiniAODv2_NanoAODv9-v2+NANOAOD".format(dirT2))
    elif(year == 2018 and type == 1052):
        filesL = findDIR("{0}/MET+Run2018C-UL2018_MiniAODv2_NanoAODv9-v1+NANOAOD".format(dirT2))
    elif(year == 2018 and type == 1053):
        filesL = findDIR("{0}/MET+Run2018D-UL2018_MiniAODv2_NanoAODv9-v1+NANOAOD".format(dirT2))

    ##### 2022 ####
    elif(year == 2022 and type == 1001):
        filesL = findDIR("{0}/SingleMuon+Run2022B-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1002):
        filesL = findDIR("{0}/SingleMuon+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2))

    elif(year == 2022 and type == 1011):
        filesL = findDIR("{0}/DoubleMuon+Run2022B-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1012):
        filesL = findDIR("{0}/DoubleMuon+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2))

    elif(year == 2022 and type == 1021):
        filesL = findDIR("{0}/MuonEG+Run2022B-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1022):
        filesL = findDIR("{0}/MuonEG+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1023):
        filesL = findDIR("{0}/MuonEG+Run2022D-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1024):
        filesL = findDIR("{0}/MuonEG+Run2022E-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1025):
        filesL = findDIR("{0}/MuonEG+Run2022F-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1026):
        filesL = findDIR("{0}/MuonEG+Run2022G-22Sep2023-v1+NANOAOD".format(dirT2))

    elif(year == 2022 and type == 1031):
        filesL = findDIR("{0}/EGamma+Run2022B-22Sep2023-v2+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1032):
        filesL = findDIR("{0}/EGamma+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1033):
        filesL = findDIR("{0}/EGamma+Run2022D-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1034):
        filesL = findDIR("{0}/EGamma+Run2022E-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1035):
        filesL = findDIR("{0}/EGamma+Run2022F-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1036):
        filesL = findDIR("{0}/EGamma+Run2022G-22Sep2023-v2+NANOAOD".format(dirT2))

    elif(year == 2022 and type == 1042):
        filesL = findDIR("{0}/Muon+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1043):
        filesL = findDIR("{0}/Muon+Run2022D-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1044):
        filesL = findDIR("{0}/Muon+Run2022E-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1045):
        filesL = findDIR("{0}/Muon+Run2022F-22Sep2023-v2+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1046):
        filesL = findDIR("{0}/Muon+Run2022G-22Sep2023-v1+NANOAOD".format(dirT2))

    elif(year == 2022 and type == 1051):
        filesL = findDIR("{0}/MET+Run2022B-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1052):
        filesL = findDIR("{0}/MET+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET+Run2022C-22Sep2023-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2022 and type == 1053):
        filesL = findDIR("{0}/JetMET+Run2022D-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1054):
        filesL = findDIR("{0}/JetMET+Run2022E-22Sep2023-v1+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1055):
        filesL = findDIR("{0}/JetMET+Run2022F-22Sep2023-v2+NANOAOD".format(dirT2))
    elif(year == 2022 and type == 1056):
        filesL = findDIR("{0}/JetMET+Run2022G-22Sep2023-v2+NANOAOD".format(dirT2))

    ##### 2023 ####
    elif(year == 2023 and type == 1022):
        filesL = findDIR("{0}/MuonEG+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/MuonEG+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/MuonEG+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/MuonEG+Run2023C-22Sep2023_v4-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2023 and type == 1023):
        filesL = findDIR("{0}/MuonEG+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/MuonEG+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2023 and type == 1032):
        filesL   = findDIR("{0}/EGamma0+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma0+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma0+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma0+Run2023C-22Sep2023_v4-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma1+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma1+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma1+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma1+Run2023C-22Sep2023_v4-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2023 and type == 1033):
        filesL   = findDIR("{0}/EGamma0+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma0+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma1+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma1+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2023 and type == 1042):
        filesL   = findDIR("{0}/Muon0+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon0+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon0+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon0+Run2023C-22Sep2023_v4-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon1+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon1+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon1+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon1+Run2023C-22Sep2023_v4-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2023 and type == 1043):
        filesL   = findDIR("{0}/Muon0+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon0+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon1+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon1+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2023 and type == 1052):
        filesL   = findDIR("{0}/JetMET0+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET0+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET0+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET0+Run2023C-22Sep2023_v4-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET1+Run2023C-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET1+Run2023C-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET1+Run2023C-22Sep2023_v3-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET1+Run2023C-22Sep2023_v4-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2023 and type == 1053):
        filesL   = findDIR("{0}/JetMET0+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET0+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET1+Run2023D-22Sep2023_v1-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET1+Run2023D-22Sep2023_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)

    ##### 2024 ####
    elif(year == 2024 and type == 1022):
        filesL   = findDIR("{0}/MuonEG+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
    elif(year == 2024 and type == 1023):
        filesL   = findDIR("{0}/MuonEG+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
    elif(year == 2024 and type == 1024):
        filesL   = findDIR("{0}/MuonEG+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
    elif(year == 2024 and type == 1025):
        filesL   = findDIR("{0}/MuonEG+Run2024F-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
    elif(year == 2024 and type == 1026):
        filesL   = findDIR("{0}/MuonEG+Run2024G-MINIv6NANOv15-v3+NANOAOD".format(dirT2))
    elif(year == 2024 and type == 1027):
        filesL   = findDIR("{0}/MuonEG+Run2024H-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
    elif(year == 2024 and type == 1028):
        filesL   = findDIR("{0}/MuonEG+Run2024I-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/MuonEG+Run2024I-MINIv6NANOv15_v2-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2024 and type == 1032):
        filesL   = findDIR("{0}/EGamma0+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1033):
        filesL   = findDIR("{0}/EGamma0+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1034):
        filesL   = findDIR("{0}/EGamma0+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1035):
        filesL   = findDIR("{0}/EGamma0+Run2024F-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2024F-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1036):
        filesL   = findDIR("{0}/EGamma0+Run2024G-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2024G-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1037):
        filesL   = findDIR("{0}/EGamma0+Run2024H-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2024H-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1038):
        filesL   = findDIR("{0}/EGamma0+Run2024I-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2024I-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma0+Run2024I-MINIv6NANOv15_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma1+Run2024I-MINIv6NANOv15_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2024 and type == 1042):
        filesL   = findDIR("{0}/Muon0+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1043):
        filesL   = findDIR("{0}/Muon0+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1044):
        filesL   = findDIR("{0}/Muon0+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1045):
        filesL   = findDIR("{0}/Muon0+Run2024F-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2024F-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1046):
        filesL   = findDIR("{0}/Muon0+Run2024G-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2024G-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1047):
        filesL   = findDIR("{0}/Muon0+Run2024H-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2024H-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1048):
        filesL   = findDIR("{0}/Muon0+Run2024I-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2024I-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon0+Run2024I-MINIv6NANOv15_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon1+Run2024I-MINIv6NANOv15_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2024 and type == 1052):
        filesL   = findDIR("{0}/JetMET0+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2024C-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1053):
        filesL   = findDIR("{0}/JetMET0+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2024D-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1054):
        filesL   = findDIR("{0}/JetMET0+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2024E-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1055):
        filesL   = findDIR("{0}/JetMET0+Run2024F-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2024F-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1056):
        filesL   = findDIR("{0}/JetMET0+Run2024G-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2024G-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1057):
        filesL   = findDIR("{0}/JetMET0+Run2024H-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2024H-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2024 and type == 1058):
        filesL   = findDIR("{0}/JetMET0+Run2024I-MINIv6NANOv15-v2+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2024I-MINIv6NANOv15-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET0+Run2024I-MINIv6NANOv15_v2-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET1+Run2024I-MINIv6NANOv15_v2-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)

    ##### 2025 ####
    elif(year == 2025 and type == 1021):
        filesL   = findDIR("{0}/MuonEG+Run2025B-PromptReco-v1+NANOAOD".format(dirT2))
    elif(year == 2025 and type == 1022):
        filesL   = findDIR("{0}/MuonEG+Run2025C-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/MuonEG+Run2025C-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1023):
        filesL   = findDIR("{0}/MuonEG+Run2025D-PromptReco-v1+NANOAOD".format(dirT2))
    elif(year == 2025 and type == 1024):
        filesL   = findDIR("{0}/MuonEG+Run2025E-PromptReco-v1+NANOAOD".format(dirT2))
    elif(year == 2025 and type == 1025):
        filesL   = findDIR("{0}/MuonEG+Run2025F-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/MuonEG+Run2025F-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1026):
        filesL   = findDIR("{0}/MuonEG+Run2025G-PromptReco-v1+NANOAOD".format(dirT2))

    elif(year == 2025 and type == 1031):
        filesL   = findDIR("{0}/EGamma0+Run2025B-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2025B-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma2+Run2025B-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma3+Run2025B-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1032):
        filesL   = findDIR("{0}/EGamma0+Run2025C-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2025C-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma2+Run2025C-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma3+Run2025C-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma0+Run2025C-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma1+Run2025C-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma2+Run2025C-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma3+Run2025C-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1033):
        filesL   = findDIR("{0}/EGamma0+Run2025D-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2025D-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma2+Run2025D-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma3+Run2025D-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1034):
        filesL   = findDIR("{0}/EGamma0+Run2025E-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2025E-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma2+Run2025E-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma3+Run2025E-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1035):
        filesL   = findDIR("{0}/EGamma0+Run2025F-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2025F-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma2+Run2025F-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma3+Run2025F-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma0+Run2025F-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma1+Run2025F-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma2+Run2025F-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma3+Run2025F-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1036):
        filesL   = findDIR("{0}/EGamma0+Run2025G-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/EGamma1+Run2025G-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma2+Run2025G-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/EGamma3+Run2025G-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2025 and type == 1041):
        filesL   = findDIR("{0}/Muon0+Run2025B-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2025B-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1042):
        filesL   = findDIR("{0}/Muon0+Run2025C-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2025C-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon0+Run2025C-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon1+Run2025C-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1043):
        filesL   = findDIR("{0}/Muon0+Run2025D-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2025D-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1044):
        filesL   = findDIR("{0}/Muon0+Run2025E-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2025E-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1045):
        filesL   = findDIR("{0}/Muon0+Run2025F-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2025F-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon0+Run2025F-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/Muon1+Run2025F-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1046):
        filesL   = findDIR("{0}/Muon0+Run2025G-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/Muon1+Run2025G-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2025 and type == 1051):
        filesL   = findDIR("{0}/JetMET0+Run2025B-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2025B-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1052):
        filesL   = findDIR("{0}/JetMET0+Run2025C-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2025C-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET0+Run2025C-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET1+Run2025C-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1053):
        filesL   = findDIR("{0}/JetMET0+Run2025D-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2025D-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1054):
        filesL   = findDIR("{0}/JetMET0+Run2025E-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2025E-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1055):
        filesL   = findDIR("{0}/JetMET0+Run2025F-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2025F-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET0+Run2025F-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
        filesAux = findDIR("{0}/JetMET1+Run2025F-PromptReco-v2+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)
    elif(year == 2025 and type == 1056):
        filesL   = findDIR("{0}/JetMET0+Run2025G-PromptReco-v1+NANOAOD".format(dirT2))
        filesAux = findDIR("{0}/JetMET1+Run2025G-PromptReco-v1+NANOAOD".format(dirT2))
        for x in filesAux:
            filesL.push_back(x)

    elif(year == 2022 and type == 9999):
        filesL = findDIR("{0}".format(dirTest))

    files = ROOT.vector('string')()
    concatenate(files, filesL)

    return files

def SwitchSample(argument, skimType, year=None):

    # Normalize year format (handle era format like 20220, 20221, etc.)

    
    # Year-dependent base directory
    # You can customize this based on year (aligned with getDATAlist)
    if year is not None:
        # # Example: year-specific paths
        # # Uncomment and modify these to use year-dependent paths:
        # # if year == 2022:
        # #     dirT2 = "/path/to/2022/skims/" + skimType
        # # elif year == 2023:
        # #     dirT2 = "/path/to/2023/skims/" + skimType
        # # elif year == 2024:
        # #     dirT2 = "/path/to/2024/skims/" + skimType
        # # else:
        # #     dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
        
        # # Default: use same path structure as getDATAlist for consistency
        # # This ensures MC and data samples use the same base directory structure
        # dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
        if year == 20220:
            dirT2 = "/home/scratch/stqian/wz_guillermo_2022a_2022b_2022d_2023a/skims_2022a/" + skimType
        elif year == 20221:
            dirT2 = "/home/scratch/stqian/wz_guillermo_2022a_2022b_2022d_2023a/skims_2022b/" + skimType
        elif year == 20230:
            dirT2 = "/home/scratch/stqian/wz_guillermo_2022a_2022b_2022d_2023a/skims_2023a/" + skimType
        elif year == 20231:
            dirT2 = "/home/scratch/stqian/wz_guillermo/skims_2023b/" + skimType
        elif year == 20240:
            dirT2 = "/home/scratch/stqian/wz_guillermo/skims_2024a/" + skimType
        elif year == 20241:
            dirT2 = "/home/scratch/stqian/wz_guillermo/skims_2024b/" + skimType
        else:
            dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType
    else:
        # Default path when year not specified (backward compatibility)
        #dirT2 = "/scratch/submit/cms/ceballos/nanoaod/skims_submit/" + skimType
        dirT2 = "/ceph/submit/data/group/cms/store/user/ceballos/nanoaod/skims_submit/" + skimType

    if year is not None and year > 10000:
        year = year // 10
    # Print to stderr to avoid contaminating file lists when called from collect_files_for_job.py
    print("year: ", year, file=sys.stderr)
    print("dirT2: ", dirT2, file=sys.stderr)
    
    dirLocal = "/work/submit/mariadlf/Hrare/D01"

    ggWWXS_LO_MCFM = 0.0496265/(0.1086*0.1086)
    ggWWXS_LO_MADGRAPH = 3.51313
    ggWWXS_kFactor = 1.4

    switch = {
       100: (dirT2+"/DYto2L-2Jets_MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",19982.5*1000,plotCategory("kPlotDY")),
       101: (dirT2+"/DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",6345.99*1000,plotCategory("kPlotDY")),
       102: (dirT2+"/WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),
       103: (dirT2+"/WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",4.924*1.08*1000,plotCategory("kPlotWZ")),
       104: (dirT2+"/WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",7.568*1.08*1000,plotCategory("kPlotWZ")),
       105: (dirT2+"/ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",6.788*1.19*1000,plotCategory("kPlotZZ")),
       106: (dirT2+"/ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",1.031*1.16*1000,plotCategory("kPlotZZ")),
       107: (dirT2+"/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",1.390*1.19*1000,plotCategory("kPlotZZ")),
       108: (dirT2+"/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       109: (dirT2+"/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.950*923.6*0.1086*3*(1-0.1086*3)*2*1000,plotCategory("kPlotTT")),
       110: (dirT2+"/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5_ext1-v2+NANOAODSIM",1000000*0.950*923.6*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       111: (dirT2+"/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       112: (dirT2+"/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       113: (dirT2+"/WtoLNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",64481.58*1000,plotCategory("kPlotOther")),
       114: (dirT2+"/WWW_4F_TuneCP5_13p6TeV_amcatnlo-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.23280*1000,plotCategory("kPlotVVV")),
       115: (dirT2+"/WWZ_4F_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.18510*1000,plotCategory("kPlotVVV")),
       116: (dirT2+"/WZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.06206*1000,plotCategory("kPlotVVV")),
       117: (dirT2+"/ZZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.01591*1000,plotCategory("kPlotVVV")),
       118: (dirT2+"/WZGtoLNuZG_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.08425*1000,plotCategory("kPlotVVV")),
       119: (dirT2+"/TTWW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.0081651*1000,plotCategory("kPlotTVX")),
       120: (dirT2+"/TTZZ_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.0015617*1000,plotCategory("kPlotTVX")),
       121: (dirT2+"/GluGluHtoZZto4L_M-125_TuneCP5_13p6TeV_powheg2-JHUGenV752-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",52.230*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       122: (dirT2+"/VBFHto2Zto4L_M125_TuneCP5_13p6TeV_powheg-jhugenv752-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",4.0780*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       123: (dirT2+"/TTLL_MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.03949*1000,plotCategory("kPlotTVX")),
       124: (dirT2+"/TTLL_MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.08646*1000,plotCategory("kPlotTVX")),
       125: (dirT2+"/ggWWto2L2Nu_OS_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.24053*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       126: (dirT2+"/ggWWto2L2Nu_OS_PolarizationLT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       127: (dirT2+"/ggWWto2L2Nu_OS_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       128: (dirT2+"/ggWWto2L2Nu_OS_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",3.10724*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       129: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",124.18762*1000,plotCategory("kPlotVG")),
       130: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-50to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v3+NANOAODSIM",2.08977*1000,plotCategory("kPlotVG")),
       131: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.34767*1000,plotCategory("kPlotVG")),
       132: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.04734*1000,plotCategory("kPlotVG")),
       133: (dirT2+"/WGtoLNuG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",668.91538*1000,plotCategory("kPlotVG")),
       134: (dirT2+"/WGtoLNuG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",2.22141*1000,plotCategory("kPlotVG")),
       135: (dirT2+"/WGtoLNuG-1Jets_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",0.291367*1000,plotCategory("kPlotVG")),
       136: (dirT2+"/WWto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",1000000*(118.7*1.06-ggWWXS_LO_MCFM)*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       137: (dirT2+"/GluGluHto2Tau_M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",52.230*0.06272*1000,plotCategory("kPlotHiggs")),
       138: (dirT2+"/VBFHToTauTau_M125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",4.0780*0.06272*1000,plotCategory("kPlotHiggs")),
       139: (dirT2+"/DYGto2LG-1Jets_MLL-4to50_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",87.73210*1000,plotCategory("kPlotVG")),
       140: (dirT2+"/DYGto2LG-1Jets_MLL-4to50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.24095*1000,plotCategory("kPlotVG")),
       141: (dirT2+"/DYGto2LG-1Jets_MLL-4to50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.02228*1000,plotCategory("kPlotVG")),
       142: (dirT2+"/TbarWplus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",23.97*1000,plotCategory("kPlotTW")),
       143: (dirT2+"/TWminus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",23.97*1000,plotCategory("kPlotTW")),
       144: (dirT2+"/VH_HtoNonbb_M-125_TuneCP5_13p6TeV_amcatnloFXFX-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",(0.9439+1.4570)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       145: (dirT2+"/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",5034.65*1000,plotCategory("kPlotDY")),
       146: (dirT2+"/DYto2L-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",952.29*1000,plotCategory("kPlotDY")),
       147: (dirT2+"/DYto2L-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",359.05*1000,plotCategory("kPlotDY")),
       148: (dirT2+"/TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",0.2502*1000,plotCategory("kPlotTVX")),
       149: (dirT2+"/TZQB-Zto2L-4FS_MLL-30_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.07968*1.00*1000,plotCategory("kPlotTVX")),
       150: (dirT2+"/VBS-SSWW_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",0.002190*1000,plotCategory("kPlotEWKSSWW")),
       151: (dirT2+"/VBS-SSWW_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v3+NANOAODSIM",0.011700*1000,plotCategory("kPlotEWKSSWW")),
       152: (dirT2+"/VBS-SSWW_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",0.017635*1000,plotCategory("kPlotEWKSSWW")),
       153: (dirT2+"/GluGluHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",52.230*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       154: (dirT2+"/VBFHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",4.0780*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       155: (dirT2+"/TTHtoNon2B_M-125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v4+NANOAODSIM",0.5700*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       156: (dirT2+"/WGtoLNuG-1Jets_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",0.022322*1000,plotCategory("kPlotVG")),
       157: (dirT2+"/WGtoLNuG-1Jets_PTG-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v3+NANOAODSIM",0.004918*1000,plotCategory("kPlotVG")),
       158: (dirT2+"/WW_DoubleScattering_TuneCP5_13p6TeV_pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",2.14891*1000,plotCategory("kPlotOther")),
       159: (dirT2+"/GluGlutoContinto2Zto4E_TuneCP5_13p6TeV_mcfm-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       160: (dirT2+"/GluGlutoContinto2Zto4Mu_TuneCP5_13p6TeV_mcfm-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       161: (dirT2+"/GluGlutoContinto2Zto4Tau_TuneCP5_13p6TeV_mcfm-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       162: (dirT2+"/GluGluToContinto2Zto2E2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       163: (dirT2+"/GluGluToContinto2Zto2Mu2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       164: (dirT2+"/GluGlutoContinto2Zto2E2Mu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v1+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       165: (dirT2+"/GluGlutoContintoWWtoENuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       166: (dirT2+"/GluGlutoContintoWWtoENuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       167: (dirT2+"/GluGlutoContintoWWtoENuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       168: (dirT2+"/GluGlutoContintoWWtoMuNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       169: (dirT2+"/GluGlutoContintoWWtoMuNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       170: (dirT2+"/GluGlutoContintoWWtoMuNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       171: (dirT2+"/GluGlutoContintoWWtoTauNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       172: (dirT2+"/GluGlutoContintoWWtoTauNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       173: (dirT2+"/GluGlutoContintoWWtoTauNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       174: (dirT2+"/WWto2L2Nu-2Jets_OS_noTop_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM", 0.3301419*1000,plotCategory("kPlotqqWW")),
       175: (dirT2+"/WWto2L2Nu-2Jets_OS_noTop_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",2.6758028*1000,plotCategory("kPlotqqWW")),
       176: (dirT2+"/WWto2L2Nu-2Jets_SS_noTop_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v3+NANOAODSIM",         0.0295576*1000,plotCategory("kPlotEWKSSWW")),
       177: (dirT2+"/WWto2L2Nu-2Jets_SS_noTop_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",        0.0280798*1000,plotCategory("kPlotQCDSSWW")),
       178: (dirT2+"/WZto3LNu-2Jets_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",           0.0429366*1000,plotCategory("kPlotEWKWZ")),
       179: (dirT2+"/WZto3LNu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",          0.4958618*1000*0.60,plotCategory("kPlotWZ")),
       180: (dirT2+"/ZZto2L2Nu-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",                  0.0051721*1000,plotCategory("kPlotZZ")),
       181: (dirT2+"/ZZto2L2Nu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",                 0.0912313*1000,plotCategory("kPlotZZ")),
       182: (dirT2+"/ZZto4L-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",                     0.0011422*1000,plotCategory("kPlotZZ")),
       183: (dirT2+"/ZZto4L-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v3+NANOAODSIM",                    0.0202984*1000,plotCategory("kPlotZZ")),
       189: (dirT2+"/WpWpJJ_EWK-QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIM",                      0.0589674*1000,plotCategory("kPlotQCDSSWW")),

       200: (dirT2+"/DYto2L-2Jets_MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",19982.5*1000,plotCategory("kPlotDY")),
       201: (dirT2+"/DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",6345.99*1000,plotCategory("kPlotDY")),
       202: (dirT2+"/WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),
       203: (dirT2+"/WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",4.924*1.08*1000,plotCategory("kPlotWZ")),
       204: (dirT2+"/WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",7.568*1.08*1000,plotCategory("kPlotWZ")),
       205: (dirT2+"/ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",6.788*1.19*1000,plotCategory("kPlotZZ")),
       206: (dirT2+"/ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",1.031*1.16*1000,plotCategory("kPlotZZ")),
       207: (dirT2+"/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",1.390*1.19*1000,plotCategory("kPlotZZ")),
       208: (dirT2+"/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       209: (dirT2+"/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.950*923.6*0.1086*3*(1-0.1086*3)*2*1000,plotCategory("kPlotTT")),
       210: (dirT2+"/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",1000000*0.950*923.6*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       211: (dirT2+"/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       212: (dirT2+"/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       213: (dirT2+"/WtoLNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",64481.58*1000,plotCategory("kPlotOther")),
       214: (dirT2+"/WWW_4F_TuneCP5_13p6TeV_amcatnlo-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.23280*1000,plotCategory("kPlotVVV")),
       215: (dirT2+"/WWZ_4F_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.18510*1000,plotCategory("kPlotVVV")),
       216: (dirT2+"/WZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.06206*1000,plotCategory("kPlotVVV")),
       217: (dirT2+"/ZZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.01591*1000,plotCategory("kPlotVVV")),
       218: (dirT2+"/WZGtoLNuZG_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.08425*1000,plotCategory("kPlotVVV")),
       219: (dirT2+"/TTWW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.0081651*1000,plotCategory("kPlotTVX")),
       220: (dirT2+"/TTZZ_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",0.0015617*1000,plotCategory("kPlotTVX")),
       221: (dirT2+"/GluGluHtoZZto4L_M-125_TuneCP5_13p6TeV_powheg2-JHUGenV752-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",52.230*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       222: (dirT2+"/VBFHto2Zto4L_M125_TuneCP5_13p6TeV_powheg-jhugenv752-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",4.0780*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       223: (dirT2+"/TTLL_MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.03949*1000,plotCategory("kPlotTVX")),
       224: (dirT2+"/TTLL_MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.08646*1000,plotCategory("kPlotTVX")),
       225: (dirT2+"/ggWWto2L2Nu_OS_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.24053*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       226: (dirT2+"/ggWWto2L2Nu_OS_PolarizationLT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       227: (dirT2+"/ggWWto2L2Nu_OS_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       228: (dirT2+"/ggWWto2L2Nu_OS_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",3.10724*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       229: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",124.18762*1000,plotCategory("kPlotVG")),
       230: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-50to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v1+NANOAODSIM",2.08977*1000,plotCategory("kPlotVG")),
       231: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.34767*1000,plotCategory("kPlotVG")),
       232: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v4+NANOAODSIM",0.04734*1000,plotCategory("kPlotVG")),
       233: (dirT2+"/WGtoLNuG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",668.91538*1000,plotCategory("kPlotVG")),
       234: (dirT2+"/WGtoLNuG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",2.22141*1000,plotCategory("kPlotVG")),
       235: (dirT2+"/WGtoLNuG-1Jets_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",0.291367*1000,plotCategory("kPlotVG")),
       236: (dirT2+"/WWto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",1000000*(118.7*1.06-ggWWXS_LO_MCFM)*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       237: (dirT2+"/GluGluHto2Tau_M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",52.230*0.06272*1000,plotCategory("kPlotHiggs")),
       238: (dirT2+"/VBFHToTauTau_M125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",4.0780*0.06272*1000,plotCategory("kPlotHiggs")),
       239: (dirT2+"/DYGto2LG-1Jets_MLL-4to50_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",87.73210*1000,plotCategory("kPlotVG")),
       240: (dirT2+"/DYGto2LG-1Jets_MLL-4to50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.24095*1000,plotCategory("kPlotVG")),
       241: (dirT2+"/DYGto2LG-1Jets_MLL-4to50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.02228*1000,plotCategory("kPlotVG")),
       242: (dirT2+"/TbarWplus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",23.97*1000,plotCategory("kPlotTW")),
       243: (dirT2+"/TWminus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",23.97*1000,plotCategory("kPlotTW")),
       244: (dirT2+"/VH_HtoNonbb_M-125_TuneCP5_13p6TeV_amcatnloFXFX-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v1+NANOAODSIM",(0.9439+1.4570)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       245: (dirT2+"/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",5034.65*1000,plotCategory("kPlotDY")),
       246: (dirT2+"/DYto2L-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",952.29*1000,plotCategory("kPlotDY")),
       247: (dirT2+"/DYto2L-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",359.05*1000,plotCategory("kPlotDY")),
       248: (dirT2+"/TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v4+NANOAODSIM",0.2502*1000,plotCategory("kPlotTVX")),
       249: (dirT2+"/TZQB-Zto2L-4FS_MLL-30_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.07968*1.00*1000,plotCategory("kPlotTVX")),
       250: (dirT2+"/VBS-SSWW_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",0.002190*1000,plotCategory("kPlotEWKSSWW")),
       251: (dirT2+"/VBS-SSWW_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v1+NANOAODSIM",0.011700*1000,plotCategory("kPlotEWKSSWW")),
       252: (dirT2+"/VBS-SSWW_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",0.017635*1000,plotCategory("kPlotEWKSSWW")),
       253: (dirT2+"/GluGluHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",52.230*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       254: (dirT2+"/VBFHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",4.0780*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       255: (dirT2+"/TTHtoNon2B_M-125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.5700*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       256: (dirT2+"/WGtoLNuG-1Jets_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",0.022322*1000,plotCategory("kPlotVG")),
       257: (dirT2+"/WGtoLNuG-1Jets_PTG-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",0.004918*1000,plotCategory("kPlotVG")),
       258: (dirT2+"/WW_DoubleScattering_TuneCP5_13p6TeV_pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",2.14891*1000,plotCategory("kPlotOther")),
       259: (dirT2+"/GluGlutoContinto2Zto4E_TuneCP5_13p6TeV_mcfm-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       260: (dirT2+"/GluGlutoContinto2Zto4Mu_TuneCP5_13p6TeV_mcfm-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       261: (dirT2+"/GluGlutoContinto2Zto4Tau_TuneCP5_13p6TeV_mcfm-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       262: (dirT2+"/GluGluToContinto2Zto2E2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v4+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       263: (dirT2+"/GluGluToContinto2Zto2Mu2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v4+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       264: (dirT2+"/GluGluToContinto2Zto2E2Mu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       265: (dirT2+"/GluGlutoContintoWWtoENuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       266: (dirT2+"/GluGlutoContintoWWtoENuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       267: (dirT2+"/GluGlutoContintoWWtoENuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       268: (dirT2+"/GluGlutoContintoWWtoMuNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       269: (dirT2+"/GluGlutoContintoWWtoMuNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       270: (dirT2+"/GluGlutoContintoWWtoMuNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       271: (dirT2+"/GluGlutoContintoWWtoTauNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       272: (dirT2+"/GluGlutoContintoWWtoTauNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       273: (dirT2+"/GluGlutoContintoWWtoTauNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       274: (dirT2+"/WWto2L2Nu-2Jets_OS_noTop_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM", 0.3301419*1000,plotCategory("kPlotqqWW")),
       275: (dirT2+"/WWto2L2Nu-2Jets_OS_noTop_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",2.6758028*1000,plotCategory("kPlotqqWW")),
       276: (dirT2+"/WWto2L2Nu-2Jets_SS_noTop_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",         0.0295576*1000,plotCategory("kPlotEWKSSWW")),
       277: (dirT2+"/WWto2L2Nu-2Jets_SS_noTop_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",        0.0280798*1000,plotCategory("kPlotQCDSSWW")),
       278: (dirT2+"/WZto3LNu-2Jets_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",           0.0429366*1000,plotCategory("kPlotEWKWZ")),
       279: (dirT2+"/WZto3LNu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",          0.4958618*1000*0.60,plotCategory("kPlotWZ")),
       280: (dirT2+"/ZZto2L2Nu-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",                  0.0051721*1000,plotCategory("kPlotZZ")),
       281: (dirT2+"/ZZto2L2Nu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",                 0.0912313*1000,plotCategory("kPlotZZ")),
       282: (dirT2+"/ZZto4L-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",                     0.0011422*1000,plotCategory("kPlotZZ")),
       283: (dirT2+"/ZZto4L-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v3+NANOAODSIM",                    0.0202984*1000,plotCategory("kPlotZZ")),
       289: (dirT2+"/WpWpJJ_EWK-QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIM",                      0.0589674*1000,plotCategory("kPlotQCDSSWW")),

       300: (dirT2+"/DYto2L-2Jets_MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14_ext1-v3+NANOAODSIM",19982.5*1000,plotCategory("kPlotDY")),
       301: (dirT2+"/DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v1+NANOAODSIM",6345.99*1000,plotCategory("kPlotDY")),
       302: (dirT2+"/WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v4+NANOAODSIM",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),
       303: (dirT2+"/WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",4.924*1.08*1000,plotCategory("kPlotWZ")),
       304: (dirT2+"/WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",7.568*1.08*1000,plotCategory("kPlotWZ")),
       305: (dirT2+"/ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v1+NANOAODSIM",6.788*1.19*1000,plotCategory("kPlotZZ")),
       306: (dirT2+"/ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v1+NANOAODSIM",1.031*1.16*1000,plotCategory("kPlotZZ")),
       307: (dirT2+"/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",1.390*1.19*1000,plotCategory("kPlotZZ")),
       308: (dirT2+"/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       309: (dirT2+"/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.950*923.6*0.1086*3*(1-0.1086*3)*2*1000,plotCategory("kPlotTT")),
       310: (dirT2+"/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-JMENano12p5_132X_mcRun3_2023_realistic_v5-v1+NANOAODSIM",1000000*0.950*923.6*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       311: (dirT2+"/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v4+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       312: (dirT2+"/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       313: (dirT2+"/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",64481.58*1000,plotCategory("kPlotOther")),
       314: (dirT2+"/WWW_4F_TuneCP5_13p6TeV_amcatnlo-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.23280*1000,plotCategory("kPlotVVV")),
       315: (dirT2+"/WWZ_4F_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.18510*1000,plotCategory("kPlotVVV")),
       316: (dirT2+"/WZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.06206*1000,plotCategory("kPlotVVV")),
       317: (dirT2+"/ZZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.01591*1000,plotCategory("kPlotVVV")),
       318: (dirT2+"/WZGtoLNuZG_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.08425*1000,plotCategory("kPlotVVV")),
       319: (dirT2+"/TTWW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.0081651*1000,plotCategory("kPlotTVX")),
       320: (dirT2+"/TTZZ_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v4+NANOAODSIM",0.0015617*1000,plotCategory("kPlotTVX")),
       321: (dirT2+"/GluGluHtoZZto4L_M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",52.230*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       322: (dirT2+"/VBFHto2Zto4L_M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",4.0780*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       323: (dirT2+"/TTLL_MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.03949*1000,plotCategory("kPlotTVX")),
       324: (dirT2+"/TTLL_MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.08646*1000,plotCategory("kPlotTVX")),
       325: (dirT2+"/ggWWto2L2Nu_OS_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIMFAKE",0.24053*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       326: (dirT2+"/ggWWto2L2Nu_OS_PolarizationLT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIMFAKE",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       327: (dirT2+"/ggWWto2L2Nu_OS_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIMFAKE",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       328: (dirT2+"/ggWWto2L2Nu_OS_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIMFAKE",3.10724*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       329: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v4+NANOAODSIM",126.469425988806051*1000,plotCategory("kPlotVG")),
       330: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.347454856033058*1000,plotCategory("kPlotVG")),
       331: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v4+NANOAODSIM",0.043623155782532*1000,plotCategory("kPlotVG")),
       332: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v4+NANOAODSIM",0.003152651247494*1000,plotCategory("kPlotVG")),
       333: (dirT2+"/WGtoLNuG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",668.91538*1000,plotCategory("kPlotVG")),
       334: (dirT2+"/WGtoLNuG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",2.22141*1000,plotCategory("kPlotVG")),
       335: (dirT2+"/WGtoLNuG-1Jets_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",0.291367*1000,plotCategory("kPlotVG")),
       336: (dirT2+"/WWto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v4+NANOAODSIM",1000000*(118.7*1.06-ggWWXS_LO_MCFM)*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       337: (dirT2+"/GluGluHto2Tau_M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",52.230*0.06272*1000,plotCategory("kPlotHiggs")),
       338: (dirT2+"/VBFHToTauTau_M125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",4.0780*0.06272*1000,plotCategory("kPlotHiggs")),
       339: (dirT2+"/DYGto2LG-1Jets_MLL-4to50_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIMFAKE",87.73210*1000,plotCategory("kPlotVG")),
       340: (dirT2+"/DYGto2LG-1Jets_MLL-4to50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIMFAKE",0.24095*1000,plotCategory("kPlotVG")),
       341: (dirT2+"/DYGto2LG-1Jets_MLL-4to50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIMFAKE",0.02228*1000,plotCategory("kPlotVG")),
       342: (dirT2+"/TbarWplus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIMFAKE",23.97*1000,plotCategory("kPlotTW")),
       343: (dirT2+"/TWminus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2+NANOAODSIMFAKE",23.97*1000,plotCategory("kPlotTW")),
       344: (dirT2+"/VH_HtoNonbb_M-125_TuneCP5_13p6TeV_amcatnloFXFX-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.9439+1.4570)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       345: (dirT2+"/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",5034.65*1000,plotCategory("kPlotDY")),
       346: (dirT2+"/DYto2L-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",952.29*1000,plotCategory("kPlotDY")),
       347: (dirT2+"/DYto2L-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",359.05*1000,plotCategory("kPlotDY")),
       348: (dirT2+"/TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.2502*1000,plotCategory("kPlotTVX")),
       349: (dirT2+"/TZQB-Zto2L-4FS_MLL-30_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.07968*1.00*1000,plotCategory("kPlotTVX")),
       350: (dirT2+"/VBS-SSWW_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.002190*1000,plotCategory("kPlotEWKSSWW")),
       351: (dirT2+"/VBS-SSWW_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.011700*1000,plotCategory("kPlotEWKSSWW")),
       352: (dirT2+"/VBS-SSWW_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.017635*1000,plotCategory("kPlotEWKSSWW")),
       353: (dirT2+"/GluGluHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",52.230*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       354: (dirT2+"/VBFHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",4.0780*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       355: (dirT2+"/TTHtoNon2B_M-125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v2+NANOAODSIM",0.5700*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       356: (dirT2+"/WGtoLNuG-1Jets_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",0.022322*1000,plotCategory("kPlotVG")),
       357: (dirT2+"/WGtoLNuG-1Jets_PTG-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v14-v3+NANOAODSIM",0.004918*1000,plotCategory("kPlotVG")),
       358: (dirT2+"/WW_DoubleScattering_TuneCP5_13p6TeV_pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",2.14891*1000,plotCategory("kPlotOther")),
       359: (dirT2+"/GluGlutoContinto2Zto4E_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       360: (dirT2+"/GluGlutoContinto2Zto4Mu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       361: (dirT2+"/GluGlutoContinto2Zto4Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       362: (dirT2+"/GluGlutoContinto2Zto2E2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       363: (dirT2+"/GluGlutoContinto2Zto2Mu2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v3+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       364: (dirT2+"/GluGluToContinto2Zto2E2Mu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       365: (dirT2+"/GluGlutoContintoWWtoENuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       366: (dirT2+"/GluGlutoContintoWWtoENuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       367: (dirT2+"/GluGlutoContintoWWtoENuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       368: (dirT2+"/GluGlutoContintoWWtoMuNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       369: (dirT2+"/GluGlutoContintoWWtoMuNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       370: (dirT2+"/GluGlutoContintoWWtoMuNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       371: (dirT2+"/GluGlutoContintoWWtoTauNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       372: (dirT2+"/GluGlutoContintoWWtoTauNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       373: (dirT2+"/GluGlutoContintoWWtoTauNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       374: (dirT2+"/WWto2L2Nu-2Jets_OS_noTop_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM", 0.3301419*1000,plotCategory("kPlotqqWW")),
       375: (dirT2+"/WWto2L2Nu-2Jets_OS_noTop_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",2.6758028*1000,plotCategory("kPlotqqWW")),
       376: (dirT2+"/WWto2L2Nu-2Jets_SS_noTop_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",         0.0295576*1000,plotCategory("kPlotEWKSSWW")),
       377: (dirT2+"/WWto2L2Nu-2Jets_SS_noTop_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",        0.0280798*1000,plotCategory("kPlotQCDSSWW")),
       378: (dirT2+"/WZto3LNu-2Jets_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",           0.0429366*1000,plotCategory("kPlotEWKWZ")),
       379: (dirT2+"/WZto3LNu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v1+NANOAODSIM",          0.4958618*1000*0.60,plotCategory("kPlotWZ")),
       380: (dirT2+"/ZZto2L2Nu-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",                  0.0051721*1000,plotCategory("kPlotZZ")),
       381: (dirT2+"/ZZto2L2Nu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",                 0.0912313*1000,plotCategory("kPlotZZ")),
       382: (dirT2+"/ZZto4L-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",                     0.0011422*1000,plotCategory("kPlotZZ")),
       383: (dirT2+"/ZZto4L-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",                    0.0202984*1000,plotCategory("kPlotZZ")),
       389: (dirT2+"/WpWpJJ_EWK-QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23NanoAODv12-130X_mcRun3_2023_realistic_v15-v2+NANOAODSIM",                      0.0589674*1000,plotCategory("kPlotQCDSSWW")),

       400: (dirT2+"/DYto2L-2Jets_MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2_ext1-v3+NANOAODSIM",19982.5*1000,plotCategory("kPlotDY")),
       401: (dirT2+"/DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",6345.99*1000,plotCategory("kPlotDY")),
       402: (dirT2+"/WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),
       403: (dirT2+"/WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",4.924*1.08*1000,plotCategory("kPlotWZ")),
       404: (dirT2+"/WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",7.568*1.08*1000,plotCategory("kPlotWZ")),
       405: (dirT2+"/ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",6.788*1.19*1000,plotCategory("kPlotZZ")),
       406: (dirT2+"/ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v1+NANOAODSIM",1.031*1.16*1000,plotCategory("kPlotZZ")),
       407: (dirT2+"/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",1.390*1.19*1000,plotCategory("kPlotZZ")),
       408: (dirT2+"/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       409: (dirT2+"/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.950*923.6*0.1086*3*(1-0.1086*3)*2*1000,plotCategory("kPlotTT")),
       410: (dirT2+"/TTto4Q_TuneCP5Up_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",1000000*0.950*923.6*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       411: (dirT2+"/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       412: (dirT2+"/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       413: (dirT2+"/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",64481.58*1000,plotCategory("kPlotOther")),
       414: (dirT2+"/WWW_4F_TuneCP5_13p6TeV_amcatnlo-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",0.23280*1000,plotCategory("kPlotVVV")),
       415: (dirT2+"/WWZ_4F_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.18510*1000,plotCategory("kPlotVVV")),
       416: (dirT2+"/WZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",0.06206*1000,plotCategory("kPlotVVV")),
       417: (dirT2+"/ZZZ_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",0.01591*1000,plotCategory("kPlotVVV")),
       418: (dirT2+"/WZGtoLNuZG_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.08425*1000,plotCategory("kPlotVVV")),
       419: (dirT2+"/TTWW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.0081651*1000,plotCategory("kPlotTVX")),
       420: (dirT2+"/TTZZ_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.0015617*1000,plotCategory("kPlotTVX")),
       421: (dirT2+"/GluGluHtoZZto4L_M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",52.230*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       422: (dirT2+"/VBFHto2Zto4L_M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",4.0780*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       423: (dirT2+"/TTLL_MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.03949*1000,plotCategory("kPlotTVX")),
       424: (dirT2+"/TTLL_MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.08646*1000,plotCategory("kPlotTVX")),
       425: (dirT2+"/ggWWto2L2Nu_OS_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIMFAKE",0.24053*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       426: (dirT2+"/ggWWto2L2Nu_OS_PolarizationLT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIMFAKE",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       427: (dirT2+"/ggWWto2L2Nu_OS_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIMFAKE",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       428: (dirT2+"/ggWWto2L2Nu_OS_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIMFAKE",3.10724*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*1.4*1000,plotCategory("kPlotggWW")),
       429: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",126.469425988806051*1000,plotCategory("kPlotVG")),
       430: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v3+NANOAODSIM",0.347454856033058*1000,plotCategory("kPlotVG")),
       431: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.043623155782532*1000,plotCategory("kPlotVG")),
       432: (dirT2+"/DYGto2LG-1Jets_MLL-50_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.003152651247494*1000,plotCategory("kPlotVG")),
       433: (dirT2+"/WGtoLNuG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",668.91538*1000,plotCategory("kPlotVG")),
       434: (dirT2+"/WGtoLNuG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",2.22141*1000,plotCategory("kPlotVG")),
       435: (dirT2+"/WGtoLNuG-1Jets_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.291367*1000,plotCategory("kPlotVG")),
       436: (dirT2+"/WWto4Q_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",1000000*(118.7*1.06-ggWWXS_LO_MCFM)*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       437: (dirT2+"/GluGluHToTauTau_M-125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",52.230*0.06272*1000,plotCategory("kPlotHiggs")),
       438: (dirT2+"/VBFHToTauTau_M125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",4.0780*0.06272*1000,plotCategory("kPlotHiggs")),
       439: (dirT2+"/DYGto2LG-1Jets_MLL-4to50_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIMFAKE",87.73210*1000,plotCategory("kPlotVG")),
       440: (dirT2+"/DYGto2LG-1Jets_MLL-4to50_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIMFAKE",0.24095*1000,plotCategory("kPlotVG")),
       441: (dirT2+"/DYGto2LG-1Jets_MLL-4to50_PTG-200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIMFAKE",0.02228*1000,plotCategory("kPlotVG")),
       442: (dirT2+"/TbarWplus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIMFAKE",23.97*1000,plotCategory("kPlotTW")),
       443: (dirT2+"/TWminus_DR_AtLeastOneLepton_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer22EENanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v2+NANOAODSIMFAKE",23.97*1000,plotCategory("kPlotTW")),
       444: (dirT2+"/VH_HtoNonbb_M-125_TuneCP5_13p6TeV_amcatnloFXFX-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.9439+1.4570)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       445: (dirT2+"/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",5034.65*1000,plotCategory("kPlotDY")),
       446: (dirT2+"/DYto2L-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",952.29*1000,plotCategory("kPlotDY")),
       447: (dirT2+"/DYto2L-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",359.05*1000,plotCategory("kPlotDY")),
       448: (dirT2+"/TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.2502*1000,plotCategory("kPlotTVX")),
       449: (dirT2+"/TZQB-Zto2L-4FS_MLL-30_TuneCP5_13p6TeV_amcatnlo-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v3+NANOAODSIM",0.07968*1.00*1000,plotCategory("kPlotTVX")),
       450: (dirT2+"/VBS-SSWW_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.002190*1000,plotCategory("kPlotEWKSSWW")),
       451: (dirT2+"/VBS-SSWW_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.011700*1000,plotCategory("kPlotEWKSSWW")),
       452: (dirT2+"/VBS-SSWW_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.017635*1000,plotCategory("kPlotEWKSSWW")),
       453: (dirT2+"/GluGluHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",52.230*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       454: (dirT2+"/VBFHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",4.0780*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       455: (dirT2+"/TTHtoNon2B_M-125_TuneCP5_13p6TeV_powheg-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2+NANOAODSIM",0.5700*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       456: (dirT2+"/WGtoLNuG-1Jets_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.022322*1000,plotCategory("kPlotVG")),
       457: (dirT2+"/WGtoLNuG-1Jets_PTG-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIM",0.004918*1000,plotCategory("kPlotVG")),
       458: (dirT2+"/WW_DoubleScattering_TuneCP5_13p6TeV_pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",2.14891*1000,plotCategory("kPlotOther")),
       459: (dirT2+"/GluGlutoContinto2Zto4E_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       460: (dirT2+"/GluGlutoContinto2Zto4Mu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       461: (dirT2+"/GluGlutoContinto2Zto4Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       462: (dirT2+"/GluGlutoContinto2Zto2E2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       463: (dirT2+"/GluGlutoContinto2Zto2Mu2Tau_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       464: (dirT2+"/GluGluToContinto2Zto2E2Mu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       465: (dirT2+"/GluGlutoContintoWWtoENuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       466: (dirT2+"/GluGlutoContintoWWtoENuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       467: (dirT2+"/GluGlutoContintoWWtoENuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       468: (dirT2+"/GluGlutoContintoWWtoMuNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       469: (dirT2+"/GluGlutoContintoWWtoMuNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       470: (dirT2+"/GluGlutoContintoWWtoMuNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       471: (dirT2+"/GluGlutoContintoWWtoTauNuENu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       472: (dirT2+"/GluGlutoContintoWWtoTauNuMuNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       473: (dirT2+"/GluGlutoContintoWWtoTauNuTauNu_TuneCP5_13p6TeV_mcfm701-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       474: (dirT2+"/WWto2L2Nu-2Jets_OS_noTop_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v1+NANOAODSIM", 0.3301419*1000,plotCategory("kPlotqqWW")),
       475: (dirT2+"/WWto2L2Nu-2Jets_OS_noTop_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",2.6758028*1000,plotCategory("kPlotqqWW")),
       476: (dirT2+"/WWto2L2Nu-2Jets_SS_noTop_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",         0.0295576*1000,plotCategory("kPlotEWKSSWW")),
       477: (dirT2+"/WWto2L2Nu-2Jets_SS_noTop_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",        0.0280798*1000,plotCategory("kPlotQCDSSWW")),
       478: (dirT2+"/WZto3LNu-2Jets_EW_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",           0.0429366*1000,plotCategory("kPlotEWKWZ")),
       479: (dirT2+"/WZto3LNu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",          0.4958618*1000*0.60,plotCategory("kPlotWZ")),
       480: (dirT2+"/ZZto2L2Nu-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",                  0.0051721*1000,plotCategory("kPlotZZ")),
       481: (dirT2+"/ZZto2L2Nu-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",                 0.0912313*1000,plotCategory("kPlotZZ")),
       482: (dirT2+"/ZZto4L-2Jets_EW_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",                     0.0011422*1000,plotCategory("kPlotZZ")),
       483: (dirT2+"/ZZto4L-2Jets_QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",                    0.0202984*1000,plotCategory("kPlotZZ")),
       489: (dirT2+"/WpWpJJ_EWK-QCD_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIM",                      0.0589674*1000,plotCategory("kPlotQCDSSWW")),

       500: (dirT2+"/DYto2E_Bin-MLL-10to50_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",19982.5*1000/3.,plotCategory("kPlotDY")),
       501: (dirT2+"/DYto2E-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v4+NANOAODSIM",6345.99*1000/3.,plotCategory("kPlotDY")),
       502: (dirT2+"/WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),
       503: (dirT2+"/WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.924*1.08*1000,plotCategory("kPlotWZ")),
       504: (dirT2+"/WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",7.568*1.08*1000,plotCategory("kPlotWZ")),
       505: (dirT2+"/ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",6.788*1.19*1000,plotCategory("kPlotZZ")),
       506: (dirT2+"/ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",1.031*1.16*1000,plotCategory("kPlotZZ")),
       507: (dirT2+"/ZZto4L_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",1.390*1.19*1000,plotCategory("kPlotZZ")),
       508: (dirT2+"/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3+NANOAODSIM",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       509: (dirT2+"/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.950*923.6*0.1086*3*(1-0.1086*3)*2*1000,plotCategory("kPlotTT")),
       510: (dirT2+"/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",1000000*0.950*923.6*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       511: (dirT2+"/TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       512: (dirT2+"/TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.67*1000,plotCategory("kPlotTW")),
       513: (dirT2+"/WtoENu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3+NANOAODSIM",64481.58*1000/3.,plotCategory("kPlotOther")),
       514: (dirT2+"/WWW-4F_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.23280*1000,plotCategory("kPlotVVV")),
       515: (dirT2+"/WWZ-4F_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.18510*1000,plotCategory("kPlotVVV")),
       516: (dirT2+"/WZZ-5F_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.06206*1000,plotCategory("kPlotVVV")),
       517: (dirT2+"/ZZZ-5F_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.01591*1000,plotCategory("kPlotVVV")),
       518: (dirT2+"/WZGtoLNuZG_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.08425*1000,plotCategory("kPlotVVV")),
       519: (dirT2+"/TTWW_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0081651*1000,plotCategory("kPlotTVX")),
       520: (dirT2+"/TTWZ_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0027199*1000,plotCategory("kPlotTVX")),
       521: (dirT2+"/GluGluHto2Zto4L_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-jhugen-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",52.230*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       522: (dirT2+"/VBFH-Hto2Zto4L_Par-M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.0780*0.02619*0.101*0.101*1000,plotCategory("kPlotHiggs")),
       523: (dirT2+"/TTLL_Bin-MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.03949*1000,plotCategory("kPlotTVX")),
       524: (dirT2+"/TTLL_Bin-MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.08646*1000,plotCategory("kPlotTVX")),
       525: (dirT2+"/DYto2Mu_Bin-MLL-10to50_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",19982.5*1000/3.,plotCategory("kPlotDY")),
       526: (dirT2+"/DYto2Mu-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v6+NANOAODSIM",6345.99*1000/3.,plotCategory("kPlotDY")),
       527: (dirT2+"/DYto2Tau_Bin-MLL-10to50_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",19982.5*1000/3.,plotCategory("kPlotDY")),
       528: (dirT2+"/DYto2Tau-2Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v5+NANOAODSIM",6345.99*1000/3.,plotCategory("kPlotDY")),
       529: (dirT2+"/DYGto2LG-1Jets_Bin-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",126.86326*1000,plotCategory("kPlotVG")),
       530: (dirT2+"/DUMMY",0.347454856033058*1000,plotCategory("kPlotVG")),
       531: (dirT2+"/DUMMY",0.043623155782532*1000,plotCategory("kPlotVG")),
       532: (dirT2+"/EWK-ZG2JtoG2L2J_Bin-MLL-50-MJJ-120_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.113109*1000,plotCategory("kPlotVG")),
       533: (dirT2+"/WGtoLNuG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIMFAKE",668.91538*1000,plotCategory("kPlotVG")),
       534: (dirT2+"/WGtoLNuG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIMFAKE",2.22141*1000,plotCategory("kPlotVG")),
       535: (dirT2+"/WGtoLNuG-1Jets_PTG-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIMFAKE",0.291367*1000,plotCategory("kPlotVG")),
       536: (dirT2+"/WWto4Q_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",1000000*(118.7*1.06-ggWWXS_LO_MCFM)*(1-0.1086*3)*(1-0.1086*3)*1000,plotCategory("kPlotNonPrompt")),
       537: (dirT2+"/GluGluH-HTo2Tau_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",52.230*0.06272*1000,plotCategory("kPlotHiggs")),
       538: (dirT2+"/VBFH-HTo2Tau_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.0780*0.06272*1000,plotCategory("kPlotHiggs")),
       539: (dirT2+"/DYGto2LG-1Jets_Bin-MLL-4to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",88.11067*1000,plotCategory("kPlotVG")),
       540: (dirT2+"/DUMMY",0.24095*1000,plotCategory("kPlotVG")),
       541: (dirT2+"/DUMMY",0.02228*1000,plotCategory("kPlotVG")),
       542: (dirT2+"/WtoMuNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3+NANOAODSIM",64481.58*1000/3.,plotCategory("kPlotOther")),
       543: (dirT2+"/WtoTauNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v3+NANOAODSIM",64481.58*1000/3.,plotCategory("kPlotOther")),
       544: (dirT2+"/VH_HtoNonbb_M-125_TuneCP5_13p6TeV_amcatnloFXFX-madspin-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIMFAKE",(0.9439+1.4570)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       545: (dirT2+"/DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIMFAKE",5034.65*1000,plotCategory("kPlotDY")),
       546: (dirT2+"/DYto2L-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIMFAKE",952.29*1000,plotCategory("kPlotDY")),
       547: (dirT2+"/DYto2L-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIMFAKE",359.05*1000,plotCategory("kPlotDY")),
       548: (dirT2+"/TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.2502*1000,plotCategory("kPlotTVX")),
       549: (dirT2+"/TZQB-Zto2L-4FS_Bin-MLL-30_TuneCP5_13p6TeV_amcatnlo-pythia8+RunIII2024Summer24NanoAODv15-Madgraph_2_6_5_150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.07968*1.00*1000,plotCategory("kPlotTVX")),
       550: (dirT2+"/VBS-SSWW_PolarizationLL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIMFAKE",0.002190*1000,plotCategory("kPlotEWKSSWW")),
       551: (dirT2+"/VBS-SSWW_PolarizationTL_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIMFAKE",0.011700*1000,plotCategory("kPlotEWKSSWW")),
       552: (dirT2+"/VBS-SSWW_PolarizationTT_TuneCP5_13p6TeV_madgraph-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v6-v2+NANOAODSIMFAKE",0.017635*1000,plotCategory("kPlotEWKSSWW")),
       553: (dirT2+"/GluGluHto2Wto2L2Nu_Par-M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",52.230*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       554: (dirT2+"/VBFHto2Wto2L2Nu_Par-M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",4.0780*0.2137*0.1086*0.1086*9*1000,plotCategory("kPlotHiggs")),
       555: (dirT2+"/TTH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5700*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       556: (dirT2+"/WGtoLNuG-1Jets_PTG-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIMFAKE",0.022322*1000,plotCategory("kPlotVG")),
       557: (dirT2+"/WGtoLNuG-1Jets_PTG-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v3+NANOAODSIMFAKE",0.004918*1000,plotCategory("kPlotVG")),
       558: (dirT2+"/WW-DPS_TuneCP5_13p6TeV_pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",2.14891*1000,plotCategory("kPlotOther")),
       559: (dirT2+"/GluGlu2Zto4E_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       560: (dirT2+"/GluGlu2Zto4Mu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       561: (dirT2+"/GluGlu2Zto4Tau_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0061150*1000,plotCategory("kPlotZZ")),
       562: (dirT2+"/GluGlu2Zto2E2Tau_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       563: (dirT2+"/GluGlu2Zto2Mu2Tau_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       564: (dirT2+"/GluGlu2Zto2E2Mu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.0061150*1000,plotCategory("kPlotZZ")),
       565: (dirT2+"/GluGluWWto2E2Nu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       566: (dirT2+"/GluGluWWtoENuMuNu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       567: (dirT2+"/GluGluWWtoENuTauNu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       568: (dirT2+"/GluGluWWtoMuNuENu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       569: (dirT2+"/GluGluWWto2Mu2Nu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       570: (dirT2+"/GluGluWWtoMuNuTauNu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       571: (dirT2+"/GluGluWWtoTauNuENu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       572: (dirT2+"/GluGluWWtoTauNuMuNu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       573: (dirT2+"/GluGluWWto2Tau2Nu_TuneCP5_13p6TeV_mcfm-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.1086*0.1086)*ggWWXS_LO_MCFM*1.4*1000,plotCategory("kPlotggWW")),
       574: (dirT2+"/WWJJto2L2Nu-OS-noTop-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                         0.3301419*1000,plotCategory("kPlotqqWW")),
       575: (dirT2+"/WWJJto2L2Nu-OS-noTop-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                         2.6758028*1000,plotCategory("kPlotqqWW")),
       576: (dirT2+"/WWJJto2L2Nu-SS-noTop-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                         0.0295576*1000,plotCategory("kPlotEWKSSWW")),
       577: (dirT2+"/WWJJto2L2Nu-SS-noTop-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                         0.0280798*1000,plotCategory("kPlotQCDSSWW")),
       578: (dirT2+"/WZJJto3LNu-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                   0.0429366*1000,plotCategory("kPlotEWKWZ")),
       579: (dirT2+"/WZJJto3LNu-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                   0.4958618*1000*0.60,plotCategory("kPlotWZ")),
       580: (dirT2+"/ZZJJto2L2Nu-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                  0.0051721*1000,plotCategory("kPlotZZ")),
       581: (dirT2+"/ZZJJto2L2Nu-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                  0.0912313*1000,plotCategory("kPlotZZ")),
       582: (dirT2+"/ZZJJto4L-EWK_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                     0.0011422*1000,plotCategory("kPlotZZ")),
       583: (dirT2+"/ZZJJto4L-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                     0.0202984*1000,plotCategory("kPlotZZ")),
       584: (dirT2+"/WpWpJJ-EWK_TuneCP5_13p6TeV-powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0295576*1000,plotCategory("kPlotEWKSSWW")),
       585: (dirT2+"/WmWmJJ-EWK_TuneCP5_13p6TeV-powheg-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",0.5*0.0295576*1000,plotCategory("kPlotEWKSSWW")),
       586: (dirT2+"/ZH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(0.9439)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       587: (dirT2+"/WplusH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(1.4570*0.608)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       588: (dirT2+"/WminusH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_amcatnloFXFX-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",(1.4570*0.392)*(1-0.577)*1000,plotCategory("kPlotHiggs")),
       589: (dirT2+"/WpWpJJ_EWK-QCD_TuneCP5_13p6TeV_madgraph-pythia8+RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2+NANOAODSIM",                                   0.0589674*1000,plotCategory("kPlotQCDSSWW")),

       900:(dirLocal+"/2018/vbf-hrhogamma-powheg+NANOAOD_01",1.0*1000,plotCategory("kPlotBSM")),

       901:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/DY_MLM_2022_preEE",6345.99*1000,plotCategory("kPlotDY")),
       902:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/DY_2022_preEE",6345.99*1000,plotCategory("kPlotDY")),
       903:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/DY_2022_postEE",6345.99*1000,plotCategory("kPlotDY")),
       904:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/DY_2023_partA",6345.99*1000,plotCategory("kPlotDY")),
       905:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/DY_2023_partB",6345.99*1000,plotCategory("kPlotDY")),

       906:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/TTto2L2Nu_2022_postEE",0.950*923.6*0.1086*0.1086*9*1000,plotCategory("kPlotTT")),
       907:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/TWminusto2L2Nu_2022_postEE",23.97*1000*2.0,plotCategory("kPlotTW")),

       960:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/qqWW_2018",(118.7-3.974)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),

       961:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/qqWW_2022_postEE",(118.7*1.06-ggWWXS_LO_MCFM)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),

       962:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoENuENu_postEE"    ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       963:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoENuMuNu_postEE"   ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       964:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoENuTauNu_postEE"  ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       965:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoMuNuENu_postEE"   ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       966:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoMuNuMuNu_postEE"  ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       967:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoMuNuTauNu_postEE" ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       968:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoTauNuENu_postEE"  ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       969:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoTauNuMuNu_postEE" ,(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       970:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/GluGlutoContintoWWtoTauNuTauNu_postEE",(0.1086*0.1086)*ggWWXS_LO_MCFM*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),

       971:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/ggWWto2L2Nu_OS_PolarizationLL_postEE",0.24053*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       972:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/ggWWto2L2Nu_OS_PolarizationLT_postEE",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       973:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/ggWWto2L2Nu_OS_PolarizationTL_postEE",0.08268*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),
       974:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/ggWWto2L2Nu_OS_PolarizationTT_postEE",3.10724*(ggWWXS_LO_MCFM/ggWWXS_LO_MADGRAPH)*ggWWXS_kFactor*1000,plotCategory("kPlotggWW")),

       975:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/WW_MINNLO_13p0TeV",(118.7-3.974)*0.1086*0.1086*9*1000,plotCategory("kPlotqqWW")),

       976:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/WW_MINNLO_13p6TeV",12.80173*1000,plotCategory("kPlotqqWW")),

       977:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/WZ3l_2022_postEE",4.924*1.08*1000,plotCategory("kPlotWZ")),

       978:("/ceph/submit/data/user/c/ceballos/test_samples/WpWpJJ-EWK_TuneCP5_13p6TeV-powheg-pythia8",0.5*0.0295576*1000,plotCategory("kPlotEWKSSWW")),
       979:("/ceph/submit/data/user/c/ceballos/test_samples/WmWmJJ-EWK_TuneCP5_13p6TeV-powheg-pythia8",0.5*0.0295576*1000,plotCategory("kPlotEWKSSWW")),

       980:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/WWJJto2L2Nu-SS-noTop-EWK_TuneCP5_13p6TeV_madgraph-pythia8",0.0295576*1000,plotCategory("kPlotEWKSSWW")),
       981:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/WZJJto3LNu-EWK_TuneCP5_13p6TeV_madgraph-pythia8",0.0429366*1000,plotCategory("kPlotEWKWZ")),
       982:("/ceph/submit/data/group/cms/store/user/ceballos/test_samples/WZJJto3LNu-QCD_TuneCP5_13p6TeV_madgraph-pythia8",0.4958618*1000*0.60,plotCategory("kPlotWZ")),
    }
    return switch.get(argument, "BKGdefault, xsecDefault, category")


if __name__ == "__main__":
    print("Testing SwitchSample function...")
    print(SwitchSample(100, "2l", 20220))
    print(SwitchSample(100, "2l", 20221))
    print(SwitchSample(100, "2l", 20230))
    print(SwitchSample(100, "2l", 20231))
    print(SwitchSample(100, "2l", 20240))
    print(SwitchSample(100, "2l", 20241))
    print(SwitchSample(100, "2l", 2025))