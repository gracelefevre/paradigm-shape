import csv
import sys
from itertools import combinations, permutations
import pickle
from approximateMultialign import *
from maxunifiedmatching import *
from aStar_matching import *
import random

#Goal: identify maximally confusable subsets of the plat

cache = {}

##Returns minimum edit distance and all possible alignments for a pair of forms
def EditDistanceWithAlignment(s1, s2, level=0):
    if(len(s1)==0):
        return len(s2), set([
            (tuple(), tuple([(char, False) for char in s2]))
            ])
    if(len(s2)==0):
        return len(s1), set([
            (tuple([(char, False) for char in s1]), tuple())    
            ])
    if(s1, s2) in cache:
        return cache[(s1, s2)]
  
    if(s1[-1]==s2[-1]):
        cost = 0
    else:
        cost = 2

    op1, solutions1 = EditDistanceWithAlignment(s1[:-1], s2, level=level + 1)
    op2, solutions2 = EditDistanceWithAlignment(s1, s2[:-1], level=level + 1)
    op3, solutions3 = EditDistanceWithAlignment(s1[:-1], s2[:-1], level=level + 1)

    op1 += 1
    op2 += 1
    op3 += cost

    solutions = set()
    mincost = min(op1, op2, op3)

    if op1==mincost:
        for (sol1, sol2) in solutions1:
            solutions.add( (sol1 + ((s1[-1], False),), sol2) )
    if op2==mincost:
        for (sol1, sol2) in solutions2:
            solutions.add( (sol1, sol2 + ((s2[-1], False),)) )
    if op3==mincost and cost==0:
        for (sol1, sol2) in solutions3:
            solutions.add( (sol1 + ((s1[-1], True),), sol2 + ((s2[-1], True),)) )
    if op3==mincost and cost>0:
        for (sol1, sol2) in solutions3:
            solutions.add( (sol1 + ((s1[-1], False),), sol2 + ((s2[-1], False),)) )
    cache[(s1, s2)] = (mincost, solutions)
    
    return mincost, solutions


##Extracts theme from two given alignments
def Theme(alignment1, alignment2):
    theme = []
    for (char, alt) in alignment1:
        if alt:
            theme.append(char)
    return theme


##Returns list of all possible themes for a pair of forms
def GetPairwiseThemes(form1, form2):
    mincost, solutions = EditDistanceWithAlignment(form1, form2)
    
    themes = []
    for ix, sol in enumerate(solutions):
        alignments = []
        for ix2, al in enumerate(sol):
            alignments.append(al)
        theme = "".join(Theme(alignments[0], alignments[1]))    
        themes.append(theme)
    
    #if len(themes)>3:
        #print("Warning:", form1, "and", form2, "have", len(themes), "pairwise themes")
    
    return(themes)
    

##Returns list of all possible themes for a row (microclass)
def ExtractThemesforRow(row):
    pairwisethemes = set()
    for i in range(1, len(row)-1):
        for j in range(i+1, len(row)):
            pthemes = GetPairwiseThemes(row[i], row[j])
            for p in pthemes:
                pairwisethemes.add(p)
                
    themes = set()
    newthemes = pairwisethemes
    while newthemes:
        usefulpairs = combinations(newthemes, 2)
        themes.update(newthemes)
        newthemes = set()
        for a, b in usefulpairs:
            pairthemes = GetPairwiseThemes(a, b)
            for t in pairthemes:
                if t not in themes:
                    newthemes.add(t)
    
    return(themes)
    
    
    
##Returns boolean value indicating whether a given theme is valid for a particular form
def CheckThemeValidity(theme, form):
    check = GetPairwiseThemes(theme, form)    
    valid = True
    
    for i in range(len(check)):
        if check[i]!=theme:
            valid = False

    return(valid)


##Given a theme and a form, returns the corresponding distinguisher in string format
def GetDistinguishers(theme, form):
    mincost, solutions = EditDistanceWithAlignment(theme, form)
    alignments = []
    distinguishers = set()
            
    for ix, sol in enumerate(solutions):
        for ix2, al in enumerate(sol):
            alignments.append(al)
        
    if CheckThemeValidity(theme, form)==False:
        print("Error:", theme, "is not a theme for", form)        
    else:
        for i in range(1, len(alignments), 2):
            dist = []
            for (char, alt) in alignments[i]:
                if alt==False:
                    dist.append(char)
            distinguishers.add("".join(dist))
        
        return(distinguishers)
        
        
##Given a distinguisher and a form, returns the corresponding theme in string format
def GetThemes(dist, form):
    mincost, solutions = EditDistanceWithAlignment(dist, form)
    alignments = []
    themes = set()
    
    for ix, sol in enumerate(solutions):
        for ix2, al in enumerate(sol):
            alignments.append(al)
            
    for i in range(1, len(alignments), 2):
        theme = []
        for (char, alt) in alignments[i]:
            if alt==False:
                theme.append(char)
        themes.add("".join(theme))
        
    return(themes)
    

