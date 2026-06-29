from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
import pickle
import os
from pathlib import Path

_TOOLS_DIR = os.path.dirname(__file__)


class RAGRetriever:

    def __init__(self):

        current_dir = Path(__file__).resolve().parent

        index_path = current_dir / "knowledge.index"
        chunk_path = current_dir / "chunks.pkl"

        self.model = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2"
        )

        # faiss C++ fopen 无法处理含中文的路径，chdir 后用纯 ASCII 文件名规避
        _prev_cwd = os.getcwd()
        os.chdir(str(current_dir))
        try:
            self.index = faiss.read_index("knowledge.index")
        finally:
            os.chdir(_prev_cwd)

        with open(
            chunk_path,
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