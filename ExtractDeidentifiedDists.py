import pickle
import csv
import random
import sys

from MaximallyConfusableSubsets_Deidentified import *
from approximateMultialign import *
from itertools import combinations

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


def GetDists(mcsets, rows):
    mcsets_list = list(mcsets)
    
    for m in range(len(mcsets)):
        for r in range(len(rows)):
            forms = []
            dists = []
            for col_ix in mcsets_list[m]:
                forms.append(rows[r][col_ix])
                            
            theme_options = ExtractThemesforSet(forms)
            theme = ''.join(random.sample(theme_options, 1))
            
            for f in forms:
                d = GetDistinguishers(theme, f)
                dists.append(''.join(random.sample(d, 1)))
            
            e = approximateMultialign(dists)
            
            yield(mcsets_list[m],r,e)
            
    

#User must provide plat as a .csv file and deidentified mcsets as a .dump file
if __name__ == "__main__":
    file = sys.argv[1]

    with open(file, encoding="utf8") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        next(csvreader, None)
        rows = list(csvreader)
        
        mcsets = pickle.load(open(sys.argv[2], "rb"))
        dists = GetDists(mcsets, rows)
        
        #print(list(dists))   
        pickle.dump(list(dists), open("deidentified_dists.dump", "wb"))
                
        
        
