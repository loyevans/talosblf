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
3. load both lists into memory and compare, if no difference, notify and quit program
4. if there are differences, do this:
    a. latest-last = talosDeltaAdd.csv
    b. last-latest = talosDeltaDelete.csv
5. upload talosDeltaAdd.csv as added annotations 
6. upload talosDeltaDelete.csv as removed annotations
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

def annotateFiles(lastFile,latestFile):
    # read last file into pandas dataframe, add two columns: VRF and Black List
    # need to parameterize the List name so we can use other BLFs eventually
    lastdf = pd.read_csv(lastFile, index_col=False, header=None, names=["IP", "Black List"])
    lastdf['Black List'] = "Talos Black List" 
    lastdf['VRF'] = "Default"
    # read latest file into pandas dataframe, add two columns: VRF and Black List
    # need to parameterize the List name so we can use other BLFs
    latestdf = pd.read_csv(latestFile, index_col=False, header=None, names=["IP", "Black List"])
    latestdf['Black List'] = "Talos Black List" 
    latestdf['VRF'] = "Default"
    # write last and latest files with included annotation fields
    header = ["IP", "VRF", "Black List"]
    lastdf.to_csv(lastFile, index=False, columns=header)
    latestdf.to_csv(latestFile, index=False, columns=header)
    
def getDeltaFiles(lastFile,latestFile,addFile,delFile):
    # dump the two files into pandas(memory) and compare
    # stuff to delete will be in latest-last = deltaDelete
    # if nothing in last, then all of latest will go into annotations
    # need to parameterize the column names and stuff so we can use other BLFs eventually
    # read last file into pandas dataframe
    lastdf = pd.read_csv(lastFile, index_col=False, header=None, names=["IP", "VRF", "Black List"])
    # read latest file into pandas dataframe
    latestdf = pd.read_csv(latestFile, index_col=False, header=None, names=["IP", "VRF", "Black List"])
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

latestTalosBlFile = 'talosblf-latest.csv'
lastTalosBlFile = 'talosblf-last.csv'
deltaDeleteFile = 'deltaDelete.csv'
deltaAddFile = 'deltaAdd.csv'

# call function to grab the BLF from the Talos Reputation Center URL
latestTalosBlf = (getBlf(talosBlfUrl))

# check to see if last exists, if not, read latest and name it first
# call function to read the last BLF that was used from the previous script run
# declare file path in ENV var
try:
    check=open(lastTalosBlFile,'r')
except IOError:
    print("Error: " + lastTalosBlFile + " does not appear to exist, creating empty file")
    with open(lastTalosBlFile,'w') as f:
        f.close()
else:
    lastTalosBlf = readFromLastBlf(lastTalosBlFile)

# call function to add annotations to the last and latest files
# compareFiles(lastBlFile, latestBlFile)
annotateFiles(lastTalosBlFile,latestTalosBlFile)

# call function to compare and pull out deltas and write thost to csv
# need to add try/except for io errors
getDeltaFiles(lastTalosBlFile,latestTalosBlFile,deltaAddFile,deltaDeleteFile)


# call function to write the Talos BLF to a file named "talosblf-latest.csv"
# need to add path Env variable eventually
writeToLatestBlf(latestTalosBlf,latestTalosBlFile)

# compare last and latest Talos BLFs
# restults from this should be dict of talosDeltaDelete and talosDeltaAdd

# call function to dump annotations into Tetration

# save current annotations to a file named "talosblf-last.csv"
# this file will be used in the next iteration 
# writeToLastTalosBlf(talosBlfContent)

