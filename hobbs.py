import json
import queue
import sys

from nltk import Tree

NOM_LABELS = ['NN', 'NNS', 'NNP', 'NNPS', 'PRP']
PLURALITY = {
        "NN":          0,
        "NNP":         0,
        "he":          0,
        "she":         0,
        "him":         0,
        "her":         0,
        "it":          0,
        "himself":     0,
        "herself":     0,
        "itself":      0,
        "NNS":         1,
        "NNPS":        1,
        "they":        1,
        "them":        1,
        "themselves":  1,
    }

def is_np_or_s(tree: Tree):
    ''' Checks if a node is represents an NP or S '''
    return tree.label() == 'NP' or tree.label() == 'S'

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
        # visited.append(node)
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
        if isinstance(c, Tree) and c.label() in NOM_LABELS:
            if PLURALITY.get(c.label(), -1) == PLURALITY.get(pn, -2):
                return True
    return False

def _check_gender(tree, pos, pn) -> bool:
    ''' Checks whether a proposed antecedent matches the gender of the pronoun '''
    with open('names.json', 'rb') as f:
        names = json.load(f)

    pns_m = ['he', 'him', 'himself']
    pns_f = ['she', 'her', 'herself']
    # pns_n = ['they', 'them', 'themself', 'themselves' 'it', 'itself']

    for c in tree[pos]:
        if isinstance(c, Tree) and c.label() in NOM_LABELS:
            c_leaf = c.leaves()[0]

            # check male name <-> male pronoun
            if c_leaf.lower() in names['male']:
                if pn in pns_m:
                    return True
                
            # check female name <-> female pronoun
            if c_leaf.lower() in names['female']:
                if pn in pns_f:
                    return True
                
    return False

def hobbs(trees: 'list[Tree]', pos: tuple):
    ''' 
    Runs Hobbs' Algorithm given a list of parse trees and the position.
    Returns the proposed antecedent in the form (tree, position)
    '''

    tree = trees[-1] # start with last tree
    pn = tree[pos].leaves()[0].lower() # pronoun we are trying to resolve

    ### START AT NP OVER PRONOUN ###

    cur = pos[:-1] # go up once from pronoun

    ### CLIMB PARSE TREE UNTIL NP OR S, CALL THIS X ###

    cur, path = climb_to_node(tree, cur) # set cur to node X's position, get path

    ### BFS ALL BRANCHES BELOW X TO LEFT, PROPOSE ANY NP/S ###

    visited = bfs(tree, cur, 0) # in-order list of node positions

    # check each node
    while not visited.empty():
        node_p = visited.get()
        if node_p not in path and node_p != pos:
            if is_np_or_s(tree[node_p]):
                if propose(tree, node_p, pn):
                    return tree, node_p

    ### IF X IS HIGHEST S, TRAVERSE PREVIOUS SENTENCES L->R, BF, PROPOSE ANY NP ###

    ### IF X NOT HIGHEST S, GO UP TO FIRST NP OR S, CALL THIS Y ###

    ### IF Y IS NP & PATH P DIDN'T PASS THRU NOMINAL NODE Y IMMEDIATELY DOMINATES, PROPOSE Y ###

    ### BFS ALL BRANCHES BELOW Y TO THE LEFT OF PATH P, PROPOSE ANY NP ###

    ### IF Y IS S, TRAVERSE LEFT DOWN TO ANY NP OR S, PROPOSE ANY NP ###

    ### TRAVERSE PREVIOUS SENTENCES L->R, BF, PROPOSE ANY NP ###

    return None, None

if __name__ == '__main__':
    assert len(sys.argv) == 3, f'expected 2 arguments, received {len(sys.argv)-1}'

    arg1, arg2 = sys.argv[1:3] # to be implemented (input files)

    # test trees
    tree0 = Tree.fromstring('(S (NP (NNP Alex) ) (VP (VBD is) (NP (PRP him))))')
    tree1 = Tree.fromstring('(S (NP (NNP John) ) (VP (VBD said) (SBAR (-NONE- 0) \
        (S (NP (PRP he) ) (VP (VBD likes) (NP (NNS dogs) ) ) ) ) ) )')
    tree2 = Tree.fromstring('(S (NP (NNP John) ) (VP (VBD said) (SBAR (-NONE- 0) \
        (S (NP (NNP Mary) ) (VP (VBD likes) (NP (PRP him) ) ) ) ) ) )')
    tree3 = Tree.fromstring('(S (NP (NNP John)) (VP (VBD saw) (NP (DT a) \
        (JJ flashy) (NN hat)) (PP (IN at) (NP (DT the) (NN store)))))')
    tree4 = Tree.fromstring('(S (NP (PRP He)) (VP (VBD showed) (NP (PRP it)) \
        (PP (IN to) (NP (NNP Terrence)))))')
    tree5 = Tree.fromstring("(S(NP-SBJ (NNP Judge) (NNP Curry))\
        (VP(VP(VBD ordered)(NP-1 (DT the) (NNS refunds))\
        (S(NP-SBJ (-NONE- *-1))(VP (TO to) (VP (VB begin)\
        (NP-TMP (NNP Feb.) (CD 1))))))(CC and)\
        (VP(VBD said)(SBAR(IN that)(S(NP-SBJ (PRP he))(VP(MD would)\
        (RB n't)(VP(VB entertain)(NP(NP (DT any) (NNS appeals))(CC or)\
        (NP(NP(JJ other)(NNS attempts)(S(NP-SBJ (-NONE- *))(VP(TO to)\
        (VP (VB block) (NP (PRP$ his) (NN order))))))(PP (IN by)\
        (NP (NNP Commonwealth) (NNP Edison)))))))))))(. .))")
    tree6 = Tree.fromstring('(S (NP (NNP John) ) (VP (VBD said) (SBAR (-NONE- 0) \
        (S (NP (NNP Mary) ) (VP (VBD likes) (NP (PRP herself) ) ) ) ) ) )')

    t, p = hobbs([tree0], (1,1,0))
    print(t[p])
    # print(hobbs([tree1], (1,1,1,0,0)))