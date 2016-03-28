import numpy as np


def partial(f, n, i, dx=0.001):
    I = np.identity(n)

    def part(x):
        return (f(x+I[i]*dx) - f(x)) / dx
    return part


def gradient(f, n, dx=0.01):
    def g(x):
        return np.array([G[i](x) for i in np.arange(n)], dtype=float)
    G = [partial(f, n, i, dx=dx) for i in np.arange(n)]
    return g


def gradient_descent(f, n, h0=0.03, dx=1./10**2):
    fx = gradient(f, n, dx=dx)
    pp = np.random.random_sample(n)
    g = fx(pp)
    p = pp - h0*g
    h = h0
    while (p-pp).dot(p-pp) > 1./10**12:
        ph = h; h = 2 * ph
        while f(p-h*g) < f(p-ph*g):
            ph = h; h *= 2
        h /= 2
        pp = p
        g = fx(p)
        p -= h * g
        h = h0
    return p