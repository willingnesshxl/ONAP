from itertools import combinations
import math

__all__ = [
    "get_structural_holes_HIS"
]


def get_structural_holes_HIS(G, C: [frozenset], epsilon, weight='weight'):
    """
    Returns S, I, H in paper https://www.aminer.cn/structural-hole
    """
    # S: list[subset_index]
    S = []
    for community_subset_size in range(2, len(C) + 1):
        S.extend(list(combinations(range(len(C)), community_subset_size)))
    # I: dict[node][cmnt_index]
    # H: dict[node][subset_index]
    I, H = initialize(G, C, S, weight=weight)

    alphas = [0.3 for i in range(len(C))]  # list[cmnt_index]
    betas = [(0.5 - math.pow(0.5, len(subset)))
             for subset in S]  # list[subset_index]

    while True:
        P = update_P(G, C, alphas, betas, S, I, H)  # dict[node][cmnt_index]
        I_new, H_new = update_I_H(G, C, S, P, I)
        if is_convergence(G, C, I, I_new, epsilon):
            break
        else:
            I, H = I_new, H_new
    return S, I, H


def initialize(G, C: [frozenset], S: [tuple], weight='weight'):
    I, H = dict(), dict()
    for node in G.nodes:
        I[node] = dict()
        H[node] = dict()

    for node in G.nodes:
        for index, community in enumerate(C):
            if node in community:
                # TODO: add PageRank or HITS to initialize I
                I[node][index] = G.degree(weight=weight)[node]
            else:
                I[node][index] = 0

    for node in G.nodes:
        for index, subset in enumerate(S):
            H[node][index] = min([I[node][i] for i in subset])

    return I, H


def update_P(G, C, alphas, betas, S, I, H):
    P = dict()
    for node in G.nodes:
        P[node] = dict()

    for node in G.nodes:
        for cmnt_index in range(len(C)):
            subsets_including_current_cmnt = []
            for subset_index in range(len(S)):
                if cmnt_index in S[subset_index]:
                    subsets_including_current_cmnt.append(
                        alphas[cmnt_index] * I[node][cmnt_index] +
                        betas[subset_index] * H[node][subset_index]
                    )
            P[node][cmnt_index] = max(subsets_including_current_cmnt)
    return P


def update_I_H(G, C, S, P, I):
    I_new, H_new = dict(), dict()
    for node in G.nodes:
        I_new[node] = dict()
        H_new[node] = dict()

    for node in G.nodes:
        for cmnt_index in range(len(C)):
            P_max = max([
                P[neighbour][cmnt_index]
                for neighbour in G.adj[node]
            ])
            I_new[node][cmnt_index] = P_max if (
                P_max > I[node][cmnt_index]) else I[node][cmnt_index]
        for subset_index, subset in enumerate(S):
            H_new[node][subset_index] = min([I_new[node][i] for i in subset])
    return I_new, H_new


def is_convergence(G, C, I, I_new, epsilon):
    deltas = []
    for node in G.nodes:
        for cmnt_index in range(len(C)):
            deltas.append(
                abs(I[node][cmnt_index] - I_new[node][cmnt_index]))
    return max(deltas) < epsilon


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
    S, I, H = get_structural_holes_HIS(g, cmnts, epsilon=0.01)

    for node in H:
        print("{}: {}".format(node, H[node][len(S)-1]))
