import pickle
import csv
import sys
import numpy
import math

from MaximallyConfusableSubsets import GetDistinguishers, GetPairwiseThemes, CheckThemeValidity
from maxunifiedmatching import *
from aStar_matching import *
from itertools import combinations

##Given a theme and a list of forms, returns a corresponding list of distinguishers
def GetDistinguishersforSet(theme, formlist):
    distinguishers = []
    for form in formlist:
        distinguishers.append(GetDistinguishers(theme, form))
        
    return(distinguishers)
    

##Given a set of forms, returns all possible themes for that set
def ExtractThemesforSet(s):
    pairwisethemes = set()
    for i in range(len(s)-1):
        for j in range(i+1, len(s)):
            pthemes = GetPairwiseThemes(s[i], s[j])
            for p in pthemes:
                pairwisethemes.add(p)
                
    possiblethemes = set()
    newthemes = pairwisethemes
    while newthemes:
        usefulpairs = combinations(newthemes, 2)
        possiblethemes.update(newthemes)
        newthemes = set()
        for a, b in usefulpairs:
            pairthemes = GetPairwiseThemes(a, b)
            for t in pairthemes:
                if t not in possiblethemes:
                    newthemes.add(t)
    
    themes = set()
    for p in possiblethemes:
        flag = False
        for form in s:
            if CheckThemeValidity(p, form)==False:
                flag = True
        
        if flag==False:
            themes.add(p)
    
    return(themes)
    
def CalculateEntropy(mcsets, plat):
    matrix = numpy.zeros(((len(plat)), len(mcsets)))
    
    for mcset_ix in range(len(mcsets)):
        setdists = []
        counts = []
        mcset = mcsets.pop()
        for r in range(len(plat)):
            rowforms = []
            rowdists = []
            for ix,col_id in enumerate(mcset):
                rowforms.append(plat[r][col_id])
            rowthemes = ExtractThemesforSet(rowforms)
            for t in rowthemes:
                rowdists.append(GetDistinguishersforSet(t, rowforms))
            setdists.append(rowdists)
    
        counts = [1 for c in range(len(plat))]
    
        for i,j in ((i,j) for i in range(len(plat)-1) for j in range(i+1, len(plat))): #iterate through all combinations of rows
            for i_dists, j_dists in ((i_dists, j_dists) for i_dists in setdists[i] for j_dists in setdists[j]): #iterate through all possible distinguisher sets
                match = True

                for d in range(len(i_dists)): #iterate through the forms in a given distinguisher set
                    if not i_dists[d].intersection(j_dists[d]):
                        match = False
            
                if match==True:
                    counts[i]+=1
                    counts[j]+=1
                    break
    
        for val in range(len(counts)):
            matrix[val][mcset_ix] = math.log(counts[val], 2)
            
        #print("entropy for mcset", mcset_ix, "done")

    return(matrix)
    
    
def CalculateEntropy_Deidentified(plat, dists):
    matrix = numpy.zeros(((len(plat)), len(dists)))
    
    for mcset_ix, mcset in enumerate(dists):
        #print("mcset:", mcset)
        setdists = dists[mcset]
        #print("set dists:", setdists)
        
        counts = [1 for c in range(len(plat))]
        
        for i,j in ((i,j) for i in range(len(plat)-1) for j in range(i+1, len(plat))):
            match = True
            
            mx = MaxMatchNode(0, [setdists[i], setdists[j]], [0 for x in range(len(mcset))])
            match_result = aStar_match(mx, verbose=0)
            matchcols = extractMatch(match_result)
            
            if len(matchcols)!=len(mcset):
                match = False
                
            if match==True:
                counts[i]+=1
                counts[j]+=1  
        
        #print("counts:", counts)
            
        for val in range(len(counts)):
            matrix[val][mcset_ix] = math.log(counts[val], 2)
            
        #print("entropy values:", matrix[:, mcset_ix])
        #print("entropy for mcset", mcset_ix, "done")
            
    return(matrix)


##User must provide plat as a .csv file, mcsets as a .dump file, and deidentified distinguishers as a .dump file
if __name__ == "__main__":
    file = sys.argv[1]
    mcsets = pickle.load(open(sys.argv[2], "rb"))
    dists = pickle.load(open(sys.argv[3], "rb"))

    with open(file, encoding="utf8") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        next(csvreader, None)
        plat = list(csvreader)
           
        #for normal mcsets 
        matrix1 = CalculateEntropy(mcsets, plat)
        pickle.dump(matrix1, open("entropymatrix.dump", "wb"))
        
        #for deidentified mcsets
        matrix2 = CalculateEntropy_Deidentified(plat, dists)
        pickle.dump(matrix2, open("entropymatrix_deidentified.dump", "wb"))
