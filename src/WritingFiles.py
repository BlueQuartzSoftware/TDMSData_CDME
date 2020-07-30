"""
Contract:

Inputs:
array of part names (TDMS file part names)
target folder locations
source file directory
number of files to write (numFiles)

batchSize (defaults to 1, don't bother changing it.)
first slice number (optional; defaults to 1, but changes if the starting slice number is
    not one. IE, segmenting your work or doing testing.)

mode: if HDF5, then creates datasets in preloaded HDF5 files in each directory.
    Note: the datasets are one per layer per part directory.
    The preloaded HDF5 files are one file per directory.
    One HDF5 file has many slices for a part.

Outputs:
the folder with all the written files. No return object necessary, just the action performed.

"""


# TODO: HDF5



import time as time
from nptdms import TdmsFile
from pprint import pprint
import os
from os import walk
import shutil
from pathlib import Path
import csv
import h5py
import numpy as np



def testTdmsFile():
    tdms = TdmsFile("/Volumes/RAID-0/LockheedMartin/TDMS_200120_12-40_2020-01-20 ATRQ Build 2/Slice00122.tdms")
    # tdms.as_hdf('/tmp/Slice00122.h5')

    properties = tdms.properties
    for property in properties:
        print(f'PROPERTY: {property} = {properties[property]}')

    objects = tdms.objects
    for obj in objects:
        print(f'OBJECT: {obj}')
    
    groups = tdms.groups()
    for part in groups:
        print(f'GROUP: {part}')
        # get the data from each group's channel and make a CSV
        channels = tdms.group_channels(part)

        # make a 2D array, and populate it with the arrays in this loop.
        groupCSV = []
        areaCol = []
        xCol = []
        yCol = []
        paramCol = []
        intensityCol = []
        laserCol = []
        csvCount = 0
        # copy each channel's data to its respective frame

        for channel in channels:
            print(f'  CHANNEL: {channel}')
            names = []
            for i in channels:
                wordList = str(i).split("/")
                name = wordList[-1]
                name = name.strip(">")
                name = name.strip("'")
                names.append(name)
            colNames = names

