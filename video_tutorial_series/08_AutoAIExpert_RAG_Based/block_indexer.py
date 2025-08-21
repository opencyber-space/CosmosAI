import os
import json
import warnings
import logging
import pandas as pd
import pdfplumber
import torch
from tqdm.auto import tqdm
import weaviate
import networkx as nx
from aios_instance import PreProcessResult, OnDataResult, Block
import numpy as np
import re
import spacy
from spacy.cli import download
import unicodedata
import requests  # Add this import for OpenAI API calls
# Suppress DEBUG logs from weaviate, openai, urllib3, httpcore, httpx, and llama_index
for noisy_logger in [
    "weaviate",
    "openai",
    "urllib3",
    "httpcore",
    "httpx",
    "llama_index",
]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Load spaCy model at module level (loads once)
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    print("spaCy model 'en_core_web_sm' not found. Downloading...")
    download('en_core_web_sm')
    nlp = spacy.load('en_core_web_sm')

def unicode_to_ascii(s):
    """Normalize unicode string to ASCII."""
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

class EmbeddingUtils:
    """
    Generic embedding utility that can use SentenceTransformer or any HuggingFace model.
    """
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = None,
        max_length: int = 512,
    ):
        self.model_name = model_name
        if "sentence-transformers" in model_name:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name, device=(device or "cuda" if torch.cuda.is_available() else "cpu"))
            self.max_length = max_length
        elif "openai" in model_name:
            #model_name should openai/text-embedding-3-large
            OPENAI_API_KEY="YOUR_API_KEY"
            if OPENAI_API_KEY == "YOUR_API_KEY":
                OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
            from llama_index.embeddings.openai import OpenAIEmbedding
            model_version = model_name.split("/")[-1]  # Extract model name from path
            self.model = OpenAIEmbedding(model=model_version, \
                        api_key=OPENAI_API_KEY,
                        dimensions=max_length)
            self.max_length = max_length

    def get_pooled_embeddings(self, texts):
        if "sentence-transformers" in self.model_name:
            return self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        elif "openai" in self.model_name:
            # For OpenAI models, we need to tokenize and get embeddings differently
            if isinstance(texts, str):
                texts = [texts]
            # Use the correct method for OpenAIEmbedding
            if len(texts) == 1:
                outputs = [self.model.get_text_embedding(texts[0])]
            else:
                outputs = self.model.get_text_embedding_batch(texts)
            return outputs

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF using pdfplumber.
    """
    with pdfplumber.open(pdf_path) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages]
    return "\n".join(pages).replace("\r", "")

def extract_text_from_file(file_path: str) -> str:
    """
    Reads text content from a regular text file (md, txt, py, etc.).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # fallback for binary or unknown encoding
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()
def extract_text_from_csv(file_path):
    """
    Extracts text from a CSV file and returns it as a string.
    Each row is joined by a newline.
    """
    df = pd.read_csv(file_path)
    # Convert DataFrame to a string (tabular text)
    text = df.to_string(index=False)
    return text

def extract_text_from_xlsx(file_path):
    """
    Extracts text from all sheets in an XLSX file and returns it as a string.
    Each sheet's content is separated by a header.
    """
    all_text = []
    with pd.ExcelFile(file_path) as excel_file:
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            sheet_text = f"Sheet: {sheet_name}\n" + df.to_string(index=False)
            all_text.append(sheet_text)
    return "\n\n".join(all_text)

def chunk_text_split(text: str, chunk_size: int, overlap: int = 0):
    """
    Split text into chunks with specified overlap between chunks.
    
    Args:
        text: The input text to be chunked
        chunk_size: Number of tokens per chunk
        overlap: Number of tokens to overlap between chunks (default: 0)
    
    Returns:
        Generator of text chunks with desired overlap
    """
    if overlap >= chunk_size and chunk_size > 0:
        logger.warning(f"Overlap ({overlap}) should be less than chunk_size ({chunk_size}). Setting overlap to {chunk_size//2}")
        overlap = chunk_size // 2
        
    toks = text.split()
    if not toks:
        return
        
    # Calculate effective step size (accounting for overlap)
    step = max(1, chunk_size - overlap)
    
    for i in range(0, len(toks), step):
        # Take chunk_size tokens or remaining tokens if less than chunk_size
        chunk = toks[i : min(i + chunk_size, len(toks))]
        if chunk:  # Only yield non-empty chunks
            yield " ".join(chunk)

