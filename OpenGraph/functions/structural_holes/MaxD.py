
__all__ = [
    "get_structural_holes_MaxD"
]

def get_community_kernel(G, C: [frozenset]):
    '''
    To get community kernels with most degrees.
    Parameters
    ----------
    G : graph
        An undirected graph.
    C : int
        #communities

    Returns
    -------
    kernels
    '''
    area = []
    for i in range(len(G)):
        area.append(0)
    for i, cc in enumerate(C):
        for each_node in cc:
            area[each_node-1] += 1 << i    # node_id from 1 to n.
    # print(area)
    kernels = []
    cnt = 0
    for i in range(len(C)):
        mask = 1<<i
        cnt+=1
        # print(cnt, ":", mask)
        q = []
        p = []
        for i in range(len(G)):
            if (area[i] & mask) == mask:
                q.append((G.degree[i+1], i+1))
        q.sort()
        q.reverse()
        # print(q)
        for i in range(max(int(len(q)/100),
                           min(2, len(q)))): # latter of min for test.
            p.append(q[i][1])
        # if len(p) > 0:
        #     kernels.append(p)
        kernels.append(p)
    # print(kernels)
    if len(kernels) < 2:
        print("ERROR: WE should have at least 2 communities.")
    for i in range(len(kernels)):
        if len(kernels[i]) == 0:
            print("Comunity %d is too small." % i)
            return None
    # print(kernels)
    return kernels

def get_structural_holes_MaxD (G, k_size, C: [frozenset]):
    '''
    To calc the strucutral hole spanners using MaxD.

    Parameters
    ----------
    G : graph
        An undirected graph.
    k_size : int
        top-k SHS
    C : int
        #communities

    Returns
    -------
    A list of top-k spanners.
    '''
    # for i, cc in enumerate(C):
    #     for aq in cc:
    #         print(i, ":", aq)
    #     print()
    # print(len(C))

    kernels = get_community_kernel(G, C)
    # print(kernels)
    c = len(kernels)
    # print(c)
    save = []
    for i in range(len(G)):
        save.append(False)

    build_network(kernels, c, G)

    n = len(G)
    sflow = []
    save = []
    for i in range(n):
        save.append(True)
    q = []
    ans_list = []
    for step in range(k_size):
        q.clear()
        sflow.clear()
        for i in range(n):
            sflow.append(0)
        max_flow(n, kernels, save)
        for i in range(n*(c-1)):
            k = head[i]
            while k >= 0:
                if flow[k] > 0:
                    sflow[i % n] += flow[k]
                k = nex[k]
        for i in range(n):
            if save[i] == False:
                q.append((-1, i))
            else:
                q.append((sflow[i]+G.degree[i+1], i))
        q.sort()
        q.reverse()
        # print(q)
        candidates = []
        for i in range(n):
            if save[q[i][1]] == True and len(candidates) < k_size:
                candidates.append(q[i][1])
        ret = pick_candidates(n, candidates, kernels, save)
        #print(ret[1]+1)
        ans_list.append(ret[1]+1)
    # global head
    # head.append(233)
    del sflow
    del q
    return ans_list

def pick_candidates(n, candidates, kernels, save):
    '''
    detect candidates.
    Parameters
    ----------
    n : #nodes
    candidates : A list of candidates.
    kernels : A list of kernels
    save : A bool list of visited candidates for max_flow.

    Returns
    -------
    A tuple of min_cut, best_candidate of this round.
    '''
    for i in range(len(candidates)):
        save[candidates[i]] = False
    old_flow = max_flow(n, kernels, save)
    global prev_flow
    prev_flow.clear()
    for i in range(nedge):
        prev_flow.append(flow[i])
    mcut = 100000000
    best_key = -1
    for i in range(len(candidates)):
        key = candidates[i]
        for j in range(len(candidates)):
            save[candidates[j]] = True
        save[key] = False
        tp = max_flow(n, kernels, save, prev_flow)
        if tp < mcut:
            mcut = tp
            best_key = key
    for i in range(len(candidates)):
        save[candidates[i]] = True
        save[best_key] = False
    return (old_flow+mcut, best_key)

head = []

point = []
nex = []
flow = []
capa = []

dist = []
work = []
dsave = []

src = 0
dest = 0
node = 0
nedge = 0
prev_flow = []
oo = 1000000000

def dinic_bfs():
    '''
    using BFS to find augmenting path.

    Returns
    -------
    A bool, whether found a augmenting path or not.
    '''
    global dist, dest, src, node
    dist.clear()
    for i in range(node):
        dist.append(-1)
    dist[src] = 0
    Q = []
    Q.append(src)
    cl = 0
    while cl < len(Q):
        # print(cl, len(Q))
        k = Q[cl]
        i = head[k]
        while i >= 0:
            if flow[i] < capa[i] and dsave[point[i]]==True and dist[point[i]]<0:
                dist[point[i]] = dist[k]+1
                Q.append(point[i])
            i = nex[i]
        cl += 1
    return dist[dest] >= 0

