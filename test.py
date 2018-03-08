import json
import os
import requests
import tetpyclient
from tetpyclient import RestClient
import csv
import pandas as pd 
import numpy as np
import csvdiff

def getDeltaFiles(lastfile,latestfile,delFile):
    # dump the two files into pandas(memory) and compare
    # stuff to delete will be in latest-last = deltaDelete
    # if nothing in last, then all of latest will go into 

    # read in 
    lastdf = pd.read_csv(lastfile, index_col=False, header=None, names=["IP", "BlackList"])
    lastdf['BlackList'] = "Talos Black List" 
    lastdf['VRF'] = "Default"
    latestdf = pd.read_csv(latestfile, index_col=False, header=None, names=["IP", "BlackList"])
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
    
    
# create tetration rest client
def createRestClient(tetEndpoint, tetKey, tetSecret):
    rc = RestClient(tetEndpoint, api_key=tetKey, api_secret=tetSecret, verify=False)
    return rc


def uploadDeletions(rc, delFile):
    # upload added annotations to tetration
    keys = ['IP', 'VRF', 'BlackList']
    req_payload = [tetpyclient.MultiPartOption(key='X-Tetration-Key', val=keys), tetpyclient.MultiPartOption(key='X-Tetration-Oper', val='delete')]
    resp = rc.upload(delFile, '/assets/cmdb/upload', req_payload)
    if resp.status_code != 200:
        print("Error posting annotations to Tetration cluster")
    else:
        print(resp.text)
        print("Successfully posted annotations to Tetration cluster")

def getUsers(rc):
    resp = rc.get('/users')
    print(resp.text)

def getFacets(rc):
    resp = rc.get('/assets/cmdb/annotations/default')
    if resp.status_code != 200:
        print("Error getting annotations from Tetration cluster")
        print(resp.status_code)
        print(resp.text)
    else:
        facetsList = resp.text
        print(facetsList)
        if "BlackList" in (facetsList):
            print ("It's in there, moving the fuck on")
        else:
            print("Nope, I don't see it, appending")
            facetsList.append("BlackList")
            req_payload = facetsList
            rc.put('/assets/cmdb/annotations/Default', json_body=json.dumps(req_payload))

def addBlfFacet(rc):
    resp = rc.get('/assets/cmdb/annotations/default')
    if resp.status_code != 200:
        print("Error getting annotations from Tetration cluster")
        print(resp.status_code)
        print(resp.text)
    else:
        facetsList = resp.text
        print(facetsList)
        if "BlackList" in (facetsList):
            print ("It's in there, moving the fuck on")
        else:
            print("Nope, I don't see it, appending")
            facetsList.append("BlackList")
            req_payload = facetsList
            rc.put('/assets/cmdb/annotations/Default', json_body=json.dumps(req_payload))

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
        print("I'd upload some stuff now.")
    else:
        print("I would NOT upload anything now.")







        
    





# code block from Brandon Beck - he's FUCKING awesome
'''
annotationUpdates = json.loads(body)

    existingAnnotations = list(db.annotations.find({},{'_id':0}))
    existing_df = pd.DataFrame(existingAnnotations)
    update_df = pd.DataFrame(annotationUpdates)

    removeIPList = existing_df[~existing_df.IP.isin(update_df.IP)]['IP'].dropna().T.to_dict().values()
    merged = existing_df.merge(update_df, indicator=True, how='outer')
    updateList = merged[merged['_merge'] == 'right_only'].ix[:,:-1].T.to_dict().values()
'''

#getDeltaFiles('talosblf-last.csv','talosblf-latest.csv','deltaDeleteFile.csv')


tetrationEndpoint = 'https://perseus-aus.cisco.com'
tetrationKey1 = '556f86c494d34ffc8063b0845c300de1'
tetrationSecret1 = 'a6a97010c6cba633d7ddbf10d8df40eb8d25484'
tetKey2 = 'a0d9299aaf7a49cab92150aaf2f7e50b'
tetSecret2 = '14ae32d279489ab5cc67b73b6777bdcc963b4817'

requests.urllib3.disable_warnings

# initialize rc client
#rc = createRestClient(tetrationEndpoint, tetKey2, tetSecret2)

#getUsers(rc)
#getFacets(rc)
#addBlfFacet(rc)
#getFacets(rc)

''' test add
keys = ['IP', 'VRF']
req_payload = [tetpyclient.MultiPartOption(key='X-Tetration-Key', val=keys), tetpyclient.MultiPartOption(key='X-Tetration-Oper', val='add')]
resp = rc.upload('deltaAdd.csv', '/assets/cmdb/upload', req_payload)
if resp.status_code != 200:
    print("Error posting annotations to Tetration cluster")
    print(resp.status_code)
    print(resp.text)
else:
    print(resp.status_code)
    print(resp.text)
    print("Successfully posted additions to Tetration cluster using file")
'''

''' test del
keys = ['IP', 'VRF']
req_payload = [tetpyclient.MultiPartOption(key='X-Tetration-Key', val=keys), tetpyclient.MultiPartOption(key='X-Tetration-Oper', val='delete')]
resp = rc.upload('deltaDelete.csv', '/assets/cmdb/upload', req_payload)
if resp.status_code != 200:
    print("Error posting annotations to Tetration cluster")
    print(resp.status_code)
    print(resp.text)
else:
    print(resp.status_code)
    print(resp.text)
    print("Successfully posted additions to Tetration cluster using file")
'''

checkCsvContent('test2.csv')

