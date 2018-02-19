import json
import os
import requests
import tetpyclient
import csv
import pandas as pd 
import numpy as np

def getDeltaDelete(lastfile,latestfile,delFile):
    # dump the two files into pandas(memory) and compare
    # stuff to delete will be in latest-last = deltaDelete
    # if nothing in last, then all of latest will go into 
# useless    lastset = set(pd.read_csv(lastfile, index_col=False, header=None)[0])
# useless   latestset = set(pd.read_csv(latestfile, index_col=False, header=None)[0])
    lastdf = pd.read_csv(lastfile, index_col=False, header=None, names=["IP", "Black List"])
    lastdf['Black List'] = "Talos BLF" 
    latestdf = pd.read_csv(latestfile, index_col=False, header=None, names=["IP", "Black List"])
    latestdf['Black List'] = "Talos BLF" 
    header = ["IP", "Black List"]
    lastdf.to_csv("last.csv", index=False, columns=header)
    latestdf.to_csv("latest.csv", index=False, columns=header)

    deltaDelDf = lastdf - latestdf
    deltaDelDf['Black List'] = "Talos BLF" 
    header = ["IP", "Black List"]
    deltaDelDf.to_csv("deltaDel.csv", index=False, columns=header)

    deltaAddDf = latestdf - lastdf
    deltaAddDf['Black List'] = "Talos BLF" 
    header = ["IP", "Black List"]
    deltaAddDf.to_csv("deltaAdd.csv", index=False, columns=header)


#    deleteSet = lastset - latestset
#    print("/n".join(str(x) for x in deleteSet))
#    addSet = latestset - lastset
#    print("/n".join(str(x) for x in addSet))
    #print(latestset)
    #print("last-latest = delete")
    #print(lastset-latestset)
    #print("latest-last = adds")
    #print(latestset-lastset)
    
getDeltaDelete('talosblf-last.csv','talosblf-latest.csv','deltaDeleteFile.csv')
