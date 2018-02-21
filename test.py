import json
import os
import requests
import tetpyclient
import csv
import pandas as pd 
import numpy as np

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


getDeltaFiles('talosblf-last.csv','talosblf-latest.csv','deltaDeleteFile.csv')
