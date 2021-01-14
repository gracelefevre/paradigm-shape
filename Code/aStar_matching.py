from collections import defaultdict, Counter
import random
from heapq import *
from EditDistanceWithAlignment import *
import sys

class MaxMatchNode:
    def __init__(self, value, data, probvars, assnmts={}):
        """value: current number of cols matched
        data: columns in problem
        probvars: 0 for undecided, -1 for no match, 1 for match
        assnmts: variable-to-variable matching
        """
        self.value = value
        self.data = data
        self.probvars = probvars
        self.assnmts = assnmts
        self.hVal = None
        
    def __str__(self):
        res = "[%d/%d] " % (-self.value, -self.heuristic())
        for p in self.probvars:
            res += "%i " % p

        res += "{" + ", ".join(["%s=%s" % (kk, vv) for kk, vv in self.assnmts.items()]) + "}"
        return res

    def complete(self):
        for p in self.probvars:
            if p == 0: #check if any columns still unknown
                return False

        return True

    def key(self):
        return tuple(self.probvars)

    def priority(self):
        return self.value + self.heuristic()

    def __eq__(self, other):
        return self.key() == other.key()

    def __lt__(self, other):
        return (self.priority() < other.priority())

    def heuristic(self):
        if self.hVal is not None:
            return self.hVal
        else:
            self.hVal = self.computeHeuristic()
            return self.hVal    
    
    def computeHeuristic(self):
        scores = 0
        
        for p in self.probvars:
            if p==0:
                scores-=1
        
        return(scores)
            
    def successors(self):           
        res = []

        newcol = self.probvars.index(0) #find first instance of zero
            
        #the new column not matching is always a possible successor
        s0 = self.probvars[:]
        s0[newcol] = -1
        newassnmts = dict(self.assnmts.items())
        res.append(MaxMatchNode(self.value, self.data, s0, newassnmts))

        #update assignments for new column matching    
        newassnmts = dict(self.assnmts.items())
        assignedBs = set(newassnmts.values())

        s1 = self.probvars[:]
        s1[newcol] = 1

        col1 = self.data[0][newcol]
        col2 = self.data[1][newcol]
        
        for ci, cj in zip(col1, col2):
            ciVal = newassnmts.get(ci, None)
            #print("matching up", ci, cj, ciVal)

            if ciVal is None and cj not in assignedBs:
                newassnmts[ci] = cj #update
                assignedBs.add(cj)
            elif ciVal != cj:
                return res #already has a value and it's bad

        #go through remaining columns: which are still unassigned?
        for col, current in enumerate(s1):
            if current == 0:
                col1 = self.data[0][col]
                col2 = self.data[1][col]
                matched = 1
                for ci, cj in zip(col1, col2):
                    ciVal = newassnmts.get(ci, None)
                    if ciVal is None and cj not in assignedBs:
                        matched = 0
                        break
                    elif ciVal != cj:
                        matched = -1
                        break

                s1[col] = matched

        #a successor matching is possible only if it passed the earlier check
        res.append(MaxMatchNode(-s1.count(1), self.data, s1, newassnmts))

        return res

class PriorityQueue:
    #see https://docs.python.org/3.8/library/heapq.html
    def __init__(self):
        self.heap = []
        self.entries = {}

    def __len__(self):
        return len(self.entries)

    def add(self, entry):
        if entry.key() in self.entries:
            self.remove(entry)

        self.entries[entry.key()] = entry
        entry.valid = True
        heappush(self.heap, entry)

    def remove(self, entry):
        current = self.entries.get(entry.key())
        if current is not None:
            current.valid = False
            del self.entries[entry.key()]

    def update(self, entry):
        current = self.entries.get(entry.key())            
        if current and (entry.priority() < current.priority()):
            self.remove(entry)
            self.add(entry)
        elif not current:
            self.add(entry)

    def popMin(self):
        while self.heap:
            nxt = heappop(self.heap)
            if nxt.valid:
                self.remove(nxt)
                return nxt

def aStar_match(node, verbose=False):
    queue = PriorityQueue()
    best = node
    steps = 0
    
    while not best.complete():
        for succ in best.successors():
            #print("\t\t", succ)
            queue.update(succ)
            
        best = queue.popMin()
        if verbose > 1:
            print("queue size", len(queue), "current priority", best.priority())
            print(best)

        steps += 1

    if verbose:
        print("finished in", steps, "steps with max match value", -best.value)

    return best

def extractMatch(node):
    cols = node.probvars
    match = []
    for ix, c in enumerate(cols):
        if c==1:
            match.append(ix)
        
    return match


def printMatch(data, node):
    cols = node.probvars
    matchingcols = [[], []]
    
    for r in range(2):
        for ix, val in enumerate(data[r]):
            if cols[ix]==1:
                matchingcols[r].append(val)
                
    print(matchingcols)
    print("under matching", end=" ")
    for ai1, ai2 in node.assnmts.items():
        print(ai1, "=", ai2, end=", ")
    print()
    print()


if __name__ == "__main__":
    #trivially matches
    data = [[[1, 2], [2, 3], [3, 4]], [[1, 2], [2, 3], [3, 4]]]
    mx = MaxMatchNode(0, data, [0 for x in range(len(data[0]))])
    match = aStar_match(mx, verbose=1)
    printMatch(data, match)
    
    #trivially matches
    data = [[[1, 2], [2, 3], [3, 4]], [[9, 10], [10, 11], [11, 12]]]
    mx = MaxMatchNode(0, data, [0 for x in range(len(data[0]))])
    match = aStar_match(mx, verbose=1)
    printMatch(data, match)

    #only one matches
    data = [[[1, 2], [2, 3], [3, 4]], [[9, 10], [9, 10], [9, 10]]]
    mx = MaxMatchNode(0, data, [0 for x in range(len(data[0]))])
    match = aStar_match(mx, verbose=1)
    printMatch(data, match)
    
    #two match
    data = [[[1, 2], [2, 3], [3, 4]], [[9, 10], [10, 11], [9, 10]]]
    mx = MaxMatchNode(0, data, [0 for x in range(len(data[0]))])
    match = aStar_match(mx, verbose=1)
    printMatch(data, match)
    
    #three match
    data = [[[1, 2],  [2, 3],    [3, 4],   [1, 4]],
            [[9, 10], [10, 11], [12, 11], [9, 11]]]
    mx = MaxMatchNode(0, data, [0 for x in range(len(data[0]))])
    match = aStar_match(mx, verbose=1)
    printMatch(data, match)

    
    #same three match but the second and fourth columns have swapped positions
    data = [[[1, 2], [3, 4], [1, 4], [2,3]], [[9, 10], [12, 11], [9, 11], [10,11]]]
    mx = MaxMatchNode(0, data, [0 for x in range(len(data[0]))])
    match = aStar_match(mx, verbose=1)
    printMatch(data, match)
