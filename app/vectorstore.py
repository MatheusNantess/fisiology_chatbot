import os
import math
os.environ['TRANSFORMERS_VERBOSITY'] = 'error' # Oculta aquele Warning chato do UNEXPECTED

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import warnings
warnings.filterwarnings('ignore')
from sentence_transformers import CrossEncoder


# Nome do diretório onde o banco será salvo fisicamente (projeto/data/chroma_db)
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")

# Escolhi a versão 'small' baseando-me na sua limitação de hardware/tempo.
# Ela tem apenas algumas centenas de MBs e gera os vetores na CPU muito rápido.
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-small"

# Modelo de Reranker (Cross-Encoder) rápido e super especializado em dar 'match'
RERANKER_MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

def get_embeddings():
    """Inicializa os embeddings locally via HuggingFace"""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        # Se você tivesse usando GPU, trocaríamos 'cpu' por 'cuda'
        model_kwargs={'device': 'cpu'},
        # O modelo 'e5' requer normalização para medir acurácia por Cosine Similarity devidamente
        encode_kwargs={'normalize_embeddings': True} 
    )

def create_or_load_vectorstore(documents=None):
    """
    Se documents for fornecido, calcula os embeddings deles e salva no ChromaDB em disco.
    Se não for fornecido, apenas carrega o banco do disco para fazer procuras.
    """
    print(f"Carregando o modelo de Embedding {EMBEDDING_MODEL_NAME} (Isso pode baixar os arquivos na 1ª vez)...")
    embeddings = get_embeddings()

    if documents:
        # Cria e persiste o chroma com os documentos em massa
        print(f"Processando Embeddings para {len(documents)} chunks e salvando em {CHROMA_PERSIST_DIR}...")
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIR
        )
        return vectorstore
    else:
        # Apenas carrega da memória persistida (útil pro seu webserver depois)
        return Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings
        )

def buscar_com_rerank(vectorstore, query: str, k: int = 10, top_n: int = 6):
    """
    Busca os top 'k' documentos usando vetores e então aplica o ReRank manual
    com um CrossEncoder para devolver os 'top_n'.
    """
    print(f"Buscando top {k} pelo Chroma e avaliando com Reranker {RERANKER_MODEL_NAME}...")
    reranker_model = CrossEncoder(RERANKER_MODEL_NAME)
    
    docs = vectorstore.similarity_search(query, k=k)
    pairs = [[query, doc.page_content] for doc in docs]
    
    # O modelo solta as notas cruas (Logits), que variam de negativos a positivos.
    raw_scores = reranker_model.predict(pairs)
    
    # Vamos converter os Logits para uma Probabilidade (0 a 1) usando a função matemática Sigmoid
    docs_com_scores = []
    for doc, s in zip(docs, raw_scores):
        probabilidade = 1 / (1 + math.exp(-s))
        docs_com_scores.append((doc, probabilidade))
    
    # Junta os documentos com sua % e ordena do maior para o menor
    docs_com_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Retorna só o podium
    return docs_com_scores[:top_n]