def writeFilesCSV(folderDictionary, tdmsFiles, sourceTDMSDirectory, numFiles, batchSize=1, firstSliceNum=1):

    # print(str(sourceTDMSDirectory) + "\\" + tdmsFiles[0])
    # testTime = time.time()
    numLayers = 0
    tdmsObjects = []
    numBatches = 0
    sliceCounter = int(firstSliceNum) - 1
    sliceFileName = ""
    # Outermost loop: controls the number of files written, total.


    while numLayers < numFiles:

        # Gets files from TDMS files
        #   This one isn't the outermost because I want to manage memory better.
        for file in tdmsFiles:

            # opens a TDMS file. Doing the same weird path-trick as before, to be OS independent.
            tdmsObjects.append(TdmsFile(str(Path(str(sourceTDMSDirectory)) / Path(str(file)))))
            numLayers += 1
            print("Printing slice " + str(numLayers) + " out of " + str(int(firstSliceNum) + int(numFiles) - 1) + ".")
            # Once we've got a few of the TDMS files open, transform them into CSV's.
            #   Happens every time a batch is fill (IE: every 5th file)
            if numLayers % batchSize == 0 or numLayers == numFiles:

                # all of the actual file writing will happen in here

                processTime = time.time()
                # print("Block " + str(numBatches))
                # print(str(tdmsObjects) + "\n")

                # print(tdmsObjects)
                # print(numLayers)

                for tdms in tdmsObjects:
                    sliceCounter = sliceCounter + 1
                    groups = tdms.groups()
                    # print(tdms)
                    for part in groups:
                        # get the data from each group's channel and make a CSV
                        channels = tdms.group_channels(part)

                        # make a 2D array, and populate it with the arrays in this loop.
                        groupCSV = []
                        areaCol = []
                        xCol = []
                        yCol = []
                        paramCol = []
                        intensityCol = []
                        laserCol = []
                        csvCount = 0
                        # copy each channel's data to its respective frame

                        for channel in channels:

                            names = []
                            for i in channels:
                                wordList = str(i).split("/")
                                name = wordList[-1]
                                name = name.strip(">")
                                name = name.strip("'")
                                names.append(name)
                            colNames = names
                            # pprint(channel.data)
                            name = channel.channel
                            data = channel.data

                            if names[0] in name:
                                areaCol = data
                            elif names[1] in name:
                                xCol = data
                            elif names[2] in name:
                                yCol = data
                            elif names[3] in name:
                                paramCol = data
                            elif names[4] in name:
                                intensityCol = data
                            elif names[5] in name:
                                laserCol = data
                            groupCSV.append(data)
                            csvCount += 1

                        writeFileLocation = folderDictionary[str(part)]

                        # I tried avoiding this earlier, but here I'm just checking the os. If unix, then use
                        #  the unix file delimiter (forwardslash). If windows, then use the backslash delimiter.
                        if os.name is "posix":
                            sliceFileName = str(writeFileLocation) + "/Slice000" + str(sliceCounter) + ".csv"
                        elif os.name is "nt":
                            sliceFileName = str(writeFileLocation) + "\\Slice000" + str(sliceCounter) + ".csv"



                        with open(sliceFileName, mode="w", newline="") as writeFile:
                            wr = csv.writer(writeFile, quoting=csv.QUOTE_ALL, dialect="excel")
                            wr.writerow(names)

                            # if len(areaCol) > 1 means:
                            # if there are data points in here
                            # But what if there straight up aren't any columns to begin with??

                            # IN that case then I need to identify if there are no rows

                            if len(areaCol > 1):
                                for rows in range(0, len(areaCol - 1)):  # - 1):
                                    # print(str(len(areaCol)) + "\n")

                                    # NOTE: the try catch isn't the best way to do this, I know.
                                    # HOWEVER, I can't deduce what the actual problem is here.
                                    # It's the best I can do -- Maxwell, Jan 15 2019.
                                    try:
                                        # print("Writing file: " + str(sliceFileName) + "\n")
                                        row = [areaCol[rows], xCol[rows], yCol[rows], paramCol[rows], intensityCol[rows],
                                               laserCol[rows]]
                                        wr.writerow(row)
                                    except IndexError:
                                        print("IndexError. Possibly no data for that part anymore?")
                                        print("While writing file: " + str(sliceFileName) + "\n")

                processTime = time.time() - processTime
                print("\nTime for this batch was " + str(processTime) + " seconds.")
                print("Or " + str(processTime / (sliceCounter - int(firstSliceNum) + 1)) + " seconds per layer so far.\n")

                # end operation space
                # this declaration clears the memory for the tdms objects
                tdmsObjects = []
                numBatches = numBatches + 1

    return numLayers


