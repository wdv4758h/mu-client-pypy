from rpython.translator.backendopt.removenoops import remove_unaryops


def mu_backend_optimisations(tlc):
    graphs = tlc.graphs

    # remove 'hint' operation
    for g in graphs:
        remove_unaryops(g, ['hint'])
