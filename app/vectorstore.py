import os
import math

os.environ['TRANSFORMERS_VERBOSITY'] = 'error'

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import warnings
warnings.filterwarnings('ignore')
from sentence_transformers import CrossEncoder


CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-small"
RERANKER_MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )


def create_or_load_vectorstore(documents=None):
    """
    Se documents for fornecido, cria o vectorstore e persiste em disco.
    Caso contrário, carrega o banco existente para buscas.
    """
    print(f"Carregando o modelo de Embedding {EMBEDDING_MODEL_NAME}...")
    embeddings = get_embeddings()

    if documents:
        print(f"Processando Embeddings para {len(documents)} chunks e salvando em {CHROMA_PERSIST_DIR}...")
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIR
        )
        return vectorstore
    else:
        return Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings
        )


def buscar_com_rerank(vectorstore, query: str, k: int = 10, top_n: int = 6):
    """
    Busca os top k documentos via similaridade vetorial e reordena com um
    CrossEncoder para retornar os top_n mais relevantes.
    """
    print(f"Buscando top {k} pelo Chroma e avaliando com Reranker {RERANKER_MODEL_NAME}...")
    reranker_model = CrossEncoder(RERANKER_MODEL_NAME)

    docs = vectorstore.similarity_search(query, k=k)
    pairs = [[query, doc.page_content] for doc in docs]

    raw_scores = reranker_model.predict(pairs)

    # Converte logits brutos para probabilidades via sigmoid
    docs_com_scores = [
        (doc, 1 / (1 + math.exp(-s)))
        for doc, s in zip(docs, raw_scores)
    ]

    docs_com_scores.sort(key=lambda x: x[1], reverse=True)
    return docs_com_scores[:top_n]
