import hashlib

import chromadb
from pydantic import BaseModel


class QueryResult(BaseModel):
    id: str
    content: str
    metadata: dict
    distance: float


class Embed:
    """Embed class for embedding and searching text

    Args:
        collection_name (str): name of collection
    """

    def __init__(self, collection_name):
        self.collection_name = self._correct_collection_name(collection_name)
        self.client = chromadb.PersistentClient()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )

    def embed(self, text, metadata={}) -> str:
        """Embed text and metadata into collection

        Args:
            text (str): text to embed
            metadata (dict, optional): metadata to embed. Defaults to {}.

        Returns:
            str: content hash
        """

        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        exiting = self.collection.get(ids=[content_hash])
        if exiting["ids"]:
            return content_hash

        file_path = metadata.get("file_path", "")
        if file_path.lower().endswith("readme.md"):
            metadata["type"] = "readme"

        self.collection.add(
            documents=[text],
            ids=[content_hash],
            metadatas=[metadata],
        )
        return content_hash

    def semantic_search(self, query_text: str, n_results=5) -> list[QueryResult]:
        """Search semantically

        Args:
            query_text (str): query text
            n_results (int, optional): number of results. Defaults to 5.

        Returns:
            list[QueryResult]: list of query results
        """

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
        """Search for query text using keyword search

        Args:
            query_text (str): query text
            n_results (int, optional): number of results. Defaults to 5.

        Returns:
            list[QueryResult]: list of query results
        """
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
        """Search for query text using keyword and semantic search

        Args:
            query_texts (str): query text
            n_results (int, optional): number of results. Defaults to 5.

        Returns:
            list[QueryResult]: list of query results
        """
        keyword_results = self.keyword_search(query_texts, n_results)
        semantic_results = self.semantic_search(query_texts, n_results)
        readme = self._get_readme()

        results = [readme] if readme else []
        results.extend(keyword_results)

        ids = set(keyword_results.id for keyword_results in keyword_results)
        for semantic_result in semantic_results:
            if semantic_result.id not in ids:
                results.append(semantic_result)

        return results

    def _get_readme(self) -> QueryResult:
        """Get readme

        Returns:
            str: readme
        """
        res = self.collection.get(
            where={"type": "readme"},
            include=["documents", "metadatas"],
            limit=1,
        )

        if not res["ids"]:
            return None

        return QueryResult(
            id=res["ids"][0],
            content=res["documents"][0],
            metadata=res["metadatas"][0],
            distance=0,
        )

    @staticmethod
    def _correct_collection_name(url):
        """Correct collection name

        Args:
            url (str): url to repo

        Returns:
            str: corrected collection name
        """
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