##Returns the largest possible subset of forms for every theme for every row of the plat as a list of dictionaries
def GetLargestSetsbyTheme(rows):
    themes_byrow = []
    subsets_bytheme = []

    for row in rows:
        themes_byrow.append(list(ExtractThemesforRow(row)))
        
    for r in range(len(themes_byrow)):
        rowsets = {}
        for theme in themes_byrow[r]:
            themeset = []
            for formidx in range(1, len(rows[r])):
                form = rows[r][formidx]
                if(CheckThemeValidity(theme, form)==True):
                    themeset.append(formidx)
            rowsets[theme]=themeset
        subsets_bytheme.append(rowsets)
            
    return(subsets_bytheme)      
    
    

def CompareTwoSets_Deidentified(row1, row2, theme1, subset1, theme2, subset2):
    cols = set()
    inter = set(subset1).intersection(subset2)
    dists1 = []
    dists2 = []
    col_keys = []
    deid_dists1 = []
    deid_dists2 = []
    
    #get distinguisher sets for both rows; randomly select a distinguisher if multiple options for a form
    for val in inter:
        d1 = GetDistinguishers(theme1, row1[val])
        d2 = GetDistinguishers(theme2, row2[val])
        dists1.append(''.join(random.sample(d1, 1)))
        dists2.append(''.join(random.sample(d2, 1)))

    e1 = approximateMultialign(dists1)
    e2 = approximateMultialign(dists2)
    
    #match column id numbers with deidentified distinguishers
    for ix in range(len(inter)):
        col_keys.append(list(inter)[ix])
        deid_dists1.append(e1[ix])
        deid_dists2.append(e2[ix])
        
    #match as many columns as possible
    mx = MaxMatchNode(0, [deid_dists1, deid_dists2], [0 for x in range(len(deid_dists1))])
    match = aStar_match(mx, verbose=0)
    matchcols = extractMatch(match)
    
    for m in matchcols:
        cols.add(col_keys[m])
        
    return(cols)    
    
    
    
##For two rows, returns their maximally confusable subsets calculated according to the deidentified distinguisher sets
def CompareTwoRows_Deidentified(row1, row2, subsets_bytheme1, subsets_bytheme2):
    mcsets = []
    themes1 = []  
    themes2 = []
    
    #Get themes for both rows
    for t1 in subsets_bytheme1:
        themes1.append(t1)
            
    for t2 in subsets_bytheme2:
        themes2.append(t2)
                
    #Compare every possible combinations of themes between the two rows
    for i in range(len(themes1)):
        for j in range(len(themes2)):
            comp = CompareTwoSets_Deidentified(row1, row2, themes1[i], subsets_bytheme1[themes1[i]], themes2[j], subsets_bytheme2[themes2[j]])
            if comp and comp not in mcsets and len(comp)>1:
                mcsets.append(comp)

    for a, b in permutations(mcsets, 2):
        if a.issubset(b) == True and a in mcsets:
            mcsets.remove(a)
            
    #print(mcsets)
    return(mcsets)
    

##Returns all possible maximally confusable subsets (by plat column id numbers) for every row in the plat
def FindMaximallyConfusableSubsets_Deidentified(rows):
    subsets_bytheme = GetLargestSetsbyTheme(rows)
    mcsets_byrow = {}
    mcsets = set()

    print("Sets by theme computed")
    
    for i in range(len(rows)):
        print(i)
        mcsets_byrow[i+1] = []
        for j in range(i + 1, len(rows)):
            print("\t", j)
            pairwisesets = CompareTwoRows_Deidentified(rows[i], rows[j], subsets_bytheme[i], subsets_bytheme[j])
            for p in range(len(pairwisesets)):
                if pairwisesets[p] not in mcsets_byrow[i+1] and len(pairwisesets[p])>1:
                    mcsets_byrow[i+1].append(frozenset(pairwisesets[p]))
    
    #print("Pairwise MC sets calculated")

    mcsets = set()

    for row in range(1, len(mcsets_byrow)+1):
        newsets = set(mcsets_byrow[row])
        while newsets:
            usefulsets = combinations(newsets, 2)
            mcsets.update(newsets)
            newsets = set()
            
            for u in usefulsets:
                ulist = []
                for s in u:
                    ulist.append(s)
                inter = frozenset.intersection(*ulist)
                if len(inter)>1:
                    newsets.add(inter)
                        
        #print("Row", row, "calculations finished")

    return(mcsets)


##User must provide plat in csv format as input
if __name__ == "__main__":
    file = sys.argv[1]

    with open(file, encoding="utf8") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        next(csvreader, None)
        rows = list(csvreader)
        mcsets = FindMaximallyConfusableSubsets_Deidentified(rows)

        print("Number of maximally confusable sets (deid):", len(mcsets))
        print("Maximally confusable sets by column index:", mcsets)
        pickle.dump(mcsets, open("mcsets_deidentified.dump", "wb"))