def get_header_for_lines(text):
    """
    Returns a list mapping each line index to the most recent markdown header (##, ###, ####).
    """
    lines = text.splitlines()
    header_for_line = [None] * len(lines)
    current_header = ""
    header_pattern = re.compile(r'^(#{2,4})\\s+(.*)')
    for i, line in enumerate(lines):
        match = header_pattern.match(line)
        if match:
            current_header = line.strip()
        header_for_line[i] = current_header
    return header_for_line

def chunk_text_with_headers(text: str, chunk_size: int, overlap: int = 0):
    """
    Split text into chunks with specified overlap, prepending the most recent markdown header (##, ###, ####) to each chunk.
    """
    lines = text.splitlines()
    header_for_line = get_header_for_lines(text)
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(lines), step):
        chunk_lines = lines[i:i+chunk_size]
        if not chunk_lines:
            continue
        header = header_for_line[i]
        chunk_text = "\n".join(chunk_lines)
        if header:
            chunk_text = f"{header}\n{chunk_text}"
        chunks.append(chunk_text)
    return chunks

def calculate_cosine_similarity(vec1, vec2):
    import numpy as np
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

def clean_text(text, remove_stopwords=False):
    text = unicode_to_ascii(text)
    text = text.replace('\n', ' ').lower()
    doc = nlp(text)
    tokens = [
        token.lemma_ for token in doc
        if not token.is_punct
        and not token.is_space
        and len(token.text) > 2
        and (not token.is_stop if remove_stopwords else True)
        and not token.text.startswith('@')
        and not token.text.startswith('http')
    ]
    cleaned = ' '.join(tokens)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def get_openai_summary(text, api_key=None, model="gpt-3.5-turbo", max_tokens=256):
    """
    Use OpenAI API to summarize a document.
    """
    response = None
    localModel = model
    doneModels = set()
    doneModels.add(localModel)
    modelsPriority = ["gpt-4","gpt-4.1-nano","gpt-4o-mini","o1-mini","gpt-3.5-turbo"]
    while True:
        try:
            if api_key is None:
                api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY not set in environment or passed explicitly.")
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            prompt = (
                "Summarize the following document in a concise paragraph, capturing all key points and main ideas. "
                "If the document is a table, summarize its purpose and the type of information it contains.\n\n" + text[:6000]  # Truncate to avoid token limits
            )
            data = {
                "model": localModel,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.2
            }
            response = requests.post(url, headers=headers, json=data, timeout=180)
            response.raise_for_status()
            result = response.json()
            break
        except Exception as e:
            print(f"Error occurred: {e}")
            modelSelectionDone = False
            for model_ in modelsPriority:
                if model_ not in doneModels:
                    localModel = model_
                    doneModels.add(localModel)
                    print(f"Retrying with model: {localModel}")
                    modelSelectionDone = True
                    continue
            if not modelSelectionDone:
                return "Error occurred while summarizing."
            #return "Error occurred while summarizing."

    return result["choices"][0]["message"]["content"].strip()

def get_gemini_summary(text, api_key=None, model="models/gemini-1.5-pro-latest", max_tokens=256):
    """
    Use Google Gemini API to summarize a document.
    """
    import requests
    response = None
    if api_key is None:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment or passed explicitly.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent?key={api_key}"
    prompt = (
        "Summarize the following document in a concise paragraph, capturing all key points and main ideas. "
        "If the document is a table, summarize its purpose and the type of information it contains.\n\n" + text[:6000]
    )
    data = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.2
        }
    }
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=180)
        resp.raise_for_status()
        result = resp.json()
        # Gemini returns summary in a nested structure
        summary = result["candidates"][0]["content"]["parts"][0]["text"]
        return summary.strip()
    except Exception as e:
        print(f"Error occurred in Gemini summary: {e}")
        return "Error occurred while summarizing."

