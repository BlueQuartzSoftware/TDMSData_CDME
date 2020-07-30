# This one will take user input,
# call the function to get a file object
# #call the function to create a directory
# call the function to build the whole fucking thing,
# and call the function to delete unnecessary files.

import sys
"""
!{sys.executable} -m pip install nptdms
!{sys.executable} -m pip install numpy
!{sys.executable} -m pip install h5py
"""

# At least on my system, requirements already satisfied.

import time as time
from pprint import pprint
import os
from os import walk
from pathlib import Path

import BuildingDirectories
import WritingFiles
import FileCleanup
#import SummaryStatisticsOfParts

# WritingFiles.testTdmsFile()
# quit()


# print("Example directory path: \nC:/Users/maxah/Documents/CDME/Sept 9 2019 TDMS Parts/TDMS\n")
testPath = "C:\\Users\\maxah\\Documents\\CDME\\Sept 9 2019 TDMS Parts\\TDMS"

print("Enter directory path. Forward or backward slash doesn't matter.\n")

time.sleep(.1)  # just so that the output makes sense to the user in the correct order; otherwise,
#                     the input prompt would come first and be confusing.
yesNoChar = 'n'
dir_path = ""
numFiles = 0
firstFileName = ""
tdmsFiles = []

mode = "csv"

testPath = "/Volumes/RAID-0/LockheedMartin/TEST/"

while 'y' not in yesNoChar and 'Y' not in yesNoChar:

    # C:\\Users\\maxah\\Documents\\CDME\\Sept 9 2019 TDMS Parts\\TDMS
    # /home/maxwell/Documents/CDME/TestDataATRQHome
    # /home/maxwell/Documents/CDME/ATRQTestFolder

    if yesNoChar == 'n' or yesNoChar == "N":
        path_choice = input("Example path: " + "C:\\Users\\maxah\\Documents\\CDME\\Sept 9 2019 TDMS Parts\\TDMS" + "\n")
        dir_path = path_choice
        if "testpath" in dir_path or "TESTPATH" in dir_path:
            dir_path = testPath

    root = os.path.abspath(os.sep)
    cwd = Path.cwd()

    if '\\' in dir_path:
        newPath = dir_path.replace("\\", "/")
        dir_path = newPath

    sourceTDMSDirectory = root / Path(dir_path)

    print("The chosen directory is: " + dir_path)

    fileNames = []
    for (dirpath, dirnames, filenames) in walk(sourceTDMSDirectory):
        fileNames.extend(filenames)
        break

    tdmsFiles = []
    for fileName in sorted(fileNames):
        if ".tdms_index" not in fileName:
            tdmsFiles.append(fileName)
            numFiles = numFiles + 1
    print("Here are the contents of that directory: \n")
    length = len(tdmsFiles)
    if length > 0:
        firstFileName = tdmsFiles[0]
    pprint(tdmsFiles)

    yesNoChar = input("If that is not the directory you want, hit 'n'. If that is the directory you want, hit 'y'.\n")

taskName = ""
print("What are you going to call this project?\nEX: \"Nov 21 Build TDMS\"")
if "testpath" in path_choice or "TESTPATH" in path_choice:
    taskName = "TESTPATH Processed Stacks"
else:
    taskName = "Processed Stacks " + input("")
sourceTDMSDirectory = Path(dir_path)


print("What do you want the mode to be? Press enter for 'csv' if not sure, otherwise type 'hdf5'.")
modeString = str(input("Mode: "))

if 'h' in modeString or 'H' in modeString:
    mode = "HDF5"
    print("HDF5")
else:
    print("Default choice: CSV")
    mode = "CSV"


startTime = time.time()

batchSize = 1

firstSliceNum = firstFileName[-6:-5]

# the data pieces I still need:

# C:\\Users\\maxah\\Documents\\CDME\\Sept 9 2019 TDMS Parts\\TDMS
# /home/maxwell/Documents/CDME/TestDataATRQHome
# /home/maxwell/Documents/CDME/ATRQTestFolder
linux_test_path = "/home/maxwell/Documents/CDME/TestEnv"
# building directories part

folderDictionary = BuildingDirectories.buildDirectories(sourceTDMSDirectory, tdmsFiles, taskName, mode)

# def writeFiles(folderDictionary, tdmsFiles, sourceTDMSDirectory, numFiles, batchSize=1, firstSliceNum=1, mode="csv"):
numLayers = 0
if mode is "HDF5":
    #run the writeFilesHDF5 method
    numLayers = WritingFiles.writeFilesHDF5(folderDictionary, tdmsFiles, sourceTDMSDirectory, len(fileNames), batchSize, firstSliceNum)
elif mode is "CSV":
    numLayers = WritingFiles.writeFilesCSV(folderDictionary, tdmsFiles, sourceTDMSDirectory, len(fileNames), batchSize,
                                    firstSliceNum)


partsDeleted, partsRemaining, newFolderDict = FileCleanup.cleanFolders(folderDictionary)

# UPDATE: THIS IS AN EXPERIMENTAL FEATURE. MIGHT BREAK SHIT.
if mode is "CSV":
    FileCleanup.cleanSlices(newFolderDict)

# input hold; causes the program to freeze before exiting.
# Boom: now it only keeps those which have items inside.
print("Finished.\n")

endTime = time.time()
runTime = endTime - startTime
print("\n***FINISHED REPORT***")
print("\n" + "Runtime was: " + str(runTime) + " seconds.")
print("Or " + str(runTime / numLayers) + " seconds per layer.")
print("Number of layers written was: " + str(numLayers) + " layers.")
print("Number of parts with no data was: " + str(partsDeleted) + " parts.")
print("Number of parts with data was: " + str(partsRemaining) + " parts.")

exit = input("Finished: type the X key to exit.")
time.sleep(.01)
if ("x" not in exit and "X" not in exit):
    input()
