import json
import os
import requests
import tetpyclient
from tetpyclient import RestClient
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

# create tetration rest client
def createRestClient(tetEndpoint, tetKey, tetSecret):
    rc = RestClient(tetEndpoint, api_key=tetKey, api_secret=tetSecret, verify=False)
    return rc

# the function getblf will grab a blf from a url 
def getBlf(url, latestFile):
    # need to put in try/excecpt function for something other than 200 response code
    blf = requests.get(url)
    return (blf.content)

# a function to write the content from the  BLF to 
def writeToLatestBlf(content,filename):
    # write the BLF to a file named by filename parm
    # will need to put an ENV variable for the public folder path on the ecoHub
    # need to put try/except for io errors
    with open(filename,'wb') as f:
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
    return(lastIpSet == latestIpSet)

def annotationsAndDeltas(lastFile, latestFile, addFile, delFile):
    # in this we will read the last and latest into dataframes
    # compare those and if they are the same, we quit
    # if they are not, then we annotate, then create the delta Add and Delete files
    # will need to add try/except for IO errors
    lastdf = pd.read_csv(lastFile, index_col=False, header=None, names=["IP", "BlackList"])
    lastdf["BlackList"] = "Talos Black List" 
    lastdf["VRF"] = "Default"
    latestdf = pd.read_csv(latestFile, index_col=False, header=None, names=["IP", "BlackList"])
    latestdf["BlackList"] = "Talos Black List" 
    latestdf["VRF"] = "Default"
    header = ["IP", "VRF", "BlackList"]
    lastdf.to_csv("templast.csv", index=False, columns=header)
    latestdf.to_csv("templatest.csv", index=False, columns=header)
    
    deltaDeleteDf = lastdf[~lastdf.IP.isin(latestdf.IP)].dropna()
    mergeDf = lastdf.merge(latestdf, indicator=True, how='outer')
    deltaAddDf = mergeDf[mergeDf['_merge'] == 'right_only'].ix[:,:-1]

    deltaDeleteDf = deltaDeleteDf[header]
    deltaDeleteDf.to_csv(delFile, index=False)
    deltaAddDf = deltaAddDf[header]
    deltaAddDf.to_csv(addFile, index=False)

def uploadAdditions(rc, addFile):
    # upload added annotations to tetration
    keys = ['IP', 'VRF']
    req_payload = [tetpyclient.MultiPartOption(key='X-Tetration-Key', val=keys), tetpyclient.MultiPartOption(key='X-Tetration-Oper', val='add')]
    resp = rc.upload(addFile, '/assets/cmdb/upload', req_payload)
    if resp.status_code != 200:
        print("Error posting annotations to Tetration cluster")
        print(resp.status_code)
        print(resp.text)
    else:
        print(resp.status_code)
        print(resp.text)
        print("Successfully posted additions to Tetration cluster using file", addFile)

def uploadDeletions(rc, delFile):
    # upload added annotations to tetration
    keys = ['IP', 'VRF']
    req_payload = [tetpyclient.MultiPartOption(key='X-Tetration-Key', val=keys), tetpyclient.MultiPartOption(key='X-Tetration-Oper', val='delete')]
    resp = rc.upload(delFile, '/assets/cmdb/upload', req_payload)
    if resp.status_code != 200:
        print("Error posting annotations to Tetration cluster")
        print(resp.status_code)
        print(resp.text)
    else:
        print(resp.status_code)
        print(resp.text)
        print("Successfully posted deletions to Tetration cluster using file", delFile)

def checkCsvContent(csvFile):
    nRowCsvIterate = 0
    with open(csvFile, 'r') as countFile:
        csv_rows = csv.reader(countFile)
        for row in csv_rows:
            if len(row) > 0:
                # print(len(row))
                # print(row)
                nRowCsvIterate += 1
    print("number of rows iterated with csv.reader:", nRowCsvIterate)
    if nRowCsvIterate > 1:
        return(True)
        #print("I'd upload some stuff now.")
    else:
        return(False)
        #print("I would NOT upload anything now.")

