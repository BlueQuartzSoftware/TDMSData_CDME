import time as time
from nptdms import TdmsFile
from pathlib import Path
import h5py
import os

# Make a "Processed" directory as a subdirectory one folder up

"""
Contract for buildDirectories:

input:

takes in:
    path to the TDMS directory
    the memory array of the TDMS files
    mode: if HDF5, then it creates an hdf5 file in every folder to be populated with datasets later.

return:

returns a dictionary of every part and its file location

Note

"""


def buildDirectories(sourceTDMSDirectory, tdmsFiles, taskName, mode="csv"):
    directoryBuildTime = time.time()

    # sourceTDMSDirectory is where we are collecting these files

    # I know these parentheses are ugly, but lemme explain.
    # TdmsFile only takes a string, but I want it to work on Linux or Windows. So I'm using the Path library
    # to concatenate these strings together in a way that works on both OS's.
    #   The Path lib takes a "/" as an operator to concatenate filepaths.
    # Then, after I concatenate the paths, I turn them back into a string.
    firstObject = TdmsFile(str(Path(str(sourceTDMSDirectory)) / Path(str(tdmsFiles[0]))))

    parentDir = sourceTDMSDirectory.parent
    newFolder = parentDir / str(taskName)
    newFolder.mkdir(exist_ok=True, parents=True)

    # Now that we have the folder: let's go in and make a subfolder for every group we've got in the TDMS files.
    folderDictionary = dict()
    groups = firstObject.groups()
    for part in groups:
        
        print(f'part: {part}')
        partName = part.name
        print(f'partName: {part.name}')
        #TODO: find out why these files aren't getting built in the proper directories.
        newDir = newFolder / partName
        newDir.mkdir(exist_ok=True, parents=True)
        folderDictionary[str(part.name)] = str(newDir)



        #if the mode is HDF5 then we need to build the HDF5 file here and detect it later to fill with datasets
        # Why build here?? Because later when populating, we populate data by loading in a slice and doing all X parts.
        # So we build the HDF5 for a part, and load in all X layers later.
        if mode is "HDF5":
            destination = newDir / str(str(partName) + ".hdf5")
            print(str(destination))
            #problem: these get opened in the root folder for the script, not the target folder.
            #print(str(partName) + ".hdf5")
            cwd = os.getcwd()
            os.chdir(newDir)
            hf = h5py.File(str(partName) + ".hdf5", 'w')
            hf.close()
            os.chdir(cwd)
            folderDictionary[str(part.name)] = str(destination)



    # pprint(FolderDictionary)
    # Boom: we've now got a folder for every part, and a mapping of group name (part name) to folder name.

    # Next step is to go into every TDMS's item, and write the
    # associated data to a CSV inside of the folder for that name, with a good name for the slice.
    # sourceTDMSDirectory

    directoryBuildTime = time.time() - directoryBuildTime
    print("Time to build directories was " + str(directoryBuildTime) + " seconds.\n")

    return folderDictionary
