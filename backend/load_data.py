import json
import os


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
        self.embedding: list = None
        self.important_words: list = []
        self.story_id = None


def load(path: str, article_name_template: str = "article_{i}.json") -> list[Article]:
    start_index = 0
    try:
        open(f"./mock_data/{path}/{article_name_template.format(i=0)}")
    except FileNotFoundError:
        start_index = 1
    try:
        article_path_names = [
            f"./mock_data/{path}/{article_name_template.format(i=i + start_index)}"
            for i in range(len(os.listdir(f"./mock_data/{path}/")))
        ]
    except IndexError:
        print("\nThere must be an index '{i}' in the template!\n")
        raise

    # article_path_names = article_path_names[:30]

    articles = []
    article_i = 1  # The same number as in the name
    for article_path in article_path_names:
        with open(article_path, "r") as f:
            data = json.loads(f.read())
            a = Article()
            a.article_index = f"{article_i}"
            load_success = False
            try:
                a.domain = data["thread"]["site_full"]
                a.title = data["title"]
                a.text = data["text"]
                a.published_time = data["published"]
                a.categories = data["categories"]
                a.url = data["url"]
                a.language = data["language"]
                if "embedding" in data:
                    if "story" in data:
                        a.story_id = data["story"]
                    if len(json.loads(data["embedding"])) < 3:
                        a.embedding = json.loads(data["embedding"])[0]
                    else:
                        a.embedding = json.loads(data["embedding"])
                load_success = True
            except:
                # print("Load type 1 did not succeed!")
                pass
            if not load_success:
                try:
                    a.title = data["title"]
                    a.url = data["link"]
                    d = data["link"].split("/")
                    if len(d) > 0:
                        if "http" in d[0]:
                            a.domain = d[2]
                        else:
                            a.domain = d[0]
                    a.text = data["content"]
                    a.published_time = data["published_time"]
                    if "story" in data:
                        a.story_id = data["story"]
                    if "embedding" in data:
                        if len(json.loads(data["embedding"])) < 3:
                            a.embedding = json.loads(data["embedding"])[0]
                        else:
                            a.embedding = json.loads(data["embedding"])
                    load_success = True
                except:
                    print("Load types 1 and 2 failed!")
                    raise
            # Add only ~non-empty english articles
            if load_success and len(a.text) > 5:
                if not a.language or a.language == "english":
                    # print(f"{a.url = }")
                    articles.append(a)

        article_i += 1

    return articles


if __name__ == "__main__":
    load_from_db()
