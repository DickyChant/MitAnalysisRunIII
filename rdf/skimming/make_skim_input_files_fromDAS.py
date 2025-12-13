import ROOT
import os, sys, getopt
from subprocess import call,check_output

def findDataset(name):

    DASclient = "dasgoclient -query '%(query)s'"
    cmd= DASclient%{'query':'file dataset=%s'%name}
    print(cmd)
    check_output(cmd,shell=True)
    fileList=[ 'root://xrootd-cms.infn.it/'+ str(x) for x in check_output(cmd,shell=True).decode('utf8').split() ]
    #fileList=[ 'root://cmsxrootd.fnal.gov/'+ str(x) for x in check_output(cmd,shell=True).decode('utf8').split() ]
    #fileList=[ 'root://cms-xrd-global.cern.ch/'+ str(x) for x in check_output(cmd,shell=True).decode('utf8').split() ]

    files_ROOT = ROOT.vector('string')()
    for f in fileList: files_ROOT.push_back(f)

    return files_ROOT

#dasgoclient --query="dataset status=* dataset=/*/*Run3Summer23NanoAODv12*/NANOAODSIM" | sort > lll;
#grep FAKE skim_input_samples_2023a_fromDAS.cfg|awk '{split($1,a,"+");print"grep "a[1]" lll"}' > ll
#dasgoclient --query="dataset status=* dataset=/*/*Run3Summer23BPixNanoAODv12*/NANOAODSIM" | sort > lll;
#grep FAKE skim_input_samples_2023b_fromDAS.cfg|awk '{split($1,a,"+");print"grep "a[1]" lll"}' > ll

if __name__ == "__main__":

    inputCfg = "skim_input_samples_fromDAS.cfg"
    outputCfg = "skim_input_files_fromDAS.cfg"
    outputForCondorCfg = "skim_input_condor_jobs_fromDAS.cfg"
    group = 5
    suffix = ""

    valid = ["inputCfg=", "outputCfg=", "outputForCondorCfg=", "group=", "suffix=", 'help']
    usage  =  "Usage: ana.py --inputCfg=<{0}>\n".format(inputCfg)
    usage +=  "              --outputCfg=<{0}>\n".format(outputCfg)
    usage +=  "              --outputForCondorCfg=<{0}>\n".format(outputForCondorCfg)
    usage +=  "              --group=<{0}>\n".format(group)
    usage +=  "              --suffix=<SUFFIX>  (optional) Suffix to append to output filenames before .cfg\n"
    usage +=  "                                   e.g., --suffix=2025d creates:\n"
    usage +=  "                                   skim_input_files_fromDAS_2025d.cfg\n"
    usage +=  "                                   skim_input_condor_jobs_fromDAS_2025d.cfg"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", valid)
    except getopt.GetoptError as ex:
        print(usage)
        print(str(ex))
        sys.exit(1)

    for opt, arg in opts:
        if opt == "--help":
            print(usage)
            sys.exit(1)
        if opt == "--inputCfg":
            inputCfg = str(arg)
        if opt == "--outputCfg":
            outputCfg = str(arg)
        if opt == "--outputForCondorCfg":
            outputForCondorCfg = str(arg)
        if opt == "--group":
            group = int(arg)
        if opt == "--suffix":
            suffix = str(arg)

    # Apply suffix to output filenames if provided
    if suffix:
        # Insert suffix before .cfg extension
        if outputCfg.endswith('.cfg'):
            outputCfg = outputCfg[:-4] + '_' + suffix + '.cfg'
        else:
            outputCfg = outputCfg + '_' + suffix
        
        if outputForCondorCfg.endswith('.cfg'):
            outputForCondorCfg = outputForCondorCfg[:-4] + '_' + suffix + '.cfg'
        else:
            outputForCondorCfg = outputForCondorCfg + '_' + suffix

    print("Output files will be:")
    print("  - {0}".format(outputCfg))
    print("  - {0}".format(outputForCondorCfg))
    if suffix:
        print("  (using suffix: {0})".format(suffix))
    print("")

    outputFile = open(outputCfg, 'w')
    outputForCondorFile = open(outputForCondorCfg, 'w')

    countSamples = 0
    inputFile = open(inputCfg, 'r')
    while True:
        line = inputFile.readline().strip()
        if not line:
            break
        countSamples += 1
        print(line)

        lineForDAS = "/" + line.replace("+","/")
        filesDAS = findDataset(lineForDAS)

        countJobs = 0
        countFiles = 0
        for nf in range(len(filesDAS)):
            lineRaw = filesDAS[nf]
            if(countFiles%group == 0):
                lineForCondor = "{0} {1} {2} {3}\n".format(countSamples-1,countJobs,group,line)
                outputForCondorFile.writelines(lineForCondor)
                countJobs += 1

            countFiles += 1
            outputFile.writelines(lineRaw)
            outputFile.writelines("\n")

        print("Sample({0}): files/jobs: {1} / {2}".format(countSamples,countFiles,countJobs))

    print("Samples: {0}".format(countSamples))
