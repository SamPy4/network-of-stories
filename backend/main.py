from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from embeddings import tfidf, alibaba, random_model
from clusterings import cosine
import load_data
import transfrom_data
import pandas as pd

app = FastAPI()

# Allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


alibaba_embedder = ()  # alibaba.Embedder("embeddings/embedding_model")
embs = {"tf-idf": tfidf, "alibaba": alibaba_embedder, "random": random_model}
clusts = {"cosine": cosine}


@app.get("/graph")
def get_graph(
    dataset: str = "",
    embedding: str = "tf-idf",
    similarity: str = "cosine",
    threshold: float = 0.7,
):

    data = load_data.load(dataset)
    print("Data loaded from", dataset, "with length", len(data))

    if embedding == "alibaba":
        if not all([d.embedding for d in data]):
            print(data[0].title)
            print(data[0].embedding)
            print(data[0].article_index)
            print("Alibaba requires all articles to have an embedding!")
            print([d.embedding for d in data])
            print(
                f"Embedding not found in {[d.embedding for d in data].count(None)}/{len(data)}"
            )
            return {}

        print("EMBEDDING AS IS")
        print(type(data[0].embedding))
        embeddings = pd.DataFrame([d.embedding for d in data])
        print(embeddings)
        c = clusts[similarity].cluster(embeddings)
        return transfrom_data.transform(data, c, {"threshold": threshold})

    elif embedding == "random":
        c = embs[embedding].embed(data)
        return transfrom_data.transform(data, c, {"threshold": threshold})

    e = embs[embedding].embed(data)
    print("Data embedded")
    c = clusts[similarity].cluster(e)
    print("Data clustered")
    return transfrom_data.transform(data, c, {"threshold": threshold})


if __name__ == "__main__":
    j_data = get_graph(
        "ten_articles", "tf-idf", {"type": "cosine", "params": {"threshold": 0.1}}
    )
    print(j_data)
