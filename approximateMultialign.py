from multialign import *
import sys
import random
import pickle
import numpy as np

class ExtendAlignNode:
    def __init__(self, cost, ptr, layer, solution, string, charAtLayer):
        self.cost = cost
        self.ptr = ptr
        self.layer = layer
        self.solution = solution
        self.string = string
        self.charAtLayer = charAtLayer
        self.heuristic = self.computeHeuristic()

    def successors(self):
        res = []
        #we can align the next char at any position it matches
        #or give it its own symbol
        nextChar = self.string[self.ptr]
        nextSym = self.layer - 1
        for layer in range(nextSym, 0, -1):
            charAtLayer = self.charAtLayer[layer]
            if charAtLayer == nextChar:
                newSol = self.solution[:] + [layer]
                res.append(ExtendAlignNode(self.cost, self.ptr + 1, layer, newSol, self.string, self.charAtLayer))

        newSol = self.solution[:] + ["NSYM"]
        res.append(ExtendAlignNode(self.cost + 1, self.ptr + 1, self.layer, newSol, self.string, self.charAtLayer))

        return res

    def __str__(self):
        res = "[%d/%d] " % (self.cost, self.heuristic)
        for (si, pi) in zip(self.string, self.solution):
            res += "%s:%d " % (si, pi)
        return res

    def complete(self):
        return self.ptr == len(self.string)

    def key(self):
        return self.ptr, tuple(self.solution)

    def priority(self):
        return self.cost + self.heuristic, self.heuristic

    def __eq__(self, other):
        return self.key() == other.key()

    def __lt__(self, other):
        return (self.priority() < other.priority())

    def computeHeuristic(self):
        ownBag = {}
        for ch in self.string[self.ptr:]:
            ownBag[ch] = ownBag.get(ch, 0) + 1

        otherBag = {}
        for layer, ch in self.charAtLayer.items():
            if layer < self.layer:
                otherBag[ch] = otherBag.get(ch, 0) + 1
                
        res = 0
        for ch, ct in ownBag.items():
            val = ct - otherBag.get(ch, 0)
            if ct > 0:
                res += ct

        return res

def incrementAll(extracted, sym):
    for item in extracted:
        for ii in range(len(item)):
            if item[ii] >= sym:
                item[ii] += 1

def renumber(extracted, draftAssignments):
    for ii, sym in enumerate(draftAssignments):
        if sym == "NSYM":
            if ii == 0:
                prevSym = max([max(xx) for xx in extracted if len(xx)]) + 1
            else:
                prevSym = draftAssignments[ii - 1]

            incrementAll(extracted, prevSym)
            for jj in range(ii):
                draftAssignments[jj] += 1
            draftAssignments[ii] = prevSym

    return draftAssignments

def incrementalMerge(string, ind, strs, extracted):
    charAtLayer = {}
    for si, sol in zip(strs, extracted):
        #print(si, sol)
        for ch, layer in zip(si, sol):
            #print(ch, layer)
            assert(charAtLayer.get(layer, ch) == ch)
            charAtLayer[layer] = ch

    #for layer, ch in sorted(charAtLayer.items(), reverse=True):
    #    print(layer, "<->", ch)
    #print()

    node = ExtendAlignNode(0, 0, max(charAtLayer.keys()) + 1, [], string, charAtLayer)
    best = aStar(node, verbose=0)
    solution = best.solution
    #print("solution", solution)
    if "NSYM" in solution:
        solution = renumber(extracted, solution)

    extracted.append(solution)

def selectAndAlign(dists, verbose=False, nSelect=10):
    #I've also tried 25 as the initial selection
    if dists:
        maxSteps = 5000
    else:
        maxSteps = 100
    select = min(len(dists), nSelect)
    sol = None
    while True:
        if verbose:
            print("\tChecking with", select, "distinguishers")
        core = dists[:select]
        mx1 = MultiAlignNode(0, core, [0 for xx in range(len(core))], prev=None, action=[])
        sol = aStar(mx1, verbose=verbose, cutoff=maxSteps)
        if sol is not None:
            break

        if select > 4:
            select = select // 2
        else:
            maxSteps = None
        
    extracted = extract(sol)
    return select, extracted

def approximateMultialign(dists):
    original = list(enumerate(dists))
    byLength = sorted(original, key=lambda xx: len(xx[1]), reverse=True)
    dists = [xx[1] for xx in byLength]
    order = [xx[0] for xx in byLength]

    verbose = False #len(dists) > 25
    if verbose:
        print(len(dists), "distinguishers to process")

    select, extracted = selectAndAlign(dists, verbose=verbose)
    core = dists[:select]
    remaining = dists[select:]

    if verbose:
        print("\tFound initial solution with", select, "elements")
    #printAlignment2(core, extracted)

    for ii in range(select, len(dists)):
        si = dists[ii]
        #print("adding", si)

        incrementalMerge(si, ii, core, extracted)
        select += 1
        core = dists[:select]
        #print()
        #printAlignment2(core, extracted)
        #print()

    final = [None for xx in original]
    for index, sol in zip(order, extracted):
        final[index] = sol

    return final

if __name__ == "__main__":
    dists = pickle.load(open(sys.argv[1], 'rb'))
    print(len(dists))
    print(dists)

    sol = approximateMultialign(dists)
    print("final cost", max([ex[0] for ex in sol if ex]))
    print(sol)
    printAlignment2(dists, sol)

    reduceAdjacentSymbols(sol)
    assert(0)

    print("real alignment")

    mx1 = MultiAlignNode(0, dists, [0 for xx in range(len(dists))], prev=None, action=[])
    sol = aStar(mx1, verbose=1, cutoff=None)
    print(sol)
