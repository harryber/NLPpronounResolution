import json
import queue
import sys

from nltk import Tree

PLURALITY = {
    "NN":           0,
    "NNP":          0,
    "he":           0,
    "she":          0,
    "him":          0,
    "her":          0,
    "his":          0,
    "it":           0,
    "himself":      None,
    "herself":      None,
    "itself":       None,
    "NNS":          1,
    "NNPS":         1,
    "we":           1,
    "our":          1,
    "they":         1,
    "them":         1,
    "themselves":   1,
    "their":        1,
    "PRP":          None
}

REFLEXIVE = {
    'herself', 
    'himself', 
    'themself', 
    'themselves', 
    'itself', 
    'myself', 
    'yourself', 
    'yourselves'
}

names_f = set()
names_m = set()

def load_names(path):
    global names_f
    global names_m

    with open(path, 'rb') as f:
        names = json.load(f)
    
    for n in names:
        names_f.add(n.lower())

    for n in names:
        names_m.add(n.lower())

def is_np_or_s(tree: Tree):
    ''' Checks if a node is represents an NP or S '''
    return tree.label() == 'NP' or tree.label() == 'S'

def is_np(tree: Tree):
    ''' Checks if a node is represents an NP '''
    return tree.label() == 'NP'

def is_reflexive(pn: str):
    return pn in REFLEXIVE

def is_nominal(tree: Tree):
    ''' Checks if a node has a nominal label '''
    return tree.label() in {'NN', 'NNS', 'NNP', 'NNPS', 'PRP'}

def is_left_of_path(pos: tuple, path: 'list[tuple]'):
    ''' Checks if a position is left of a path '''
    return any([pos < p for p in path])

def climb_to_node(tree: Tree, pos: tuple) -> 'tuple[tuple, list[tuple]]':
    ''' 
    Climbs up tree from pos until a NP or S node is encountered.
    Returns the position of that node and the path to it.
    '''
    path = [pos]
    while len(pos) > 0:
        pos = pos[:-1]
        path.append(pos)

        if is_np_or_s(tree[pos]):
            return pos, path
        
    sys.exit('Did not find an NP or S while climbing tree')

def bfs(tree: Tree, pos: tuple = (), dir: int = -1) -> queue.Queue:
    ''' 
    Performs a BFS on a provided tree in left-to-right order.
    Optionally, takes a direction (0 = left, 1 = right) to search only to that side.
    Returns a queue of visited nodes' positions in order.
    '''
    subtree = tree[pos]

    if dir == 0 or dir == 1:
        subtree = subtree[dir]
        pos = pos + (dir,)

    visited = queue.Queue()
    visited.put(pos)

    q = queue.Queue()
    q.put(pos)

    while not q.empty():
        p = q.get()
        i = 0
        for child in tree[p]:
            if isinstance(child, Tree):
                visited.put(p + (i,))
                q.put(p + (i,))
                i += 1

    return visited

def propose(tree: Tree, pos: tuple, pn: str) -> bool:
    ''' 
    Takes a proposed antecedent and the target pronoun and 
    checks whether they match in gender and plurality.
    '''
    return _check_plurality(tree, pos, pn) and _check_gender(tree, pos, pn)

def _check_plurality(tree, pos, pn) -> bool:
    ''' Checks whether a proposed antecedent matches the plurality of the pronoun '''
    for c in tree[pos]:
        if isinstance(c, Tree) and is_nominal(c):
            if PLURALITY[c.label()] == PLURALITY[pn]:
                return True
    return False

def _check_gender(tree, pos, pn) -> bool:
    ''' Checks whether a proposed antecedent matches the gender of the pronoun '''
    global names_f
    global names_m

    male = ['he', 'him', 'himself']
    female = ['she', 'her', 'herself']
    inanimate = ['it', 'itself']

    for c in tree[pos]:
        if isinstance(c, Tree) and is_nominal(c):
            c_leaf = c.leaves()[0].lower()

            # check male name <-> female pronoun
            if c_leaf in names_m and c_leaf not in names_f:
                if pn in female or pn in inanimate:
                    return False
                
            # check female name <-> male pronoun
            if c_leaf in names_f and c_leaf not in names_m:
                if pn in male or pn in inanimate:
                    return False
                
    return True

def resolve_reflexive(tree: 'list[Tree]', pos: tuple, pn: str):
    ''' Resolves reflexive pronouns '''
    x, path = climb_to_node(tree, pos) # get dominating NP

    # climb to first S
    while is_np(tree[x]):
        x, new_path = climb_to_node(tree, x)
        path = path + new_path

    # search to left of path
    nodes = bfs(tree, x)
    while not nodes.empty():
        node_p = nodes.get()
        
        if is_left_of_path(node_p, path):
            if is_np(tree[node_p]) and propose(tree, node_p, pn):
                return tree, node_p
            
    return None, None

