#!/usr/bin/env python

__author__ = "George M. Grindlinger"
__version__ = "1.0"
__email__ = "georgeg@oit.rutgers.edu"
__status__ = "Development"
__doc__ = "Tape Reaper: Reaps tapes from the amanda vault lists."

import pprint
import os
import subprocess
import re

# Initialize debugging code
#def dump(obj):
#   for attr in dir(obj):
#       if hasattr( obj, attr ):
#           print( "obj.%s = %s" % (attr, getattr(obj, attr)))

# Query `mtx status` and pull the tape robot data
# Apparently Py2.6 doesn't support this
# mtx_status = subprocess.check_output('mtx status')
mtx_status = subprocess.Popen(['/usr/sbin/mtx', 'status'], stdout=subprocess.PIPE).communicate()[0]
mtx_status = mtx_status.split("\n")

# Parse mtx_status and pull individual tape barcodes
tapes = []
for line in mtx_status:
    if "Full" in line:
        match = re.search('VolumeTag ?= ?(\w+)(L6)', line)
        if match:
            tapes.append(match.group(1))
        else:
            print("Error: No Match on:\n" + line)

# Enumerate found tapes for diagnostic and logging purposes
print("Found the following tapes: ")
for tape in tapes:
    print("  " + tape)
print("Total number: " + str(len(tapes)))

# Walk Amanda dirs from amandaRoot and generate list of tapelist files to check
amandaRoot = '/etc/amanda'
tapelist_FileCache = []
for dirpath, dirnames, files in os.walk(amandaRoot):
    for name in files:
        if name == "tapelist":
            tapelist_FileCache.append(os.path.join(dirpath, name))

print("\nFound the following tapelist files: ")
for file in tapelist_FileCache:
    print("  " + file)

# For every tapelist file found in the walk above, open it, read it in
# then get the backup job name (parent directory name of file)
foundTapes = False
for file in tapelist_FileCache:
    f = open(file, "r")
    f_buff = f.readlines()
    bkupJobName = os.path.split(os.path.dirname(file))[1]

    # Compare every tape against every line in the file and look for matches
    for tape in tapes:
        tapeFound = False
        for i in f_buff:
            if tape in i:
                # If a tape match is found we need to run `amrmtape`
                # and give it the job name  as well as the full 
                # tape label name (2nd field of matching line)
                # If this is the first time finding the tape list the job
                if tapeFound == False:
                    print("\nTape: " + tape + " found in: " + bkupJobName)
                    tapeFound = True
                    foundTapes = True
                tapeLabel = i.split(" ")[1] 

                print("\n  Removing label: " + tapeLabel)
                subprocess.Popen(['/usr/sbin/amrmtape', bkupJobName, tapeLabel]).communicate()[0]

if foundTapes == False:
    print("\nNo current tapes were found in any of the tapelists")

# For screen formatting
print("\n")
exit(0)