def dinic_dfs(x, exp):
    '''
    using DFS to calc the augmenting path and refresh network.
    Parameters
    ----------
    x : current node.
    exp : current flow.

    Returns
    -------
    current flow.
    '''
    if x == dest:
        return exp
    res = 0
    i = work[x]
    global flow
    while i >= 0:
        v = point[i]
        tmp = 0
        if flow[i] < capa[i] and dist[v]==dist[x]+1:
            tmp = dinic_dfs(v, min(exp, capa[i] - flow[i]))
            if tmp>0:
                flow[i] += tmp
                flow[i^1] -= tmp
                res += tmp
                exp -= tmp
                if exp == 0:
                    break
        i = nex[i]
    return res

def dinic_flow():
    '''
    Dinic algorithm to calc max_flow.

    Returns
    -------
    max_flow.
    '''
    result = 0
    global work
    # print(dinic_bfs())
    while dinic_bfs():
        work.clear()
        for i in range(node):
            work.append(head[i])
        result += dinic_dfs(src, oo)
    # print(result)
    return result

def max_flow(n,kernels, save, prev_flow = None):
    '''
    Calculate max_flow.
    Parameters
    ----------
    n : #nodes
    kernels : A list of kernels.
    save : A bool list of visited nodes.
    prev_flow : A list of previous flows.

    Returns
    -------
    max_flow
    '''
    global dsave, node
    dsave.clear()
    for i in range(node):
        dsave.append(True)

    # print(nedge)

    if prev_flow != None:
        for i in range(nedge):
            flow.append(prev_flow[i])
    else:
        for i in range(nedge):
            flow.append(0)

    c = len(kernels)
    for i in range(n):
        for k in range(c-1):
            dsave[k*n+i] = save[i]
    ret = dinic_flow()
    return ret

def init_MaxD(_node, _src, _dest):
    '''
    Initialize a network.
    Parameters
    ----------
    _node : #nodes
    _src : the source node
    _dest : the destiny node

    Returns
    -------
    void
    '''
    global node, src, dest
    node = _node
    src = _src
    dest = _dest
    global point, capa, flow, nex, head
    head.clear()
    # print(node)
    for i in range(node):
        head.append(-1)
    nedge = 0
    point.clear()
    capa.clear()
    flow.clear()
    nex.clear()

    # print(head)
    # print(node)
    # print(src)
    # print(dest)
    return

def addedge(u, v, c1, c2):
    '''
    Add an edge(u,v) with capacity c1 and inverse capacity c2.
    Parameters
    ----------
    u : node u
    v : node v
    c1 : capacity c1
    c2 : capacity c2

    Returns
    -------
    void
    '''
    # print(u, v)
    global nedge
    global point, capa, flow, nex, head
    point.append(v)
    capa.append(c1)
    flow.append(0)
    nex.append(head[u])
    head[u] = nedge
    nedge += 1
    # print(u, point[nedge-1])
    point.append(u)
    capa.append(c2)
    flow.append(0)
    nex.append(head[v])
    head[v] = nedge
    nedge +=1
    return

def build_network(kernels, c, G):
    '''
    build a network.
    Parameters
    ----------
    kernels : A list of kernels.
    c : #communities.
    G : graph
        An undirected graph.

    Returns
    -------
    void
    '''
    n = len(G)
    init_MaxD(n*(c-1)+2, n*(c-1), n*(c-1)+1)

    # print(kernels)

    base = 0
    for k_iter in range(c):
        S1 = set()
        S2 = set()
        for i in range(c):
            for j in range(len(kernels[i])):
                if i == k_iter:
                    S1.add(kernels[i][j])
                elif i < k_iter:
                    S2.add(kernels[i][j])
        if len(S1) == 0 or len(S2) == 0:
            continue

        for edges in G.edges:
            addedge(base + edges[0] - 1, base + edges[1] - 1, 1, 1)
            addedge(base + edges[1] - 1, base + edges[0] - 1, 1, 1)

        # print(nedge)

        for i in S1:
            if i not in S2:
                # print(i)
                addedge(src, base + i - 1, n, 0)
        for i in S2:
            if i not in S1:
                addedge(base + i - 1, dest, n, 0)
        base += n
    # print(dest)
    return

if __name__ == "__main__":
    import sys
    sys.path.append('../../../')
    import OpenGraph as og

    g = og.classes.Graph()
    edges1 = [(1, 2), (2, 3), (1, 3), (3, 4), (4, 5), (4, 6), (5, 6)]
    edges2 = [(3, 7), (4, 7), (10, 7), (11, 7)]
    edges3 = [(8, 9), (8, 10), (9, 10), (10, 11), (11, 12), (11, 13), (12, 13)]
    g.add_edges(edges1)
    g.add_edges(edges2)
    g.add_edges(edges3)

    cmnts = [frozenset([1, 2, 3]), frozenset([4, 5, 6]), frozenset([3, 4, 7, 10, 11]),
             frozenset([8, 9, 10]), frozenset([11, 12, 13])]
    # for edge in g.edges:
    #     print(edge[0],edge[1])

    k = 5 # top-k spanners

    k_top = get_structural_holes_MaxD(g, k, cmnts)
    print(k_top)