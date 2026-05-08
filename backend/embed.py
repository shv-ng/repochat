import hashlib

import chromadb
from pydantic import BaseModel


class QueryResult(BaseModel):
    id: str
    content: str
    metadata: dict
    distance: float


class Embed:
    def __init__(self, collection_name):
        self.collection_name = self._correct_collection_name(collection_name)
        self.client = chromadb.PersistentClient()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )

    def embed(self, text, metadata=None) -> str:
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        exiting = self.collection.get(ids=[content_hash])
        if exiting["ids"]:
            return content_hash

        self.collection.add(
            documents=[text],
            ids=[content_hash],
            metadatas=[metadata],
        )
        return content_hash

    def semantic_search(self, query_text: str, n_results=5) -> list[QueryResult]:
        results = self.collection.query(
            query_texts=query_text,
            n_results=n_results,
        )
        if not results["ids"]:
            return []

        return [
            QueryResult(
                id=id_,
                content=str(doc),
                metadata=meta,
                distance=dist,
            )
            for id_, doc, meta, dist in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def keyword_search(self, query_text: str, n_results=5) -> list[QueryResult]:
        results = self.collection.query(
            query_texts=query_text,
            where_document={"$contains": query_text},
            n_results=n_results,
        )
        if not results["ids"]:
            return []
        return [
            QueryResult(
                id=id_,
                content=str(doc),
                metadata=meta,
                distance=dist,
            )
            for id_, doc, meta, dist in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def query(self, query_texts: str, n_results=5) -> list[QueryResult]:
        keyword_results = self.keyword_search(query_texts, n_results)
        semantic_results = self.semantic_search(query_texts, n_results)

        results = keyword_results

        ids = set(keyword_results[0].id for keyword_results in keyword_results)
        for semantic_result in semantic_results:
            if semantic_result.id not in ids:
                results.append(semantic_result)

        return results

    @staticmethod
    def _correct_collection_name(url):
        return (
            url.replace("https://github.com/", "").replace(".git", "").replace("/", "_")
        )


if __name__ == "__main__":
    embed = Embed("my_collection")

    embed.embed("This is a document about pineapple")
    embed.embed("This is a document about oranges")
    embed.embed("This is a document about apples")
    embed.embed("This is a document about iphone")

    results = embed.query(query_texts=["This is a query document about laptop"])
    print(results)
