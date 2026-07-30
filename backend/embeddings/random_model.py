import numpy as np
from load_data import Article

def embed(articles: list[Article]):
    # rng = np.random.default_rng(42)
    n = len(articles)  # Matrix size
    # Generate random values for the upper triangle (excluding diagonal)
    A = np.zeros((n, n))
    upper = np.triu_indices(n, k=1)
    A[upper] = 0.1 + 0.9 * np.random.random(len(upper[0]))**100 # Power law
    # A[upper] = np.round(np.random.uniform(0.10, 0.99, size=len(upper[0])), 2)
    # Mirror the upper triangle to the lower triangle
    A += A.T
    # Set diagonal to 1.0
    np.fill_diagonal(A, 1.0)
    
    distances = A

    return distances