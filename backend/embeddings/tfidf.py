from sklearn import feature_extraction
import numpy as np
from load_data import Article


def top_tfidf_words_per_doc(X, feature_names, k=10):
    results = []

    for doc_idx in range(X.shape[0]):
        row = X[doc_idx]

        # get non-zero tf-idf scores
        scores = row.toarray().flatten()

        # indices of top k scores
        top_indices = np.argsort(scores)[-k:][::-1]

        top_words = [
            (feature_names[i], scores[i]) for i in top_indices if scores[i] > 0
        ]

        results.append(top_words)

    return results


def embed(articles: list[Article]):
    corpus = [art.text for art in articles]
    print(f"{len(corpus) = }")

    vectorizer = feature_extraction.text.TfidfVectorizer(
        stop_words="english",
        # max_features=50  # optional: limit vocabulary size
    )

    X = vectorizer.fit_transform(corpus)

    feat_names = vectorizer.get_feature_names_out()
    top_words = top_tfidf_words_per_doc(X, feat_names)
    [a.important_words.extend(t) for a, t in zip(articles, top_words)]

    return X


if __name__ == "__main__":
    texts = [
        "Huonekaluliikeet, Askon ja Sotkan, omistava Indoor Group on hakeutunut konkurssiin. Ylen tietojen mukaan tehtaan työntekijät on passitettu kotiin, ja ainakin osa myymälöistä on suljettu.",
        "Syynä ovat yhtiön pitkään jatkuneet talousvaikeudet ja epäonnistuneet rahoitusneuvottelut.",
        "Kuluttajan asema konkurssitilanteessa riippuu pitkälti siitä, millä tavalla ostos on maksettu.",
        "Jos maksu on tehty luottokortilla ja tuote on jäänyt toimittamatta, kuluttajan on oltava suoraan yhteydessä luottokorttiyhtiöön ja pyydettävä sieltä rahojen palautusta.",
        "Konkurssihakemuksen Indoor Groupista Helsingin käräjäoikeuteen on jättänyt kauhavalainen huonekaluvalmistaja Unico Finland Oy.",
        "Indoor Group kertoo tiedotteessaan, että se pyrkii aktiivisesti sopuratkaisuun tilanteessa. Yhtiön operatiivinen toiminta jatkuu asiakkaiden ja yhteistyökumppaneiden suuntaan normaalisti.",
        "Huonekalualan markkinatilanne on ollut viime vuosina tunnetusti erittäin haastava. Vastatakseen tähän markkinapaineeseen Indoor on tehnyt määrätietoisesti töitä kulurakenteensa keventämiseksi, yhtiö kertoo.",
    ]

    ass = [Article(t) for t in texts]

    e = embed(ass)

    [print(a.important_words) for a in ass]
