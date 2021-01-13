import pulp

def maxUnifiedMatching(rowA, rowB):
    """Assume each row is list of list of int, 1 sublist per column
    Match as many sublists as possible; all terms within the column
    have to match."""

    asyms = set()
    for col in rowA:
        asyms.update(col)

    bsyms = set()
    for col in rowB:
        bsyms.update(col)

    #step 1: define problem variables
    #---------------------------------
    #let m_i = 1 if column i matches
    ms = []
    for col in range(len(rowA)):
        ms.append(pulp.LpVariable("m_%d" % col,
                                  0, 1, "Binary"))

    #let x_{ij} = 1 if symbol i matches symbol j
    syms = {}
    for sa in asyms:
        for sb in bsyms:
            syms[sa, sb] = pulp.LpVariable("x_%d_%d" % (sa, sb),
                                           0, 1, "Binary")

    #step 2: set up objective
    #--------------------------
    #we want to maximize the number of matched items
    problem = pulp.LpProblem("maxmatch", pulp.LpMaximize)
    problem += sum(ms)
    
    #step 3: set constraints
    #------------------------

    #if we match a column, we must match all its terms
    #we can express this as m_i <= x_{sj,sk} for all sj, sk in the column
    #this means if we make m_i = 1, all the xs have to be 1 as well
    
    for col, (cA, cB) in enumerate(zip(rowA, rowB)):
        if len(cA) != len(cB):
            problem.add( ms[col] == 0)
        else:
            for sA, sB in zip(cA, cB):
                problem.add( ms[col] <= syms[sA, sB])

    #no more than one sb can correspond to any sa
    for sa in asyms:
        allVars = []
        for sb in bsyms:
            allVars.append(syms[sa, sb])
        
        if allVars:
            problem.add( sum(allVars) <= 1)

    #and vice-versa
    for sb in bsyms:
        allVars = []
        for sa in asyms:
            allVars.append(syms[sa, sb])

        if allVars:
            problem.add( sum(allVars) <= 1)


    #step 4: press the button and pray
    problem.solve()
    status = pulp.LpStatus[problem.status]
    assert(status == "Optimal")

    #step 5: figure out what happened-- which columns are included in solution?
    res = []
    
    for ii, mi in enumerate(ms):
        if mi.varValue > 0:
            res.append(ii)

    return res

if __name__ == "__main__":
    #trivially matches
    rowA = [[1, 2], [2, 3], [3, 4]]
    rowB = [[1, 2], [2, 3], [3, 4]]

    match = maxUnifiedMatching(rowA, rowB)
    print(match)

    #trivially matches
    rowA = [[1, 2], [2, 3], [3, 4]]
    rowB = [[9, 10], [10, 11], [11, 12]]

    match = maxUnifiedMatching(rowA, rowB)
    print(match)

    #only one matches
    rowA = [[1, 2], [2, 3], [3, 4]]
    rowB = [[9, 10], [9, 10], [9, 10]]

    match = maxUnifiedMatching(rowA, rowB)
    print(match)

    #two match
    rowA = [[1, 2], [2, 3], [3, 4]]
    rowB = [[9, 10], [10, 11], [9, 10]]

    match = maxUnifiedMatching(rowA, rowB)
    print(match)

    #three match
    rowA = [[1, 2], [2, 3], [3, 4], [1, 4]]
    rowB = [[9, 10], [10, 11], [12, 11], [9, 11]]

    match = maxUnifiedMatching(rowA, rowB)
    print(match)

    #rowA = [[2, 1], [2, 1]]
    #rowB = [[4, 2, 1], [3, 2, 1]]
    #match = maxUnifiedMatching(rowA, rowB)
    #print(match)
    
    #rowA = [[], []]
    #rowB = [[4, 3, 1], [3, 2, 1]]
    #match = maxUnifiedMatching(rowA, rowB)
    #print(match)