def writeFilesHDF5(destinationDictionary, tdmsFiles, sourceTDMSDirectory, numFiles, batchSize=1, firstSliceNum=1):

    #destinationDictionary looks like this:
    # '0_00001_op1_Pad_6_cls', '/home/maxwell/Documents/CDME/Processed Stacks test Jan 27/0_00001_op1_Pad_6_cls/0_00001_op1_Pad_6_cls.hdf5'


    numLayers = 0
    tdmsObjects = []
    sliceCounter = int(firstSliceNum) - 1
    # Outermost loop: controls the number of files written, total.

    while numLayers < numFiles:

        # Gets files from TDMS files
        #   This one isn't the outermost because I want to manage memory better.
        for file in tdmsFiles:

            # opens a TDMS file. Doing the same weird path-trick as before, to be OS independent.
            tdmsObjects.append(TdmsFile(str(Path(str(sourceTDMSDirectory)) / Path(str(file)))))
            numLayers += 1
            print("Printing slice " + str(numLayers) + " out of " + str(int(firstSliceNum) + int(numFiles) - 1) + ".")
            # Once we've got a few of the TDMS files open, transform them into CSV's.
            #   Happens every time a batch is fill (IE: every 5th file)
            if numLayers % batchSize == 0 or numLayers == numFiles:

                # all of the actual file writing will happen in here

                processTime = time.time()
                # print("Block " + str(numBatches))
                # print(str(tdmsObjects) + "\n")
                # print(tdmsObjects)
                # print(numLayers)

                for tdms in tdmsObjects:
                    properties = tdms.properties
                    properties["Layer Start Time"] = properties["StartTime"]
                    properties["Layer End Time"] = properties["EndTime"]
                    del properties["StartTime"]
                    del properties["EndTime"]

                    sliceCounter = sliceCounter + 1
                    groups = tdms.groups()
                    # print(tdms)
                    for part in groups:
                        partPropertyItems = part.properties
                        partPropertyItems["Part Start Time"] = partPropertyItems["StartTime"]
                        partPropertyItems["Part End Time"] = partPropertyItems["EndTime"]
                        del partPropertyItems["StartTime"]
                        del partPropertyItems["EndTime"]
                        partPropertyItems = part.properties.items()

                        # get the data from each group's channel and make a CSV
                        channels = tdms.group_channels(part)

                        # make a 2D array, and populate it with the arrays in this loop.
                        groupCSV = []
                        areaCol = []
                        xCol = []
                        yCol = []
                        paramCol = []
                        intensityCol = []
                        laserCol = []
                        csvCount = 0
                        # copy each channel's data to its respective frame

                        for channel in channels:

                            names = []
                            for i in channels:
                                wordList = str(i).split("/")
                                name = wordList[-1]
                                name = name.strip(">")
                                name = name.strip("'")
                                names.append(name)
                            colNames = names
                            # pprint(channel.data)
                            name = channel.channel
                            data = channel.data

                            if names[0] in name:
                                areaCol = data
                            elif names[1] in name:
                                xCol = data
                            elif names[2] in name:
                                yCol = data
                            elif names[3] in name:
                                paramCol = data
                            elif names[4] in name:
                                intensityCol = data
                            elif names[5] in name:
                                laserCol = data
                            groupCSV.append(data)
                            csvCount += 1

                        writeFileLocation = destinationDictionary[str(part.name)]
                        #except it's actually like this:
                        # '0_00001_op1_Pad_6_cls', '/home/maxwell/Documents/CDME/Processed Stacks test Jan 27/0_00001_op1_Pad_6_cls/0_00001_op1_Pad_6_cls.hdf5'
                        # so I have to get rid of the last addendum

                        # working directory has to be changed before writing the HDF5, for several reasons
                        #   one: operating sys independence
                        #   two: it doesn't work with relative pathing for some reason? cwd gets around that.
                        #     Not sure why tho.
                        cwd = os.getcwd()
                        lastSlashIndex = writeFileLocation.rfind("/")
                        targetWD = writeFileLocation[0:lastSlashIndex]
                        os.chdir(targetWD)

                        groupName = str(sliceCounter)

                        # now to open the target file!

                        with h5py.File(writeFileLocation, "a") as hdf5File:

                            sliceGroup = hdf5File.create_group(groupName)
                            sliceAttributes = sliceGroup.attrs
                            sliceAttributes.create("TDMS Group Name", np.string_(part.name))

                            #print('TDMS PROPERTIES')
                            for property in properties:
                                #print(f'  PROPERTY: {property} = {properties[property]}')
                                value = properties[property]
                                if isinstance(value, np.datetime64):
                                    value = np.string_(np.datetime_as_string(value, unit='us', timezone='UTC'))
                                sliceAttributes.create(property, value)

                            #print("  PART PROPERTIES")
                            for prop_name, value in partPropertyItems:
                                #print(f'    prop_name: {prop_name}   prop_value: {value}')
                                if isinstance(value, np.datetime64):
                                    value = np.string_(np.datetime_as_string(value, unit='us', timezone='UTC'))
                                sliceAttributes.create(prop_name, value)

                            # If there aren't any rows then just skip it,
                            #  otherwise create a dataset for each trait
                            if len(areaCol > 1):
                                try:
                                    areaData = sliceGroup.create_dataset("Area", data=areaCol)
                                    intensityCol = sliceGroup.create_dataset("Intensity", data=intensityCol)
                                    laserCol = sliceGroup.create_dataset("LaserTTL", data=laserCol)
                                    paramData = sliceGroup.create_dataset("Parameter", data=paramCol)
                                    xData = sliceGroup.create_dataset("X-Axis", data=xCol)
                                    yData = sliceGroup.create_dataset("Y-Axis", data=yCol)
                                except Exception as ex:
                                    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                                    message = template.format(type(ex).__name__, ex.args)
                                    print(message)

                        os.chdir(cwd)

                processTime = time.time() - processTime
                # TODO: fix this because the times are incorrect again for some reason
                print("\nTime for this batch was " + str(processTime) + " seconds.")
                print("Or " + str(processTime / (sliceCounter - int(firstSliceNum) + 1)) + " seconds per layer, so far.\n")

                # end operation space
                # this declaration clears the memory for the tdms objects
                tdmsObjects = []
    return numLayers





