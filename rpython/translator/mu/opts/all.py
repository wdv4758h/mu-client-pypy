from rpython.translator.mu.opts import boolflag


def mu_backend_opts(graphs):
    boolflag.optimise(graphs)
