import ROOT
import os, sys, getopt, json, time, subprocess, socket
import fnmatch
import math


if __name__ == "__main__":

    years = [20220, 20221, 20230, 20231, 20240, 20250]
    wzPOW = ["103 ", "203 ", "303 ", "403 ", "503 ", "503 "]
    wzMG  = ["179 ", "279 ", "379 ", "479 ", "579 ", "579 "]

    inputCfg = "Analysis_input_condor_jobs.cfg"
    ana  = "wz"
    isWZMG = 1
    inputFolder = "."

    valid = ['outputDir=', "ana=", "isWZMG=", "inputFolder=", 'help']
    usage  =  "Usage: ana.py --ana=<{0}>\n".format(ana)
    usage +=  "              --isWZMG=<{0}>\n".format(isWZMG)
    usage +=  "              --inputFolder=<{0}>".format(inputFolder)
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
        if opt == "--ana":
            ana = str(arg)
        if opt == "--isWZMG":
            isWZMG = int(arg)
        if opt == "--inputFolder":
            inputFolder = str(arg)

    inputSamplesCfg = inputFolder + "/" + ana + inputCfg
    if(not os.path.exists(inputSamplesCfg)):
        print("File {0} does not exist".format(inputSamplesCfg))
        sys.exit(1)

    outputSamplesCfg = inputSamplesCfg.replace(".cfg","_new.cfg")
    outputSamplesFile = open(outputSamplesCfg, 'w')

    for x in range(len(years)):
        if(isWZMG == 1):
            outputSamplesFile.write("{0}{1}\n".format(wzMG[x],years[x]))
        else:
            outputSamplesFile.write("{0}{1}\n".format(wzPOW[x],years[x]))

    inputSamplesFile = open(inputSamplesCfg, 'r')
    while True:
        line = inputSamplesFile.readline().strip()
        if not line:
            break
        goodLine = True
        for x in range(len(years)):
            # Must remove all wzMG and wzPOW lines
            if  (wzMG[x]  in line): goodLine = False
            elif(wzPOW[x] in line): goodLine = False
        if(goodLine == False):
            continue
        outputSamplesFile.write(line+"\n")

    outputSamplesFile.close()