def hobbs(trees: 'list[Tree]', pos: tuple):
    ''' 
    Runs Hobbs' Algorithm given a list of parse trees and the position.
    Returns the proposed antecedent in the form (tree, position)
    '''

    tree = trees[-1] # start with last tree
    pn = tree[pos].leaves()[0].lower() # pronoun we are trying to resolve

    if is_reflexive(pn):
        return resolve_reflexive(tree, pos, pn)

    ### START AT NP OVER PRONOUN ###

    cur = pos[:-1] # go up once from pronoun

    ### CLIMB PARSE TREE UNTIL NP OR S, CALL THIS X ###

    cur, path = climb_to_node(tree, cur) # set cur to node X's position, get path

    ### BFS ALL BRANCHES BELOW X TO LEFT, PROPOSE ANY NP/S ###

    nodes = bfs(tree, cur, 0) # in-order list of node positions

    # check each node
    while not nodes.empty():
        node_p = nodes.get()
        if node_p not in path and node_p != pos:
            if is_np_or_s(tree[node_p]):
                if propose(tree, node_p, pn):
                    return tree, node_p

    ### IF X IS HIGHEST S, TRAVERSE PREVIOUS SENTENCES L->R, BF, PROPOSE ANY NP, SEE ELSE CASE ###

    if cur != ():

        ### IF X NOT HIGHEST S, GO UP TO FIRST NP OR S, CALL THIS Y ###

        cur, path = climb_to_node(tree, cur)

        ### IF Y IS NP & PATH P DIDN'T PASS THRU NOMINAL NODE Y IMMEDIATELY DOMINATES, PROPOSE Y ###

        if is_np(tree[cur]) and not is_nominal(tree[cur]):
            for cp in [cur + (i,) for i in range(len(tree[cur]))]:
                if isinstance(tree[cp], Tree) and is_nominal(tree[cp]):
                    if cp not in path:
                        if propose(tree, cur, pn):
                            return tree, cur

        ### BFS ALL BRANCHES BELOW Y TO THE LEFT OF PATH P, PROPOSE ANY NP ###

        nodes = bfs(tree, cur, 0)
        while not nodes.empty():
            node_p = nodes.get()
            
            if is_left_of_path(node_p, path):
                if is_np(tree[node_p]) and propose(tree, node_p, pn):
                    return tree, node_p

        ### IF Y IS S, TRAVERSE RIGHT DOWN TO ANY NP OR S, PROPOSE ANY NP ###

        if not is_np(tree[cur]):
            while not nodes.empty():
                n = nodes.get()
                if is_np(tree[n]) and propose(tree, n, pn):
                    return tree, n
                elif is_np_or_s(tree[n]):
                    break

    ### TRAVERSE PREVIOUS SENTENCES L->R, BF, PROPOSE ANY NP ###

    for t in reversed(trees[:-1]):
        nq = bfs(t) # get L->R ordered BFS list of nodes

        while not nq.empty():
            node_p = nq.get()

            if is_np(t[node_p]) and propose(t, node_p, pn):
                return t, node_p
                
        return None, None

    return None, None

def pretty_print(tts, tp, t, p):
    ''' 
    Takes a list of test sentences, pronoun position, antecedent tree, and antecedent position
    and prints the sentences with pronoun and antecedent highlighted by angled brackets.
    '''
    for i, tt in enumerate(tts):
        if tt == t:
            # add '[' to front of first word in antecedent
            f = tt[p].leaf_treeposition(0)
            tt[p][f] = f'[{tt[p][f]}'

            # add ']' to end of last word in antecedent
            l = tt[p].leaf_treeposition(len(tt[p].leaves())-1)
            tt[p][l] = f'{tt[p][l]}]'
        if i == len(tts)-1:
            # add brackets around pronoun
            x = tt[tp].leaf_treeposition(0)
            tt[tp] = f'<{tt[tp][x]}>'

    s = ' '.join([' '.join(tt.leaves()) for tt in tts] + [''])
    if t:
        print(f'[+] {s}')
    else:
        print(f'[?] {s}')

def main(tests):
    ''' Takes a list of tests and runs Hobbs' algorithm on them '''
    for (tts,tp) in tests:
        t, p = hobbs(tts, tp)
        pretty_print(tts, tp, t, p)

if __name__ == '__main__':
    load_names('new_names.json')

    data_path = sys.argv[1]

    with open(data_path, 'r') as f:
        raw = f.readlines()

    raw_q = queue.Queue()
    for rt in raw:
        raw_q.put(rt)

    data = []

    while not raw_q.empty():
        sentences = []
        while not raw_q.empty():
            s = raw_q.get()
            if s == '' or s == '\n':
                break
            else:
                sentences.append(s)

        trees: 'list[Tree]' = [Tree.fromstring(x) for x in sentences]
        
        for t in trees:
            for i, l in enumerate(t.leaves()):
                if l[0] == '<' and l[-1] == '>':
                    lp = t.leaf_treeposition(i)
                    t[lp] = t[lp][1:-1]
                    data.append((trees, lp[:-1]))
                    break
         
    main(data)