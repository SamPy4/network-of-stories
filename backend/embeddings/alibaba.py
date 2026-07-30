import torch
from transformers import AutoModel, AutoTokenizer
from sklearn.metrics.pairwise import cosine_similarity


torch.manual_seed(42)
torch.cuda.manual_seed(42)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False


class Article:
    def __init__(self, text: str = ""):
        self.article_index = ""
        self.title = ""
        self.text = text
        self.published_time = None
        # self.topics = []
        self.categories = []
        self.domain = ""
        self.url = ""
        self.language = ""


class Embedder:
    def __init__(self, model_path: str, device: str = "cuda") -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, trust_remote_code=True, use_fast=True
        )
        self.embedding_model = AutoModel.from_pretrained(
            model_path, trust_remote_code=True
        ).to(device)

    def embed(self, texts: list[Article]) -> list[list[float]]:
        if len(texts) == 0:
            return []

        tokens = self.tokenizer(
            [art.text for art in texts],
            truncation=False,
            padding=True,
            return_tensors="pt",
        ).to(
            self.device,
        )

        embeddings: torch.Tensor = torch.nn.functional.normalize(
            self.embedding_model(**tokens).last_hidden_state[:, 0, :],
            p=2,
            dim=1,
        )
        return [e.cpu().flatten().tolist() for e in embeddings]


if __name__ == "__main__":
    embedder = Embedder("./embedding_model")

    input_texts = [
        Article("what is the capital of China?"),
        Article("how to implement quick sort in python?"),
        Article("Beijing"),
        Article("sorting algorithms"),
    ]

    embeddings = embedder.embed(input_texts)

    similarity_matrix = cosine_similarity(embeddings)

    print(similarity_matrix)