class IndexDocumentsBlock:
    """
    Block to extract text from a local repo (PDFs, MD, PY, TXT), chunk into passages,
    embed with SentenceTransformer (or other HuggingFace model), build a graph (Graph RAG),
    and store nodes/edges in Weaviate.
    """
    def __init__(self, context):
        self.context = context
        self.repo_dir = context.block_init_data.get("repo_dir", "./")
        self.passages_json = context.block_init_data.get("passages_json", "data/psgs_w100.jsonl")
        self.chunk_size = int(context.block_init_parameters.get("chunk_size", 100))
        self.chunk_overlap = int(context.block_init_parameters.get("chunk_overlap", 20))  # Default 20% overlap
        self.max_length = int(context.block_init_parameters.get("max_length", 512))
        self.device = context.block_init_data.get("device", "cuda" if torch.cuda.is_available() else "cpu")
        self.similarity_threshold = float(context.block_init_parameters.get("similarity_threshold", 0.7))
        self.include_filename_prefix = bool(context.block_init_parameters.get("include_filename_prefix", True))
        
        # suppress pdfplumber CropBox warnings
        warnings.filterwarnings(
            "ignore",
            message="CropBox missing from /Page, defaulting to MediaBox"
        )

        # Embedding util, can swap the model name easily
        self.embedder = EmbeddingUtils(
            model_name=context.block_init_data.get("embed_model", "sentence-transformers/all-MiniLM-L6-v2"),
            device=self.device,
            max_length=self.max_length,
        )

        # supported file extensions and their extractors
        self.extractors = {
            ".pdf": extract_text_from_pdf,
            ".md": extract_text_from_file,
            ".txt": extract_text_from_file,
            ".py": extract_text_from_file,
            ".js": extract_text_from_file,
            ".java": extract_text_from_file,
            ".html": extract_text_from_file,
            ".css": extract_text_from_file,
            ".json": extract_text_from_file,
            ".yml": extract_text_from_file,
            ".yaml": extract_text_from_file,
            ".csv": extract_text_from_csv,
            ".xlsx": extract_text_from_xlsx
        }

        # Weaviate client
        self.client_type = context.block_init_data.get("client_type", "weaviate")
        if "client_type" in self.context.block_init_data and self.context.block_init_data["client_type"] == "weaviate":
            import weaviate
            from weaviate.auth import AuthClientPassword
            self.weaviate_url = self.context.block_init_data.get("client_config", {}).get("uri", "http://localhost:8080")   # Default Weaviate URI
            user=self.context.block_init_data.get("client_config", {}).get("user", "user1"),         # Add the username
            password=self.context.block_init_data.get("client_config", {}).get("password", "mypassword"), # Add the password
            auth_secret = AuthClientPassword(username=user, password=password)
            logging.getLogger("weaviate").setLevel(logging.ERROR)
            self.client = weaviate.Client(url=self.weaviate_url,auth_client_secret=auth_secret)
        

        if self.client_type == "weaviate":
            # Schema for nodes (chunks/passages)
            self.node_class = "PassageNode"
            self.edge_class = "PassageEdge"

            # Create schema if not exists
            self._ensure_weaviate_schema()
        
        logger.info(f"Initialized with chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}")

    def _ensure_weaviate_schema(self):
        """
        Create or ensure Weaviate schema exists with all needed fields.
        """
        # PassageNode: id, title, text, source, chunk_id, vector
        node_schema = {
            "class": self.node_class,
            "properties": [
                {"name": "title", "dataType": ["text"]},
                {"name": "text", "dataType": ["text"]},
                {"name": "source", "dataType": ["text"]},  # Source document path
                {"name": "chunk_id", "dataType": ["int"]}, # Sequential chunk ID within document
            ],
            "vectorizer": "none",
        }
        # PassageEdge: from, to, weight
        edge_schema = {
            "class": self.edge_class,
            "properties": [
                {"name": "from_node", "dataType": ["PassageNode"]},
                {"name": "to_node", "dataType": ["PassageNode"]},
                {"name": "weight", "dataType": ["number"]},
                {"name": "edge_type", "dataType": ["text"]}, # "similarity" or "sequential"
            ],
            "vectorizer": "none",
        }
        schema = self.client.schema.get()
        if self.node_class not in [c["class"] for c in schema["classes"]]:
            self.client.schema.create_class(node_schema)
        if self.edge_class not in [c["class"] for c in schema["classes"]]:
            self.client.schema.create_class(edge_schema)

    def on_preprocess(self, packet):
        return True, [PreProcessResult(packet=packet, extra_data={}, session_id=packet.session_id)]

    def on_data(self, pre: PreProcessResult,is_ws=False):
        try:
            if self.client_type == "weaviate":
                # 1) Walk repo and extract text
                passages = []
                for root, dirs, files in os.walk(self.repo_dir):
                    for fname in files:
                        ext = os.path.splitext(fname)[1].lower()
                        if ext not in self.extractors:
                            continue
                        if "scalelayout.txt" in fname:
                            continue
                        file_path = os.path.join(root, fname)
                        original_text = self.extractors[ext](file_path)
                        cleaned_text = clean_text(original_text, remove_stopwords=False)
                        title = os.path.relpath(file_path, self.repo_dir)
                        source = title  # Store source file path
                        # Create chunks with specified overlap (use cleaned for embedding, original for context)
                        # cleaned_chunks = list(chunk_text_split(cleaned_text, self.chunk_size, self.chunk_overlap))
                        # original_chunks = list(chunk_text_split(original_text, self.chunk_size, self.chunk_overlap))
                        cleaned_chunks = list(chunk_text_split(cleaned_text, self.chunk_size, self.chunk_overlap))
                        original_chunks = list(chunk_text_with_headers(original_text, self.chunk_size, self.chunk_overlap))
                        logger.info(f"File: {title} - Created {len(cleaned_chunks)} chunks with {self.chunk_overlap} token overlap")
                        for idx, (chunk_clean, chunk_orig) in enumerate(zip(cleaned_chunks, original_chunks)):
                            chunk_text = chunk_orig
                            if self.include_filename_prefix:
                                chunk_text = f"[{title}] {chunk_orig}"
                            passages.append({
                                "title": title,
                                "text": chunk_text,           # original for LLM context
                                "cleaned_text": chunk_clean,  # cleaned for embedding
                                "source": source,
                                "chunk_id": idx
                            })
                # 2) Serialize passages
                os.makedirs(os.path.dirname(self.passages_json), exist_ok=True)
                with open(self.passages_json, "w", encoding="utf-8") as out:
                    for p in passages:
                        out.write(json.dumps(p, ensure_ascii=False) + "\n")
                # 3) Embed passages and build node records
                embeddings = []
                node_uuids = []
                batch_size = 32
                chunks_by_source = {}
                for i in tqdm(range(0, len(passages), batch_size), desc="Embedding & pushing to Weaviate"):
                    batch_passages = passages[i : i + batch_size]
                    batch_texts = [p["cleaned_text"] for p in batch_passages]  # use cleaned for embedding
                    embs = self.embedder.get_pooled_embeddings(batch_texts)
                    embeddings.extend(embs)
                    for j, passage in enumerate(batch_passages):
                        uuid = self.client.data_object.create(
                            data_object={
                                "title": passage["title"],
                                "text": passage["text"],  # original for LLM context
                                "source": passage["source"],
                                "chunk_id": passage["chunk_id"]
                            },
                            class_name=self.node_class,
                            vector=embs[j]
                        )
                        node_uuids.append(uuid)
                        source = passage["source"]
                        if source not in chunks_by_source:
                            chunks_by_source[source] = []
                        chunks_by_source[source].append({
                            "uuid": uuid,
                            "chunk_id": passage["chunk_id"]
                        })
                # 4) Build graph - both similarity-based and sequential connections
                G = nx.Graph()
                for i, node_id in enumerate(node_uuids):
                    G.add_node(node_id, passage=passages[i], embedding=embeddings[i])

                # 5) Add edges based on similarity threshold (Graph RAG)
                similarity_edges = 0
                sequential_edges = 0
                
                # First, create sequential edges between adjacent chunks from same source
                for source, chunks in chunks_by_source.items():
                    # Sort chunks by chunk_id
                    sorted_chunks = sorted(chunks, key=lambda x: x["chunk_id"])
                    
                    # Connect sequential chunks
                    for i in range(len(sorted_chunks) - 1):
                        from_uuid = sorted_chunks[i]["uuid"]
                        to_uuid = sorted_chunks[i + 1]["uuid"]
                        
                        # Create edge with type "sequential"
                        edge_uuid = self.client.data_object.create(
                            data_object={
                                "weight": 1.0,  # Maximum weight for sequential connections
                                "edge_type": "sequential"
                            },
                            class_name=self.edge_class
                        )
                        
                        # Add the from_node and to_node references
                        self.client.data_object.reference.add(
                            from_class_name=self.edge_class,
                            from_uuid=edge_uuid,
                            from_property_name="from_node",
                            to_class_name=self.node_class,
                            to_uuid=from_uuid
                        )
                        self.client.data_object.reference.add(
                            from_class_name=self.edge_class,
                            from_uuid=edge_uuid,
                            from_property_name="to_node",
                            to_class_name=self.node_class,
                            to_uuid=to_uuid
                        )
                        
                        G.add_edge(from_uuid, to_uuid, weight=1.0, edge_type="sequential")
                        sequential_edges += 1

                # --- SPEEDUP: Vectorized similarity computation and top-K neighbors ---
                # Convert embeddings to numpy array
                embeddings_np = np.stack(embeddings)  # shape (N, D)
                norms = np.linalg.norm(embeddings_np, axis=1, keepdims=True)
                normed = embeddings_np / (norms + 1e-8)
                similarity_matrix = np.dot(normed, normed.T)  # shape (N, N)
                np.fill_diagonal(similarity_matrix, 0)  # Remove self-similarity

                K = 50  # Number of top neighbors to connect per node (tune as needed)
                for i in tqdm(range(len(node_uuids)), desc="Building similarity graph edges (top-K)"):
                    # Get indices of top-K most similar nodes
                    top_k_idx = np.argpartition(-similarity_matrix[i], K)[:K]
                    for j in top_k_idx:
                        # Skip if already connected sequentially
                        if G.has_edge(node_uuids[i], node_uuids[j]):
                            continue
                        sim = similarity_matrix[i, j]
                        if sim > self.similarity_threshold:
                            # Create the edge object with weight and type
                            edge_uuid = self.client.data_object.create(
                                data_object={
                                    "weight": float(sim),
                                    "edge_type": "similarity"
                                },
                                class_name=self.edge_class
                            )
                            # Add the from_node and to_node references
                            self.client.data_object.reference.add(
                                from_class_name=self.edge_class,
                                from_uuid=edge_uuid,
                                from_property_name="from_node",
                                to_class_name=self.node_class,
                                to_uuid=node_uuids[i]
                            )
                            self.client.data_object.reference.add(
                                from_class_name=self.edge_class,
                                from_uuid=edge_uuid,
                                from_property_name="to_node",
                                to_class_name=self.node_class,
                                to_uuid=node_uuids[j]
                            )
                            G.add_edge(node_uuids[i], node_uuids[j], weight=float(sim), edge_type="similarity")
                            similarity_edges += 1

                # # --- Multi-vector (document-level summary) embedding addition ---
                # # This block is optional and can be commented out if not needed
                # try:
                #     for root, dirs, files in os.walk(self.repo_dir):
                #         for fname in files:
                #             ext = os.path.splitext(fname)[1].lower()
                #             if ext not in self.extractors:
                #                 continue
                #             if "scalelayout.txt" in fname:
                #                 continue
                #             file_path = os.path.join(root, fname)
                #             # Check if summary file exists in /summary directory
                #             summary_dir = os.path.join(self.repo_dir, "../summary")
                #             os.makedirs(summary_dir, exist_ok=True)
                #             summary_file = os.path.join(summary_dir, os.path.splitext(os.path.relpath(file_path, self.repo_dir))[0] + ".txt")
                #             summary = None
                #             if os.path.isfile(summary_file):
                #                 try:
                #                     with open(summary_file, "r", encoding="utf-8") as sf:
                #                         summary = sf.read().strip()
                #                     print(f"Loaded summary from {summary_file}")
                #                 except Exception as e:
                #                     logger.warning(f"Failed to read summary file {summary_file}: {e}")
                #                     summary = None
                #             original_text = self.extractors[ext](file_path)
                #             print(f"Processing file for multi-vector summary: {file_path}")
                #             # Use OpenAI API to get a summary for the document
                #             try:
                #                 if not summary:
                #                     #summary = get_openai_summary(original_text,model="gpt-4")
                #                     summary = get_gemini_summary(original_text)
                #                     print(f"Generated summary for {file_path}: {summary[:300]}...")  # Log first 300 chars
                #                     if summary == "Error occurred while summarizing.":
                #                         raise ValueError("OpenAI summary is empty or None")
                #                     # Save summary to file
                #                     os.makedirs(os.path.dirname(summary_file), exist_ok=True)
                #                     with open(summary_file, "w", encoding="utf-8") as sf:
                #                         sf.write(summary)
                #             except Exception as e:
                #                 logger.warning(f"OpenAI summarization failed, using fallback: {e}")
                #                 summary = "\n".join(original_text.splitlines()[:3])
                #             summary_embedding = self.embedder.get_pooled_embeddings([summary])[0]
                #             # Store the summary as a special passage (chunk_id = -1)
                #             passages.append({
                #                 "title": os.path.relpath(file_path, self.repo_dir),
                #                 "text": f"[SUMMARY] {original_text}",
                #                 "cleaned_text": clean_text(summary, remove_stopwords=False),
                #                 "source": os.path.relpath(file_path, self.repo_dir),
                #                 "chunk_id": -1
                #             })
                #             # Optionally, push the summary embedding to Weaviate as a node
                #             self.client.data_object.create(
                #                 data_object={
                #                     "title": os.path.relpath(file_path, self.repo_dir),
                #                     "summary": f"[SUMMARY] {summary}",
                #                     "text": f"[SUMMARY] {original_text}",
                #                     "source": os.path.relpath(file_path, self.repo_dir),
                #                     "chunk_id": -1
                #                 },
                #                 class_name=self.node_class,
                #                 vector=summary_embedding
                #             )
                # except Exception as e:
                #     logger.warning(f"[Multi-vector summary addition] {e}")
                # # # --- End multi-vector addition ---

                msg = f"Indexed {len(node_uuids)} passages with {self.chunk_overlap} token overlap.\n"
                msg += f"Built graph with {sequential_edges} sequential edges and {similarity_edges} similarity edges."
                logger.info(msg)
                return True, OnDataResult(output={"message": msg})
        except Exception as e:
            logger.error(f"[Indexing Error] {e}", exc_info=True)
            return False, str(e)

    def on_update(self, params):
        for key in ("repo_dir", "passages_json"):
            if key in params:
                setattr(self, key, params[key])
        if "chunk_size" in params:
            self.chunk_size = int(params["chunk_size"])
        if "chunk_overlap" in params:
            self.chunk_overlap = int(params["chunk_overlap"])
        if "max_length" in params:
            self.max_length = int(params["max_length"])
        if "similarity_threshold" in params:
            self.similarity_threshold = float(params["similarity_threshold"])
        if "include_filename_prefix" in params:
            self.include_filename_prefix = bool(params["include_filename_prefix"])
        return True, params

    def reset_weaviate(self):
        for class_name in [self.node_class, self.edge_class]:
            try:
                self.client.schema.delete_class(class_name)
            except Exception as e:
                logger.warning(f"Could not delete {class_name}: {e}")
        self._ensure_weaviate_schema()

    def health(self):
        # Check if node class exists and has any objects
        try:
            nodes = self.client.data_object.get(class_name=self.node_class, limit=1)
            exists = len(nodes.get('objects', [])) > 0
        except Exception:
            exists = False
        return {
            "status": "healthy" if exists else "unhealthy", 
            "graph_exists": exists,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "timestamp": "2025-06-17 11:57:53"  # Current UTC time from context
        }

    def management(self, action, data):
        if action == "reset":
            self.reset_weaviate()
            # Optionally clear the whole schema/classes in Weaviate if needed
            return {"message": "Weaviate schema reset"}
        
        if action == "set_chunking_params":
            if "chunk_size" in data:
                self.chunk_size = int(data["chunk_size"])
            if "chunk_overlap" in data:
                self.chunk_overlap = int(data["chunk_overlap"])
            return {
                "message": f"Chunking parameters updated: chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}"
            }
            
        return {"message": f"Unknown action: {action}"}

    def get_muxer(self):
        return None



if __name__ == "__main__":
    Block(IndexDocumentsBlock).run()