def checkBlfFacet(rc):
    resp = rc.get('/assets/cmdb/annotations/default')
    if resp.status_code != 200:
        print("Error getting annotations from Tetration cluster:", resp.status_code, resp.text)
        print(resp.status_code)
        print(resp.text)
    else:
        facetsList = resp.text
        if "BlackList" in (facetsList):
            print ("BlackList is already enabled, moving on")
        else:
            print("BlackList is not enabled, enabling")
            facetsList.append("BlackList")
            req_payload = facetsList
            rc.put('/assets/cmdb/annotations/Default', json_body=json.dumps(req_payload))

def fileCleanUp(lastFile, latestFile, deltaAddFile, deltaDelFile):
    os.remove('templast.csv')
    os.remove('templatest.csv')
    os.remove(deltaAddFile)
    os.remove(deltaDelFile)
    os.remove(lastFile)
    os.rename(latestFile, lastFile)


''' 
-----------------------------------------------------------
 begin globals section
-----------------------------------------------------------
'''

# make talosBlfUrl an ENV variable at some point??
# need to parameterize the Talos BLF URL as a var
talosBlfUrl = 'https://talosintelligence.com/documents/ip-blacklist'
# declare names of files 
# need to parameterize the lastTalosBLFile - it should persist
lastTalosBlFile = 'lastTalosIp.csv'
# these files are only significant DURING an instantiation, don't need to declare outside of script
latestTalosBlFile = 'latestTalosIp.csv'
deltaDelFile = 'deltaDel.csv'
deltaAddFile = 'deltaAdd.csv'

# perseus endpoint and keys
''' 
tetrationEndpoint = 'https://perseus-aus.cisco.com'
tetrationKey = 'a0d9299aaf7a49cab92150aaf2f7e50b'
tetrationSecret = '14ae32d279489ab5cc67b73b6777bdcc963b4817'
'''

# andromeda endpoint and keys
tetrationEndpoint = 'https://andromeda.auslab.cisco.com'
tetrationKey = '566a39a28ef74775a16b650dd6b5359d'
tetrationSecret = '4363de8f75d4e374ad64034b14fe2951e0d34bed'

requests.urllib3.disable_warnings()

''' 
-----------------------------------------------------------
 end globals section
-----------------------------------------------------------
'''
# initialize rc client
rc = createRestClient(tetrationEndpoint, tetrationKey, tetrationSecret)


# call function to grab the BLF from the Talos Reputation Center URL
latestTalosBlf = (getBlf(talosBlfUrl, latestTalosBlFile))
writeToLatestBlf(latestTalosBlf, latestTalosBlFile)

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

# check to see if last is empty, then run a check function that compares the 
# two IP lists, if they match, no need to go on
if not (os.stat(lastTalosBlFile).st_size==0):
    if (areLastAndLatestSame(lastTalosBlFile, latestTalosBlFile)):
        print("Files are the same, nothing to do. Exiting...")
        SystemExit
print("Files are different, let's do some annotating...")

# call function to add annotations to the last and latest files then compare them
annotationsAndDeltas(lastTalosBlFile, latestTalosBlFile, deltaAddFile, deltaDelFile)

# call function to upload add annotations file to tetration
uploadAdditions(rc, deltaAddFile)

# call function to upload delete annotations file to tetration 
'''
if checkCsvContent(deltaDelFile):
    uploadDeletions(rc, deltaDelFile)
'''
uploadDeletions(rc, deltaDelFile)

# Check to see if the BlackList annotation has been enabled in the annotation facets, if not, enable it
# this may not be needed any more... ?
# checkBlfFacet(rc)

# save current annotations to a file named "talosblf-last.csv"
# this file will be used in the next iteration 
# fileCleanUp(lastTalosBlFile, latestTalosBlFile, deltaAddFile, deltaDelFile)
