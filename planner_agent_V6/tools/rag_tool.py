from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import pickle

from config import (
    RAG_INDEX_PATH,
    RAG_CHUNK_PATH
)


class RAGRetriever:

    def __init__(self):

        self.model = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2"
        )

        self.index = faiss.read_index(
            str(Path(RAG_INDEX_PATH))
        )

        with open(
            Path(RAG_CHUNK_PATH),
            "rb"
        ) as f:

            self.chunks = pickle.load(f)

    def search(
            self,
            query,
            top_k=3
    ):

        query_vec = self.model.encode(
            [query]
        )

        query_vec = np.array(
            query_vec,
            dtype=np.float32
        )

        distances, indices = self.index.search(
            query_vec,
            top_k
        )

        results = []

        for idx in indices[0]:

            chunk = self.chunks[idx].strip()

            if chunk:

                results.append(chunk)

        return results

retriever = RAGRetriever()


def rag_tool(query):

    docs = retriever.search(
        query=query,
        top_k=3
    )

    return "\n".join(docs)