import json
import os
import requests
import tetpyclient
import csv
import pandas as pd 
import numpy as np

'''
the goal of this script is to pull an IP blacklist from the Talos Reputation Center and
inject that into tetration with an annotation that will highlight it's Blacklisted
The Talos Reputation Center maintains an IP BLF that they update every 15 minutes 
at https://talosintelligence.com/documents/ip-blacklist. 

There are a BUNCH of different blacklist files in the Internetz, so I'll add those 
in future versions and this will become more than just a Talos BLF

Basic outline of what I want to do here:
1. if last does not exist, create an empty last file
2. grab latest list from talos BLF url
3. annotate both last and latest with proper annotation keys and values
4. load both latest and last into memory and compare. if last and latest are the same, quit & notify
5. get deltas and write them to csv as follows:
6. upload deltaAdd.csv as added annotations and deltaDelete.csv as removed annotations
7. when we're done, rename latest file as last file

we can rinse/repeat for every known bad list that we want to use

Needed Environment Variables:
PATH_TO_LAST
PATH_TO_LATEST
TALOS_URL
TETRATION_ENDPOINT
TETRATION_KEY
TETRATION_SECRET
TETRATION_VRF

'''

# the function getblf will grab a blf from a url 
def getBlf(url):
    # need to put in try/excecpt function for something other than 200 response code
    blf = requests.get(url)
    return (blf.content)

# a function to write the content from the  BLF to 
def writeToLatestBlf(content,filename):
    # write the BLF to a file named by filename parm
    # will need to put an ENV variable for the public folder path on the ecoHub
    # need to put try/except for io errors
    with open(filename,'w') as f:
        f.write(content)

def writeToLastBlf(content,filename):
    # write the BLF to a file named by filename parm
    # will need to put an ENV variable for the public folder path on the ecoHub
    # need to put try/except for io errors
    with open(filename,'w') as f:
        f.write(content)

# a function to read the last BLF file used
def readFromLastBlf(filename):
    # read from the last BLF
    # need to pass in path and filename as ENV
    # need to add try/except for IO errors
    with open(filename,'r') as f:
        last = f.read()
    return(last)

def annotateAndCompareFiles(lastFile,latestFile,addFile,delFile):
    # read last file into pandas dataframe, add two columns: VRF and Black List
    # need to parameterize the List name so we can use other BLFs eventually
    blfheader = ["IP", "VRF", "Black List"]
    lastdf = pd.read_csv(lastFile, index_col=False, header=None, columns=blfheader)
    lastdf['Black List'] = "Talos Black List" 
    lastdf['VRF'] = "Default"
    # read latest file into pandas dataframe, add two columns: VRF and Black List
    # need to parameterize the List name so we can use other BLFs
    latestdf = pd.read_csv(latestFile, index_col=False, header=None, columns=blfheader)
    latestdf['Black List'] = "Talos Black List" 
    latestdf['VRF'] = "Default"
    # write last and latest files with included annotation fields
    lastdf.to_csv(lastFile, index=False, columns=blfheader)
    latestdf.to_csv(latestFile, index=False, columns=blfheader)
    # dump the two files into pandas(memory) and compare
    # stuff to delete will be in latest-last = deltaDelete
    # if nothing in last, then all of latest will go into annotations
    # need to parameterize the column names and stuff so we can use other BLFs eventually
    # now let's compare if the two dataframes are the same, if so, return an exit code and quit the program
    if ((lastdf['IP'] == latestdf['IP']).all()):
        print("*** Last and Latest IP lists are the same, quitting... ***")
        raise SystemExit
    # if it's in last but not in latest, delete it
    header = ["IP", "VRF", "Black List"]
    deltaDeleteDf = lastdf[~lastdf.IP.isin(latestdf.IP)].dropna()
    deltaDeleteDf = deltaDeleteDf[header]
    deltaDeleteDf.to_csv(delFile, index=False)
    # if it's in latest but not in last, add it to the deltaAddFile
    mergeDf = lastdf.merge(latestdf, indicator=True, how='outer')
    deltaAddDf = mergeDf[mergeDf['_merge'] == 'right_only'].ix[:,:-1]
    deltaAddDf = deltaAddDf[header]
    deltaAddDf.to_csv(addFile, index=False)




# make talosBlfUrl an ENV variable at some point??
# need to parameterize the Talos BLF URL as a var
talosBlfUrl = 'https://talosintelligence.com/documents/ip-blacklist'
# declare names of files 
# not sure if we should parameterize the last file or not...
lastTalosBlFile = 'talosblf-last.csv'
# these files are only significant DURING an instantiation, don't need to declare outside of script
latestTalosBlFile = 'talosblf-latest.csv'
deltaDeleteFile = 'deltaDelete.csv'
deltaAddFile = 'deltaAdd.csv'

# call function to grab the BLF from the Talos Reputation Center URL
latestTalosBlf = (getBlf(talosBlfUrl))

# check to see if last exists, if not, create an empty one
# if last existst, call function to read the last BLF 
# we should declare file path in ENV var to pull from the ecoHub
try:
    check=open(lastTalosBlFile,'r')
except IOError:
    print("Error: " + lastTalosBlFile + " does not appear to exist, creating empty file")
    with open(lastTalosBlFile,'w') as f:
        f.close()
else:
    lastTalosBlf = readFromLastBlf(lastTalosBlFile)

print(lastTalosBlf)
print(latestTalosBlf)

# call function to add annotations to the last and latest files
# compareFiles(lastBlFile, latestBlFile)
annotateAndCompareFiles(lastTalosBlFile,latestTalosBlFile,deltaAddFile,deltaDeleteFile)

# call function to write the Talos BLF to a file named "talosblf-latest.csv"
# need to add path Env variable eventually
#writeToLatestBlf(latestTalosBlf,latestTalosBlFile)

# call function to dump annotations into Tetration

# save current annotations to a file named "talosblf-last.csv"
# this file will be used in the next iteration 
# writeToLastTalosBlf(talosBlfContent)

