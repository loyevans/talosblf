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
1. if last does not exist, create an empty lastIp.csv file
2. grab latest IP list from talos BLF url & write to latestIp.csv
3. read latestIP.csv and lastIP.csv info datarames
4. compare these dataframes, if they are exactly the same, exit & notify, if not, go on
5. annotate both last and latest with proper annotation keys and values
5. check for deltas and write them to csv as follows:
    a. deltaAdd.csv - add annotations
    b. deltaDel.csv - remove annotations
6. upload deltaAdd.csv as added annotations and deltaDelete.csv as removed annotations
7. when we're done, rename/copy latestIp.csv to lastIp.csv

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

def areLastAndLatestSame(lastFile, latestFile):
    lastIpSet = set(pd.read_csv(lastFile, index_col=False, header=None)[0])
    latestIpSet = set(pd.read_csv(latestFile, index_col=False, header=None)[0])
    # print(lastIpSet)
    # print(latestIpSet)
    # print(lastIpSet == latestIpSet)
    return(lastIpSet == latestIpSet)

def annotationsAndDeltas(lastFile, latestFile, addFile, delFile):
    # in this we will read the last and latest into dataframes
    # compare those and if they are the same, we quit
    # if they are not, then we annotate, then create the delta Add and Delete files
    # will need to add try/except for IO errors
    lastdf = pd.read_csv(lastFile, index_col=False, header=None, names=["IP", "BlackList"])
    lastdf['BlackList'] = "Talos Black List" 
    lastdf['VRF'] = "Default"
    latestdf = pd.read_csv(latestFile, index_col=False, header=None, names=["IP", "BlackList"])
    latestdf['BlackList'] = "Talos Black List" 
    latestdf['VRF'] = "Default"
    header = ["IP", "VRF", "Black List"]
    lastdf.to_csv("last.csv", index=False, columns=header)
    latestdf.to_csv("latest.csv", index=False, columns=header)
    
    deltaDeleteDf = lastdf[~lastdf.IP.isin(latestdf.IP)].dropna()
    mergeDf = lastdf.merge(latestdf, indicator=True, how='outer')
    deltaAddDf = mergeDf[mergeDf['_merge'] == 'right_only'].ix[:,:-1]

    deltaDeleteDf = deltaDeleteDf[header]
    deltaDeleteDf.to_csv("deltaDelete.csv", index=False)
    deltaAddDf = deltaAddDf[header]
    deltaAddDf.to_csv("deltaAdd.csv", index=False)

def uploadAdditions(tetEndpoint, tetKey, tetSecret, addFile):
    # upload added annotations to tetration

def uploadDeletions(tetEndpoint, tetKey, tetSecret, delFile):
    # upload added annotations to tetration

# make talosBlfUrl an ENV variable at some point??
# need to parameterize the Talos BLF URL as a var
talosBlfUrl = 'https://talosintelligence.com/documents/ip-blacklist'
# declare names of files 
# not sure if we should parameterize the last file or not...
lastTalosBlFile = 'lastTalosIp.csv'
# these files are only significant DURING an instantiation, don't need to declare outside of script
latestTalosBlFile = 'latestTalosIp.csv'
tempAnnotationsFile = ''
deltaDelFile = 'deltaDel.csv'
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

# check a function that compares the two IP lists, if they match, no need to go on
if (areLastAndLatestSame(lastTalosBlFile, latestTalosBlFile)):
    print("Files are the same, nothing to do. Exiting...")
    SystemExit
print("Files are different, let's do some annotating...")

# call function to add annotations to the last and latest files then compare them
annotationsAndDeltas(lastTalosBlFile, latestTalosBlFile, deltaAddFile, deltaDelFile)

# call function to upload add annotations file to tetration
uploadAdditions(deltaAddFile)

# call function to upload delete annotations file to tetration 
uploadDeletions(deltaDelFile)


# save current annotations to a file named "talosblf-last.csv"
# this file will be used in the next iteration 
# writeToLastTalosBlf(talosBlfContent)

