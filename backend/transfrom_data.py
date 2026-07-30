from load_data import Article
from dateutil import parser
import pandas as pd
import random
import uuid
import torch
import numpy as np


def create_node(article: Article):
    node = {
        "key": article.article_index,
        "attributes": {
            # "x": random.choice(range(20)),
            # "y": random.choice(range(20)),
            "x": random.random(),
            "y": random.random(),
            "type": "square",
            "tooltip_label": f"{article.published_time} - {article.title}",
            "title": article.title,
            "published_time": article.published_time,
            "url": article.url,
            "text": article.text,
            "domain": article.domain,
            "timestamp": parser.parse(article.published_time).timestamp(),
            "important_words": article.important_words,
            "story_id": article.story_id,
        },
    }
    return node


def create_edge(art1: Article, art2: Article, weight=0):
    edge = {
        "key": str(uuid.uuid4()),
        "source": art1.article_index,
        "target": art2.article_index,
        "attributes": {"label": weight, "type": "arrow", "size": 2, "weight": weight},
    }
    return edge


def transform(
    articles: list[Article], similarity_matrix: pd.DataFrame, params: dict = dict()
):
    domains = set()
    data = dict()
    data["nodes"] = []
    data["edges"] = []
    for a in articles:
        art = create_node(a)
        data["nodes"].append(art)
        domains.add(art["attributes"]["domain"])

    import torch

    # Convert similarity_matrix to GPU tensor
    sim = torch.as_tensor(similarity_matrix, device="cuda")
    threshold = params.get("threshold", 0)
    n = sim.shape[0]

    # Lower-triangle indices (i > j)
    i_idx, j_idx = torch.tril_indices(n, n, offset=-1, device="cuda")

    frequency_data = {i/10: 0 for i in range(10)}
    # print(i_idx, j_idx)

    # Mask: only pairs above threshold
    valid_mask = sim[i_idx, j_idx] >= threshold
    i_valid = i_idx[valid_mask].cpu().numpy()
    j_valid = j_idx[valid_mask].cpu().numpy()

    # Pre-parse publication times once
    pub_times = np.array([parser.parse(str(a.published_time)) for a in articles])

    # Vectorized comparison to decide edge order
    art1_times = pub_times[i_valid]
    art2_times = pub_times[j_valid]

    # Determine which article comes first
    swap_mask = art1_times >= art2_times

    # Apply swapping
    final_i = np.where(swap_mask, j_valid, i_valid)
    final_j = np.where(swap_mask, i_valid, j_valid)

    # Batch edge creation
    edges = [
        create_edge(articles[i], articles[j], float(sim[i, j]))
        for i, j in zip(final_i, final_j)
    ]
    # print(f"{len(edges)} edges to be created!")
    # edges = [create_edge(articles[i], articles[j]) for i, j in zip(final_i, final_j)]
    data["edges"].extend(edges)

    return data

    import torch

    # Convert similarity_matrix to GPU tensor
    sim = torch.as_tensor(similarity_matrix, device="cuda")
    threshold = params.get("threshold", 0)

    n = sim.shape[0]

    # Get lower-triangle indices (i > j)
    i_idx, j_idx = torch.tril_indices(n, n, offset=-1, device="cuda")

    # Mask: only pairs above threshold
    valid_mask = sim[i_idx, j_idx] >= threshold

    # Indices that pass threshold
    i_valid = i_idx[valid_mask].cpu().numpy()
    j_valid = j_idx[valid_mask].cpu().numpy()

    # Optional: pre-parse publication times to save repeated parsing
    pub_times = [parser.parse(str(a.published_time)) for a in articles]

    # Build edges
    for i, j in zip(i_valid, j_valid):
        art1 = articles[i]
        art2 = articles[j]

        art1_pub = pub_times[i]
        art2_pub = pub_times[j]

        if art1_pub < art2_pub:
            data["edges"].append(create_edge(art1, art2))
        else:
            data["edges"].append(create_edge(art2, art1))

    return data
    for i, a1 in enumerate(similarity_matrix):
        for j, a2 in enumerate(a1):
            if i <= j:
                continue
            if a2 >= params.get("threshold", 0):
                art1 = articles[i]
                art2 = articles[j]
                art1_pub = parser.parse(str(art1.published_time))
                art2_pub = parser.parse(str(art2.published_time))

                if art1_pub < art2_pub:
                    data["edges"].append(create_edge(art1, art2))
                else:
                    data["edges"].append(create_edge(art2, art1))

    return data
