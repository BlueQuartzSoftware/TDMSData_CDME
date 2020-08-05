# TDMSData_CDME #

Transforms TDMS data from the CDME's Metal 3D Printers to a more readable file format. This is part of the Ohio State University Center for Design and Manufacturing Excellence Additive Manufacturing lab efforts.

The original problem: The TDMS file outputs from the metal 3d printers here at the lab come with the following hierarchy:

+ A build is made of hundreds to thousands of slices, all printed onto the same build plate. Each slice has a TDMS file.
+ Each slice of the build has dozens of parts on it, that all occur at the same height on the Y axis.
+ Each part has some associated data inside of a TDMS file. All parts are contained in 1 file.

This is pretty understandable at a conceptual level but not very easy to machine read in for visualization purposes.
For one, we can't easily grab multiple layers from one part; instead, we have to grab many parts.
I'm going ahead and separating these manually.

For visualization purposes, we would prefer to have:

A build will be made of dozens of parts
Each part is made of hundreds to thousands of slices
Each slice has some associated data located inside a file.

This script transforms the file arrangement to be in a folder hierarchy with HDF5 storage.

## USAGE INSTRUCTIONS ##

The repository linked contains a src folder and a README. Download the src folder or clone the repository to your local machine to use it.

Software prerequisites:
Python interpreter & IDLE: https://www.python.org/downloads/
Make sure to install Pip.
All of the project was written with Python 3.8 in mind, but the most recent Python 3 version should work.
Anaconda also will work well for this.

After installing Pip: open your command line (On windows, run cmd.exe. On Linux, you should know how to do that.)
    Run the following to install some python libraries:

    pip install nptdms
    pip install numpy
    pip install h5py

These three libraries are required. If these don’t work because you don’t have admin permissions, install locally by appending the --user flag to the commands.

Ok, so I’ve got Python downloaded, the three libraries installed. ***What now?***

Locate the folder of tdms files you want to transform. If they’re in a zip folder, extract them out of the archive.

Run the "tdms2h5.py” file in the root folder by right clicking & selecting “Run with IDLE”. Alternatively, start a command line, navigate to the folder with main.py, and run it in python with the commands python then Main.py.

## Anaconda ##

        [user] $ conda activate [virtual env name]
        [user] $ conda install h5py numpy nptdms
        [user] $ python tdms2h5.py [input_dir] [output_dir] Slice
