import os
import json
import logging
import torch
import weaviate
import requests
import time
from aios_instance import PreProcessResult, OnDataResult, Block
from aios_transformers.library import TransformersUtils
from transformers import BitsAndBytesConfig
from sentence_transformers import CrossEncoder

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

#logger = logging.getLogger(__name__)

# Configure more verbose logging for debugging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

class OpenAIClient:
    """
    Client for OpenAI API with enhanced debugging and error handling
    Handles all interaction with the OpenAI API, including model listing and chat completions
    """
    def __init__(self, debug=False):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("The OPENAI_API_KEY environment variable must be set for OpenAI API access.")
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.debug = debug
        
    def get_models(self):
        """
        Fetches available models from OpenAI API.
        """
        api_url = f"{self.base_url}/models"
        try:
            response = requests.get(api_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            models = [model["id"] for model in data.get("data", [])]
            # Filter to only include chat models
            chat_models = [model for model in models if "gpt" in model.lower()]
            return chat_models
        except Exception as e:
            logger.error(f"Error fetching models from OpenAI API: {e}")
            return ["gpt-3.5-turbo"] # Return default model if API fails
            
    def generate_chat_completion(self, model_id, messages, temperature=0.3, max_tokens=256, **kwargs):
        """
        Calls the OpenAI chat completions API to generate a response.
        """
        api_url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if value is not None:
                payload[key] = value
        
        # Debug: Print the messages being sent (if debug is enabled)
        if self.debug:
            logger.info(f"===== OPENAI REQUEST =====")
            logger.info(f"Model: {model_id}")
            logger.info(f"Temperature: {temperature}, Max tokens: {max_tokens}")
            logger.info("Messages:")
            for i, msg in enumerate(messages):
                content_preview = msg['content'][:100] + ('...' if len(msg['content']) > 100 else '')
                logger.info(f"[{i}] {msg['role']}: {content_preview}")
            logger.info("=========================")
        response = None
        try:
            print(self.headers)
            response = requests.post(api_url, headers=self.headers, json=payload, timeout=90)
            response.raise_for_status()
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            logger.warning(f"Unexpected response format from OpenAI API: {data}")
            return ""
        except Exception as e:
            logger.error(f"Error generating completion from OpenAI API: {e}")
            if response is not None:
                logger.error(f"Response status code: {response.status_code}, Response Headers: {response.headers}")
            raise

    def generate_embeddings(self, texts, model="text-embedding-ada-002"):
        """
        Generates embeddings for a list of texts using OpenAI's embedding API.
        """
        api_url = f"{self.base_url}/embeddings"
        
        if isinstance(texts, str):
            texts = [texts]
            
        payload = {
            "model": model,
            "input": texts
        }
                
        try:
            response = requests.post(api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "data" in data and len(data["data"]) > 0:
                # Return list of embeddings
                return [item["embedding"] for item in data["data"]]
            
            logger.warning(f"Unexpected response format from OpenAI embedding API: {data}")
            return []
        except Exception as e:
            logger.error(f"Error generating embeddings from OpenAI API: {e}")
            raise

class GeminiClient:
    """
    Client for Google Gemini API with enhanced debugging and error handling
    Handles all interaction with the Gemini API, including model listing and chat completions
    """
    def __init__(self, debug=False):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("The GEMINI_API_KEY environment variable must be set for Gemini API access.")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.headers = {
            "Content-Type": "application/json"
        }
        self.debug = debug
        self.available_models = [
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash-latest",
            "gemini-pro",
            "gemini-pro-vision"
        ]
        
    def get_models(self):
        """
        Returns available Gemini models.
        """
        return self.available_models
    
    def list_models_from_api(self):
        """
        Fetches available models from Gemini API and displays them.
        Returns a list of available models with their details.
        """
        api_url = f"{self.base_url}/models?key={self.api_key}"
        
        if self.debug:
            logger.info(f"===== GEMINI LIST MODELS =====")
            logger.info(f"API URL: {api_url}")
            
        try:
            response = requests.get(api_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "models" in data:
                models = data["models"]
                model_list = []
                
                print("\n" + "="*80)
                print("AVAILABLE GEMINI MODELS")
                print("="*80)
                print(f"{'Model Name':<35} {'Version':<15} {'Display Name':<30}")
                print("-"*80)
                
                for model in models:
                    name = model.get("name", "").replace("models/", "")
                    version = model.get("version", "N/A")
                    display_name = model.get("displayName", "N/A")
                    description = model.get("description", "")
                    
                    # Truncate display name if too long
                    display_name = display_name[:28] + ".." if len(display_name) > 30 else display_name
                    
                    print(f"{name:<35} {version:<15} {display_name:<30}")
                    
                    model_info = {
                        "name": name,
                        "full_name": model.get("name", ""),
                        "version": version,
                        "display_name": model.get("displayName", ""),
                        "description": description,
                        "supported_generation_methods": model.get("supportedGenerationMethods", []),
                        "input_token_limit": model.get("inputTokenLimit", "N/A"),
                        "output_token_limit": model.get("outputTokenLimit", "N/A")
                    }
                    model_list.append(model_info)
                
                print("="*80)
                print(f"Total models: {len(models)}")
                print("="*80 + "\n")
                
                # Update available models with API response
                self.available_models = [model["name"] for model in model_list if "generateContent" in model.get("supported_generation_methods", [])]
                
                if self.debug:
                    logger.info(f"Updated available models: {self.available_models}")
                    logger.info("=============================")
                
                return model_list
            else:
                logger.warning(f"Unexpected response format from Gemini API: {data}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching models from Gemini API: {e}")
            return []
            
    def generate_chat_completion(self, model_id, messages, temperature=0.3, max_tokens=256, **kwargs):
        """
        Calls the Gemini API to generate a response from messages.
        Converts OpenAI-style messages to Gemini format.
        """
        # Convert model name if needed
        if not model_id.startswith("models/"):
            model_id = f"models/{model_id}"
            
        api_url = f"{self.base_url}/{model_id}:generateContent?key={self.api_key}"
        
        # Convert OpenAI-style messages to Gemini format
        gemini_contents = []
        system_instruction = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                gemini_contents.append({
                    "role": "user",
                    "parts": [{"text": msg["content"]}]
                })
            elif msg["role"] == "assistant":
                gemini_contents.append({
                    "role": "model",
                    "parts": [{"text": msg["content"]}]
                })
        
        # Build the payload
        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature
            }
        }
        
        # Add system instruction if provided
        if system_instruction:
            payload["systemInstruction"] = {
                "role": "user",
                "parts": [{"text": system_instruction}]
            }
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if value is not None:  # max_tokens is handled above
                payload["generationConfig"][key] = value
        
        # Debug: Print the messages being sent (if debug is enabled)
        if self.debug:
            logger.info(f"===== GEMINI REQUEST =====")
            logger.info(f"Model: {model_id}")
            logger.info(f"Temperature: {temperature}, Max tokens: {max_tokens}")
            logger.info("Messages:")
            for i, msg in enumerate(messages):
                content_preview = msg['content'][:100] + ('...' if len(msg['content']) > 100 else '')
                logger.info(f"[{i}] {msg['role']}: {content_preview}")
            logger.info("=========================")
            
        response = None
        try:
            response = requests.post(api_url, headers=self.headers, json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()
            
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    return candidate["content"]["parts"][0]["text"]
            
            logger.warning(f"Unexpected response format from Gemini API: {data}")
            return ""
        except Exception as e:
            logger.error(f"Error generating completion from Gemini API: {e}")
            if response is not None:
                logger.error(f"Response status code: {response.status_code}, Response text: {response.text}")
            raise

    def get_gemini_summary(self, text, model="models/gemini-1.5-pro-latest", max_tokens=256):
        """
        Use Google Gemini API to summarize a document.
        """
        prompt = (
            "Summarize the following document in a concise paragraph, capturing all key points and main ideas. "
            "If the document is a table, summarize its purpose and the type of information it contains.\n\n" + text[:6000]
        )
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            return self.generate_chat_completion(model, messages, temperature=0.2, max_tokens=max_tokens)
        except Exception as e:
            logger.error(f"Error occurred in Gemini summary: {e}")
            return "Error occurred while summarizing."

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
        self.max_length = max_length
        self._load_model(model_name)
        
    def _load_model(self, model_name):
        self.model_name = model_name
        if "sentence-transformers" in model_name:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name, device=(device or "cuda" if torch.cuda.is_available() else "cpu"))
            #self.max_length = max_length
        elif "openai" in model_name:
            #model_name should openai/text-embedding-3-large
            OPENAI_API_KEY="YOUR_API_KEY"
            if OPENAI_API_KEY == "YOUR_API_KEY":
                OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
            from llama_index.embeddings.openai import OpenAIEmbedding
            model_version = model_name.split("/")[-1]  # Extract model name from path
            self.model = OpenAIEmbedding(model=model_version, \
                        api_key=OPENAI_API_KEY,
                        dimensions=self.max_length)
            #self.max_length = max_length

    def switch_model(self, model_name):
        if model_name != self.model_name:
            self._load_model(model_name)

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

class SentenceTransformerUtils:
    """
    Wraps a SentenceTransformer model for generic embedding.
    Used as fallback when OpenAI embedding API is not available.
    """
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = None,
        max_length: int = 512,
    ):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_length = max_length
        self._load_model(model_name)

    def _load_model(self, model_name):
        # from sentence_transformers import SentenceTransformer
        # self.model = SentenceTransformer(model_name, device=self.device)
        # self.model_name = model_name

        # Embedding util, can swap the model name easily
        self.model = EmbeddingUtils(
            model_name=model_name,
            device=self.device,
            max_length=self.max_length,
        )

    def switch_model(self, model_name):
        if model_name != self.model_name:
            self._load_model(model_name)

    def get_pooled_embeddings(self, texts):
        #return self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return self.model.get_pooled_embeddings(texts)

def get_graphrag_passages_from_weaviate(
    client, node_class, edge_class, query_emb, topk=5, similarity_threshold=0.7, 
    edge_limit=10, debug=False
):
    """
    Enhanced GraphRAG retrieval function that returns full passage metadata for proper references.
    Compatible with overlapping chunks indexer schema (only uses fields that exist).
    
    Args:
        client: Weaviate client
        node_class: Node class name (e.g., "PassageNode")
        edge_class: Edge class name (e.g., "PassageEdge")  
        query_emb: Query embedding vector
        topk: Number of initial similar passages to retrieve
        similarity_threshold: Similarity threshold for vector search
        edge_limit: Maximum number of edges to follow per node
        debug: Enable debug logging
    """
    start_time = time.time()
    
    if debug:
        logger.info(f"===== RAG RETRIEVAL =====")
        logger.info(f"Query: Vector of dimension {len(query_emb[0]) if isinstance(query_emb, list) and len(query_emb) > 0 else 'unknown'}")
        logger.info(f"Node class: {node_class}, Edge class: {edge_class}")
        logger.info(f"Top-k: {topk}, Similarity threshold: {similarity_threshold}, Edge limit: {edge_limit}")
    
    # Variable to collect passage information for grid display
    passage_grid_data = []
    
    # Retrieve nodes with ONLY fields that exist in index_documents_block.py schema
    # Schema fields: title, text, source, chunk_id (confirmed from indexer)
    try:
        resp = client.query.get(node_class, ["title", "text", "source", "chunk_id", "_additional {certainty}"])\
            .with_near_vector({"vector": query_emb[0] if isinstance(query_emb[0], list) else query_emb[0].tolist(), 
                            "certainty": similarity_threshold})\
            .with_limit(topk).do()
    except Exception as e:
        if debug:
            logger.warning(f"Failed to query with all fields, falling back to basic fields: {e}")
        # Fall back to just title and text if other fields aren't available
        resp = client.query.get(node_class, ["title", "text", "_additional {certainty}"])\
            .with_near_vector({"vector": query_emb[0] if isinstance(query_emb[0], list) else query_emb[0].tolist(), 
                            "certainty": similarity_threshold})\
            .with_limit(topk).do()
    
    hits = resp.get("data", {}).get("Get", {}).get(node_class) or []
    
    if debug:
        logger.info(f"Found {len(hits)} initial passages via vector similarity")
        
    node_ids = []
    passages = []
    
    # Process primary hits from vector similarity search
    for h in hits:
        # Extract metadata using ONLY fields from index_documents_block.py
        passage_data = {
            "text": h["text"],
            "title": h.get("title", "Untitled passage"),
            "id": h.get("id", ""),
            "source": h.get("source", "Unknown source"),
            "chunk_id": h.get("chunk_id", 0),
            # Legacy compatibility fields (not in indexer but needed for format_references)
            "url": "",  # Not available in indexer schema
            "doc_id": h.get("source", ""),  # Use source as doc_id for compatibility
            "certainty": h.get("_additional", {}).get("certainty", 0.0) if "_additional" in h else 0.0
        }
        
        if "id" in h:
            node_ids.append(h["id"])
        
        passages.append(passage_data)
        
        # Add to grid data for display
        passage_grid_data.append({
            "Source": passage_data["title"],
            "Score": f"{passage_data['certainty']:.4f}",
            "Chunk": passage_data["chunk_id"],
            "Type": "initial"
        })
        
        if debug:
            certainty = passage_data["certainty"]
            title = passage_data["title"]
            chunk_id = passage_data["chunk_id"]
            logger.info(f"Passage [initial]: Score={certainty:.4f}, Source={title}, Chunk={chunk_id}")
            logger.info(f"Text preview: {h['text'][:150]}...")
    
    # Get neighboring nodes through graph edges (both similarity and sequential)
    neighbor_count = 0
    for node_id in node_ids:
        try:
            # Query for edges with configurable limit - try to get edge_type if available
            edge_resp = client.query.get(edge_class, ["from_node", "to_node", "weight", "edge_type"])\
                .with_where({
                    "operator": "Or",
                    "operands": [
                        {
                            "path": ["from_node", "id"],
                            "operator": "Equal",
                            "valueString": node_id
                        },
                        {
                            "path": ["to_node", "id"],
                            "operator": "Equal",
                            "valueString": node_id
                        }
                    ]
                }).with_limit(edge_limit).do()
        except Exception as e:
            if debug:
                logger.warning(f"Failed to query edges with edge_type, falling back: {e}")
            # Fall back without edge_type if field doesn't exist (older schema)
            edge_resp = client.query.get(edge_class, ["from_node", "to_node", "weight"])\
                .with_where({
                    "operator": "Or",
                    "operands": [
                        {
                            "path": ["from_node", "id"],
                            "operator": "Equal",
                            "valueString": node_id
                        },
                        {
                            "path": ["to_node", "id"],
                            "operator": "Equal",
                            "valueString": node_id
                        }
                    ]
                }).with_limit(edge_limit).do()
                
        edges = edge_resp.get("data", {}).get("Get", {}).get(edge_class) or []
        
        if debug:
            logger.info(f"Found {len(edges)} connected edges for node {node_id}")
            
        for edge in edges:
            neighbor_id = None
            edge_weight = edge.get("weight", 0.0)
            edge_type = edge.get("edge_type", "unknown")
            if edge_type == "sequential":
                edge_weight += 0.2  # Boost sequential connections
            # Determine which node is the neighbor
            if edge.get("from_node", [{}])[0].get("id") != node_id:
                neighbor_id = edge.get("from_node", [{}])[0].get("id")
            elif edge.get("to_node", [{}])[0].get("id") != node_id:
                neighbor_id = edge.get("to_node", [{}])[0].get("id")
                
            if neighbor_id:
                try:
                    # Try to get neighbor with fields from indexer schema
                    neighbor_resp = client.query.get(node_class, ["title", "text", "source", "chunk_id"])\
                        .with_where({"path": ["id"], "operator": "Equal", "valueString": neighbor_id})\
                        .with_limit(1).do()
                except Exception:
                    # Fall back to just title and text
                    neighbor_resp = client.query.get(node_class, ["title", "text"])\
                        .with_where({"path": ["id"], "operator": "Equal", "valueString": neighbor_id})\
                        .with_limit(1).do()
                
                neighbor_hits = neighbor_resp.get("data", {}).get("Get", {}).get(node_class) or []
                
                for nh in neighbor_hits:
                    # Create passage data structure with metadata
                    neighbor_data = {
                        "text": nh["text"],
                        "title": nh.get("title", "Untitled passage"),
                        "id": neighbor_id,
                        "source": nh.get("source", "Unknown source"),
                        "chunk_id": nh.get("chunk_id", 0),
                        # Legacy compatibility fields
                        "url": "",  # Not available in indexer schema
                        "doc_id": nh.get("source", ""),  # Use source as doc_id
                        "certainty": edge_weight  # Use edge weight as certainty for neighbors
                    }
                    passages.append(neighbor_data)
                    neighbor_count += 1
                    
                    # Add to grid data for display
                    passage_grid_data.append({
                        "Source": neighbor_data["title"],
                        "Score": f"{edge_weight:.4f}",
                        "Chunk": neighbor_data["chunk_id"],
                        "Type": edge_type
                    })
                    
                    if debug:
                        title = neighbor_data["title"]
                        chunk_id = neighbor_data["chunk_id"]
                        logger.info(f"Passage [neighbor-{edge_type}]: Weight={edge_weight:.4f}, Source={title}, Chunk={chunk_id}")
    
    # # --- Multi-vector (summary node) retrieval addition ---
    # try:
    #     # Retrieve summary nodes (chunk_id = -1) for the same query embedding
    #     summary_resp = client.query.get(node_class, ["title", "text", "source", "chunk_id", "summary", "_additional {certainty}"])\
    #         .with_near_vector({"vector": query_emb[0] if isinstance(query_emb[0], list) else query_emb[0].tolist(),
    #                            "certainty": similarity_threshold})\
    #         .with_where({
    #             "path": ["chunk_id"],
    #             "operator": "Equal",
    #             "valueInt": -1
    #         })\
    #         .with_limit(3).do()
    #     summary_hits = summary_resp.get("data", {}).get("Get", {}).get(node_class) or []
    #     for h in summary_hits:
    #         # Avoid duplicates
    #         if not any(p["text"] == h["text"] for p in passages):
    #             passages.append({
    #                 "text": h["text"],
    #                 "title": h.get("title", "Summary"),
    #                 "id": h.get("id", ""),
    #                 "source": h.get("source", "Unknown source"),
    #                 "chunk_id": h.get("chunk_id", -1),
    #                 "summary": h.get("summary", ""),
    #                 "url": "",
    #                 "doc_id": h.get("source", ""),
    #                 "certainty": h.get("_additional", {}).get("certainty", 0.0) if "_additional" in h else 0.0
    #             })
                
    #             # Add to grid data for display
    #             passage_grid_data.append({
    #                 "Source": h.get("title", "Summary"),
    #                 "Score": f"{h.get('_additional', {}).get('certainty', 0.0):.4f}" if "_additional" in h else "0.0000",
    #                 "Chunk": h.get("chunk_id", -1),
    #                 "Type": "summary"
    #             })
    # except Exception as e:
    #     logger.warning(f"[Multi-vector summary retrieval] {e}")
    # # --- End multi-vector addition ---
    
    # Remove duplicates while preserving order
    unique_passages = []
    seen_texts = set()
    
    for p in passages:
        if "summary" in p and p["summary"]:
            # If summary exists, use it as the text for uniqueness check
            if p["summary"] not in seen_texts:
                unique_passages.append(p)
                seen_texts.add(p["summary"])
                continue
        elif p["text"] not in seen_texts:
            unique_passages.append(p)
            seen_texts.add(p["text"])
    
    elapsed_time = time.time() - start_time
    
    # Print passage grid data
    if passage_grid_data:
        print("\n" + "="*80)
        print("RETRIEVED PASSAGES SUMMARY")
        print("="*80)
        print(f"{'Source':<30} {'Score':<8} {'Chunk':<6} {'Type':<12}")
        print("-"*80)
        for data in passage_grid_data:
            source = data["Source"][:40] + ".." if len(data["Source"]) > 40 else data["Source"]
            print(f"{source:<40} {data['Score']:<8} {data['Chunk']:<6} {data['Type']:<12}")
        print("="*80)
        print(f"Total passages: {len(unique_passages)} | Time: {elapsed_time:.2f}s")
        print("="*80 + "\n")
    
    if debug:
        logger.info(f"RAG stats: {len(hits)} initial hits, {neighbor_count} neighbors, {len(unique_passages)} unique passages")
        logger.info(f"RAG retrieval completed in {elapsed_time:.2f} seconds")
        logger.info("========================")
        
    # Return full passage objects with metadata for proper reference formatting
    return unique_passages

def format_references(passages):
    """
    Format a list of passage objects into a references section
    Compatible with overlapping chunks indexer metadata
    """
    references = []
    
    for i, passage in enumerate(passages, 1):
        # Extract meaningful reference information from available fields
        title = passage.get("title", "Untitled passage")
        source = passage.get("source", "Unknown source")
        chunk_id = passage.get("chunk_id", "")
        url = passage.get("url", "")
        certainty = passage.get("certainty", 0.0)
        
        # Build reference string with available information
        ref_parts = [f"[{i}] {title}"]
        
        if source and source != "Unknown source" and source != title:
            ref_parts.append(f"Source: {source}")
            
        if chunk_id is not None and chunk_id != "":
            ref_parts.append(f"Chunk: {chunk_id}")
            
        if url and url.strip():
            ref_parts.append(f"URL: {url}")
        
        # Add relevance score for debugging
        if certainty > 0:
            ref_parts.append(f"Relevance: {certainty:.3f}")
            
        references.append(" - ".join(ref_parts))
    
    return references

def add_references_to_response(answer, references):
    """
    Add references section to the response if it doesn't already have one.
    """
    if "References:" not in answer and "REFERENCES:" not in answer:
        return f"{answer}\n\nReferences:\n" + "\n".join(references)
    return answer



def rerank_passages(reranker, query, passages, top_n=None):
    """
    Rerank retrieved passages using a cross-encoder model.
    Args:
        query: The user query (string)
        passages: List of passage dicts with 'text' field
        top_n: If set, return only top_n reranked passages
    Returns:
        List of passages sorted by rerank score (descending)
    """
    if reranker is None:
        logger.warning("Reranker model is not loaded. Skipping reranking.")
        return passages
    # Use summary if available, else fall back to text
    pairs = [(query, p.get('summary', p.get('cleaned_text', ''))) for p in passages]
    #print(f"Reranking {len(pairs)} passage pairs with model ")
    scores = reranker.predict(pairs)
    for p, s in zip(passages, scores):
        p['rerank_score'] = float(s)
    reranked = sorted(passages, key=lambda x: x['rerank_score'], reverse=True)
    if top_n:
        # Iterative logic to ensure only one chunk per file (summary preferred), and top_n results
        selected = reranked[:top_n]
        last_fetched = top_n
        while True:
            # Build a map: source -> list of (chunk_id, idx)
            source_chunks = {}
            for idx, p in enumerate(selected):
                source = p.get('source', None)
                chunk_id = p.get('chunk_id', None)
                if source not in source_chunks:
                    source_chunks[source] = []
                source_chunks[source].append((chunk_id, idx))
            # Find sources with both summary and other chunks
            #print("source_chunks:", source_chunks)
            to_remove_idxs = set()
            for source, chunks in source_chunks.items():
                has_summary = any(cid == -1 for cid, _ in chunks)
                if has_summary and len(chunks) > 1:
                    # Remove all chunk_id > 0 for this source
                    for cid, idx in chunks:
                        if cid != -1:
                            to_remove_idxs.add(idx)
            # Remove marked indices
            #print(f"Removing {to_remove_idxs} conflicting chunks from selected passages")
            if to_remove_idxs:
                selected = [p for idx, p in enumerate(selected) if idx not in to_remove_idxs]
            # If after removal, selected is less than top_n, fetch more from reranked
            if len(selected) < top_n:
                needed = top_n - len(selected)
                # Get more candidates from reranked, skipping already selected ones (by id or (source, chunk_id))
                selected_keys = set((p.get('source', None), p.get('chunk_id', None)) for p in selected)
                # Extend the window to fetch more candidates
                new_last_fetched = last_fetched + needed
                candidates = reranked[last_fetched:new_last_fetched]
                for p in candidates:
                    key = (p.get('source', None), p.get('chunk_id', None))
                    if key not in selected_keys:
                        selected.append(p)
                        selected_keys.add(key)
                last_fetched = new_last_fetched
                # If no new candidates were added, break to avoid infinite loop
                if not candidates:
                    break
            else:
                # If selected is now top_n, check again for conflicts, else break
                if len(selected) == top_n:
                    # Check if any source still has both summary and chunk>0
                    source_chunks = {}
                    for idx, p in enumerate(selected):
                        source = p.get('source', None)
                        chunk_id = p.get('chunk_id', None)
                        if source not in source_chunks:
                            source_chunks[source] = []
                        source_chunks[source].append((chunk_id, idx))
                    conflict = False
                    for source, chunks in source_chunks.items():
                        has_summary = any(cid == -1 for cid, _ in chunks)
                        if has_summary and len(chunks) > 1:
                            conflict = True
                            break
                    if not conflict:
                        break
                else:
                    break
        return selected[:top_n]
    return reranked

class RagQAServiceBlock:
    """
    Block supporting multiple modes: chat, rag-chat, generate, tokens, embed.
    Uses OpenAI API for completions and embeddings with fallback to local models.
    Enhanced with proper reference formatting for RAG outputs.
    """
    def __init__(self, context):
        self.context = context
        self.passages_json = context.block_init_data.get("passages_json", "data/psgs_w100.jsonl")
        self.topk = int(context.block_init_parameters.get("topk", 5))
        self.edge_limit = int(context.block_init_parameters.get("edge_limit", 10))  # New configurable parameter
        self.max_length = int(context.block_init_parameters.get("max_length", 512))
        self.similarity_threshold = float(context.block_init_parameters.get("similarity_threshold", 0.7))
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.reranking_topk = int(context.block_init_parameters.get("reranking_topk", 20))
        self.reranking_model_name = context.block_init_parameters.get("reranking_model", "cross-encoder/ms-marco-MiniLM-L-12-v2")

        # Debug mode
        self.debug = context.block_init_parameters.get("debug", True)

        self.weaviate_url = context.block_init_data.get("weaviate_url", "http://localhost:8080")
        self.node_class = context.block_init_data.get("node_class", "PassageNode")
        self.edge_class = context.block_init_data.get("edge_class", "PassageEdge")
        self.client = weaviate.Client(self.weaviate_url)

        llm_model = context.block_init_data.get("llm_model")
        self.openai_client = None
        self.use_openai = False
        self.use_openai_embeddings = False
        self.gemini_models = []
        self.use_gemini = False

        if "openai" in llm_model or "gpt" in llm_model:
            # Initialize the OpenAI API client
            try:
                self.openai_client = OpenAIClient(debug=self.debug)
                # Get available models from OpenAI API
                self.available_models = self.openai_client.get_models()
                logger.info(f"Available OpenAI models: {self.available_models}")
                self.use_openai = True
                # Set default LLM model to gpt-4o for better RAG performance
                self.llm_model = context.block_init_data.get(
                    "llm_model", "gpt-4o" if "gpt-4o" in self.available_models else 
                    ("gpt-3.5-turbo" if "gpt-3.5-turbo" in self.available_models else self.available_models[0])
                )
                # Try to use OpenAI embeddings
                self.use_openai_embeddings = False
                self.embedding_model = "text-embedding-ada-002"
            except Exception as e:
                logger.error(f"Error initializing OpenAI API: {e}")
                # Fallback to using TransformersUtils if OpenAI API fails
                self.available_models = []
                self.openai_client = None
                self.use_openai = False
                self.use_openai_embeddings = False
        elif "gemini" in llm_model:
            # Initialize the Gemini API client
            try:
                self.gemini_client = GeminiClient(debug=self.debug)
                self.gemini_client.list_models_from_api()
                # Get available models from Gemini API
                self.gemini_models = self.gemini_client.get_models()
                logger.info(f"Available Gemini models: {self.gemini_models}")
                self.use_gemini = True
                # Set default Gemini model
                self.llm_model = context.block_init_data.get(
                    "llm_model", "gemini-1.5-pro-latest"
                )
            except Exception as e:
                logger.error(f"Error initializing Gemini API: {e}")
                self.gemini_client = None
                self.gemini_models = []
                self.use_gemini = False
        
        # Set default embedding model (either OpenAI or local)
        self.embed_model = context.block_init_data.get(
            "embed_model", "sentence-transformers/all-MiniLM-L6-v2" 
        )
        
        # Initialize local embedder as fallback
        # self.embedder = SentenceTransformerUtils(
        #     model_name=self.embed_model,
        #     device=self.device,
        #     max_length=self.max_length,
        # )

        # Embedding util, can swap the model name easily
        self.embedder = EmbeddingUtils(
            model_name=self.embed_model,
            device=self.device,
            max_length=self.max_length,
        )

        # Load reranker model once at module level
        #RERANKER_MODEL_NAME = self.reranking_model_name #'cross-encoder/ms-marco-MiniLM-L-6-v2'
        try:
            self.reranker = CrossEncoder(self.reranking_model_name)
        except Exception as e:
            logger.error(f"Failed to load reranker model {self.reranking_model_name}: {e}")
            self.reranker = None

        # Setup local model as fallback if OpenAI is not available
        if not self.use_openai and not self.use_gemini:
            logger.warning("Falling back to local model as OpenAI API is not available")
            # Configure the local model as fallback
            bnb_cfg = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype="float16"
            )
            self.utils = TransformersUtils(
                model_name=context.block_init_data.get(
                    "local_model", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"),
                device=self.device,
                tensor_parallel=context.block_init_data.get("tensor_parallel", True),
                quantize=False,
                generation_config=context.block_init_parameters.get(
                    "generation_config", {"max_new_tokens":256, "temperature":0.3}
                )
            )
            self.utils.load_model(extra_args={
                "quantization_config": bnb_cfg,
                "device_map": "auto",
                "low_cpu_mem_usage": True,
                "torch_dtype": "auto",
            })

        # Store chat sessions
        self.chat_sessions = {}
        
        # Generation configuration - optimized for RAG
        self.generation_config = context.block_init_parameters.get(
            "generation_config", {
                "max_tokens": 4096,  # Increased for comprehensive responses
                "temperature": 0.1   # Lower for more focused, factual responses
            }
        )
        
        # Add auto-references setting (enables appending references to RAG responses)
        self.auto_references = context.block_init_parameters.get("auto_references", True)
        
        logger.info(f"RagQAServiceBlock initialized with debug={self.debug}, auto_references={self.auto_references}")
        logger.info(f"Top-k: {self.topk}, Edge limit: {self.edge_limit}")
        logger.info(f"Current user: shridharkini, Time: 2025-06-17 12:47:37")

    def reorder_passages_by_sequence(self, passages):
        """Reorders passages to maintain document flow based on chunk IDs"""
        # Group passages by source document
        docs = {}
        for p in passages:
            source = p.get("source", "")
            if source not in docs:
                docs[source] = []
            docs[source].append(p)
        
        # Sort each document's chunks by chunk_id
        for source in docs:
            docs[source] = sorted(docs[source], key=lambda x: x.get("chunk_id", 0))
        
        # Interleave results but prioritize directly relevant chunks
        result = []
        # First add direct matches (high certainty)
        for p in passages:
            if p.get("certainty", 0) > 0.7:  # Direct vector match
                result.append(p)
        
        # Then add sequential chunks from the same documents
        for source in docs:
            for p in docs[source]:
                if p not in result:  # Avoid duplicates
                    result.append(p)
        
        return result

    def create_chat_session(self, session_id, system_message=""):
        """Create a new chat session with optional system message"""
        if not system_message:
            system_message = "You are a helpful AI assistant that provides accurate, detailed responses based on provided context."
        
        self.chat_sessions[session_id] = [
            {"role": "system", "content": system_message}
        ]
        return session_id
    
    def add_message_to_chat(self, session_id, message, role="user"):
        """Add a message to the chat session"""
        if session_id not in self.chat_sessions:
            self.create_chat_session(session_id,message)
            
        self.chat_sessions[session_id].append({"role": role, "content": message})
        return True
        
    def run_chat_inference(self, session_id):
        """Run inference on the chat session and add the response to the chat history"""
        if session_id not in self.chat_sessions:
            raise ValueError(f"Chat session {session_id} not found")
            
        messages = self.chat_sessions[session_id]
        
        if self.debug:
            logger.info(f"Running inference for session {session_id} with {len(messages)} messages")
        
        # Determine which model to use based on llm_model setting
        if self.use_openai and ("gpt" in self.llm_model.lower() or self.llm_model in self.available_models):
            response = self.openai_client.generate_chat_completion(
                self.llm_model,
                messages,
                **self.generation_config
            )
        elif self.use_gemini and ("gemini" in self.llm_model.lower() or self.llm_model in self.gemini_models):
            response = self.gemini_client.generate_chat_completion(
                self.llm_model,
                messages,
                **self.generation_config
            )
        else:
            # Fallback to local model if neither OpenAI nor Gemini API is available/selected
            # First, ensure the session exists in the utility's chat sessions
            if session_id not in self.utils.chat_sessions:
                system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
                self.utils.create_chat_session(session_id, system_msg)
                
                # Add all non-system messages
                for msg in messages:
                    if msg["role"] != "system":
                        self.utils.add_message_to_chat(session_id, msg["content"], role=msg["role"])
            
            response = self.utils.run_chat_inference(session_id)
        
        # Add assistant response to chat history
        self.chat_sessions[session_id].append({"role": "assistant", "content": response})
        
        return response
    
    def get_embeddings(self, texts):
        """Get embeddings for texts using either OpenAI API or local model"""
        if self.use_openai_embeddings:
            try:
                return self.openai_client.generate_embeddings(texts)
            except Exception as e:
                logger.error(f"Error using OpenAI embeddings, falling back to local: {e}")
                self.use_openai_embeddings = False  # Switch to local for future calls
                
        # Fall back to local embeddings
        return self.embedder.get_pooled_embeddings(texts)

    def on_preprocess(self, packet):
        data = packet.data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                # If not valid JSON, treat as raw text
                data = {"payload": data}
        mode = data.get("mode", "rag")
        payload = data.get("payload", data)
        return True, [PreProcessResult(packet=packet, extra_data={"mode": mode, "payload": payload}, session_id=packet.session_id)]

    def on_data(self, pre: PreProcessResult, is_ws=False):
        mode = pre.extra_data.get("mode")
        pld = pre.extra_data.get("payload")
        try:
            # Handle model change dynamically via payload
            requested_embed_model = None
            requested_llm_model = None
            
            if isinstance(pld, dict):
                requested_embed_model = pld.get("embed_model")
                requested_llm_model = pld.get("llm_model")
                
            if requested_embed_model:
                if self.use_openai_embeddings and "text-embedding" in requested_embed_model:
                    self.embedding_model = requested_embed_model
                else:
                    self.embedder.switch_model(requested_embed_model)
                
            if requested_llm_model:
                # Check if it's an OpenAI model
                if self.use_openai and requested_llm_model in self.available_models:
                    self.llm_model = requested_llm_model
                # Check if it's a Gemini model
                elif self.use_gemini and requested_llm_model in self.gemini_models:
                    self.llm_model = requested_llm_model
                # For local models or when APIs are not available
                elif not self.use_openai and not self.use_gemini:
                    self.llm_model = requested_llm_model

            # -------------- STANDARD CHAT -----------------
            if mode == "chat":
                sid = pld.get("session_id", "default")
                if sid not in self.chat_sessions:
                    self.create_chat_session(sid, pld.get("system_message", ""))
                self.add_message_to_chat(sid, pld.get("message", ""), role="user")
                resp = self.run_chat_inference(sid)
                return True, OnDataResult(output={"reply": resp})

            # -------------- RAG-ENHANCED CHAT (GraphRAG+Weaviate) -----------------
            if mode == "rag-chat":
                sid = pld.get("session_id", "default")
                if sid not in self.chat_sessions:
                    self.create_chat_session(sid, pld.get("system_message", ""))
                query = pld.get("message", "")
                q_emb = self.get_embeddings([query])
                print(f"Query is : {query}")
                # Get passages with full metadata for proper references
                passages = get_graphrag_passages_from_weaviate(
                    self.client, self.node_class, self.edge_class, q_emb, 
                    self.topk, self.similarity_threshold, self.edge_limit, debug=self.debug
                )
                # --- RERANKING STEP ---
                passages = rerank_passages(self.reranker, query, passages, top_n=self.reranking_topk)
                # Apply reordering if we have chunk information
                if any("chunk_id" in p and p["chunk_id"] is not None for p in passages):
                    passages = self.reorder_passages_by_sequence(passages)
                
                # Extract text for context
                context_texts = [p["text"] for p in passages]
                context_str = "\n\n".join(f"[{i+1}] {t}" for i, t in enumerate(context_texts))
                
                # Format references using metadata
                references = format_references(passages)
                references_str = "\n".join(references)
                
                # Enhanced system message with references
                enhanced_system_message = f"""Answer the question based only on the provided context passages.
When citing information, use numbered citations like [1], [2], etc. that correspond to the passage numbers in the context.

The passages are arranged to preserve document flow. Multiple passages from the same document are related and may contain sequential content, so consider how information connects between passages.
You are a specialized assistant for answering questions based on provided context. Your primary directive is to adhere strictly to the following rules:\n\n1.  **Context is King:** You must base your answers exclusively on the information present in the provided context chunks. Do not use any prior knowledge or external information.\n\n2.  **Cite Your Sources Precisely:** For every piece of information, data point, or decision step you take, you must cite its source. The citation must include **both the name of the source** (e.g., `pod_metrics`) **and the chunk number** it came from in brackets (e.g., `[4]`).\n    * **Correct Format Example:** `The required vCPU is 2.0 (from pod_metrics [3]).`\n    * **Correct Format Example:** `Cameras must be grouped by use case (as per Set Creation Rules [2]).`\n\n3.  **No Assumptions:** If the context does not provide the necessary information to answer a question, state that the information is not available. Never ask the user to estimate or provide missing details.\n\n4.  **Topic-Specific Logic:**\n    * **For AppLayout Creation:** When a question is about creating an `AppLayout`, you must ignore any context or information related to `ScaleLayout`.\n    * **For Deployment Planning:** When a question is about deployment planning, you must follow this exact five-step process, providing precise citations (source name and chunk number) for each step:\n        1.  **Determine FPS:** Identify the minimum common FPS for each camera, referencing the **camera vs usecase matrix [X]**.\n        2.  **Create Sets:** Group the cameras into sets, explaining the grouping based on the **'Set Creation Rules' [X]**.\n        3.  **Calculate System Resources:** Sum the required vCPU/CPU and RAM for each set for Gstremer pipeline as well as pods/blocks of ScaleLayout, explicitly stating that the data comes from **`pod_metrics` [X]**.\n        4.  **Calculate GPU Resources:** Sum the required GPU RAM for each set including Gstreamer Pipeline as well as pods/blocks of ScaleLayout, citing the **`pod_gpumemory_and_gpuutility` [X]** data. For optimizing the Hardware resource always see if you need to iterate, explain why based on the resource constraints.\n        5.  **Assign to Nodes:** Assign the finalized sets to the appropriate nodes or GPUs, ensuring you follow and reference the **resource limits and assignment rules [X]**.,
At the end of your answer, include a "References" section that lists the sources you cited.
Use multiple data points for better accuracy.Dont assume `trackerlite` is same as `trackerlitefast_960x540`.

Context passages:
{context_str}

Available References:
{references_str}"""
                
                # Log context and references if debug is enabled
                #if self.debug:
                logger.info(f"===== RAG-CHAT CONTEXT =====")
                logger.info(f"Query: {query}")
                logger.info(f"Retrieved {len(passages)} passages")
                logger.info(f"References:\n{references_str}")
                logger.info("============================")
                #exit(0)
                #return True, OnDataResult(output={"reply": "Please wait, processing your request..."})
                self.add_message_to_chat(sid, enhanced_system_message, role="system")
                self.add_message_to_chat(sid, query, role="user")
                resp = self.run_chat_inference(sid)
                
                # Add references if not already included
                if self.auto_references:
                    resp = add_references_to_response(resp, references)
                
                # Include debug information in the result if debug is enabled
                if self.debug:
                    return True, OnDataResult(output={
                        "reply": resp,
                        "debug_info": {
                            "context": context_texts,
                            "references": references,
                            "query": query,
                            "passages_metadata": passages
                        }
                    })
                else:
                    return True, OnDataResult(output={"reply": resp})

            # ------------ GENERATE ---------------
            if mode == "generate":
                prompt = pld.get("prompt", "")
                gen_kwargs = pld.get("generation_kwargs", {})
                
                # Determine which model to use based on llm_model setting
                if self.use_openai and ("gpt" in self.llm_model.lower() or self.llm_model in self.available_models):
                    messages = [{"role": "user", "content": prompt}]
                    txt = self.openai_client.generate_chat_completion(
                        self.llm_model, messages, **{**self.generation_config, **gen_kwargs}
                    )
                elif self.use_gemini and ("gemini" in self.llm_model.lower() or self.llm_model in self.gemini_models):
                    messages = [{"role": "user", "content": prompt}]
                    txt = self.gemini_client.generate_chat_completion(
                        self.llm_model, messages, **{**self.generation_config, **gen_kwargs}
                    )
                else:
                    txt = self.utils.generate(prompt, **gen_kwargs)
                    
                return True, OnDataResult(output={"generated": txt})

            # ------------- TOKENS ----------------
            if mode == "tokens":
                prompt = pld.get("prompt", "")
                gen_kwargs = pld.get("generation_kwargs", {})
                
                if self.use_openai:
                    # OpenAI API doesn't directly return tokens, so we'll log a warning
                    logger.warning("Token mode is not supported with OpenAI API, returning text instead")
                    messages = [{"role": "user", "content": prompt}]
                    txt = self.openai_client.generate_chat_completion(
                        self.llm_model, messages, **{**self.generation_config, **gen_kwargs}
                    )
                    return True, OnDataResult(output={"text": txt, "tokens": []})
                else:
                    ids = self.utils.generate_tokens(prompt, **gen_kwargs).tolist()[0]
                    return True, OnDataResult(output={"tokens": ids})

            # ---------------- EMBED ----------------
            if mode == "embed":
                text = pld.get("text", "")
                embeds = self.get_embeddings([text])
                return True, OnDataResult(output={"embedding": embeds[0]})

            # ------------- RAG QA (default mode, GraphRAG+Weaviate) -----------------
            query = pld.get("query", pld)
            if isinstance(query, dict):
                query = query.get("text", str(query))
            q_emb = self.get_embeddings([query])
            # Get passages with full metadata for proper references
            passages = get_graphrag_passages_from_weaviate(
                self.client, self.node_class, self.edge_class, q_emb, 
                self.topk, self.similarity_threshold, self.edge_limit, debug=self.debug
            )
            # --- RERANKING STEP ---
            passages = rerank_passages(self.reranker, query, passages, top_n=self.reranking_topk)
            # Extract text for context
            context_texts = [p["text"] for p in passages]
            context_str = "\n\n".join(f"[{i+1}] {t}" for i, t in enumerate(context_texts))
            
            # Format references using metadata
            references = format_references(passages)
            references_str = "\n".join(references)
            
            # Log context and references if debug is enabled
            if self.debug:
                logger.info(f"===== RAG QA CONTEXT =====")
                logger.info(f"Query: {query}")
                logger.info(f"Retrieved {len(passages)} passages")
                logger.info(f"References:\n{references_str}")
                logger.info("=========================")
            
            # Determine which model to use based on llm_model setting
            if self.use_openai and ("gpt" in self.llm_model.lower() or self.llm_model in self.available_models):
                # Enhanced system message with references
                system_message = f"""Answer the question based only on the provided context passages.
When citing information, use numbered citations like [1], [2], etc. that correspond to the passage numbers in the context.

At the end of your answer, include a "References" section that lists the sources you cited.

Context passages:
{context_str}

Available References:
{references_str}"""

                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Question: {query}"}
                ]
                
                answer = self.openai_client.generate_chat_completion(
                    self.llm_model, messages, **self.generation_config
                )
                
                # Add references if not already included
                if self.auto_references:
                    answer = add_references_to_response(answer, references)
            elif self.use_gemini and ("gemini" in self.llm_model.lower() or self.llm_model in self.gemini_models):
                # Enhanced system message with references for Gemini
                system_message = f"""Answer the question based only on the provided context passages.
When citing information, use numbered citations like [1], [2], etc. that correspond to the passage numbers in the context.

At the end of your answer, include a "References" section that lists the sources you cited.

Context passages:
{context_str}

Available References:
{references_str}"""

                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Question: {query}"}
                ]
                
                answer = self.gemini_client.generate_chat_completion(
                    self.llm_model, messages, **self.generation_config
                )
                
                # Add references if not already included
                if self.auto_references:
                    answer = add_references_to_response(answer, references)
            else:
                # For local models, include references in the prompt
                prompt = (
                    "### Context passages:\n"
                    f"{context_str}\n\n"
                    "### Available References:\n"
                    f"{references_str}\n\n"
                    "### Question:\n"
                    f"{query}\n\n"
                    "### Instructions:\n"
                    "Answer the question based only on the provided context passages. "
                    "When citing information, use numbered citations like [1], [2], etc. "
                    "At the end of your answer, include a References section.\n\n"
                    "### Answer:"
                )
                answer = self.utils.generate(prompt)
                
                # Add references if not already included
                if self.auto_references:
                    answer = add_references_to_response(answer, references)
            
            # Include debug information in the result if debug is enabled
            if self.debug:
                return True, OnDataResult(output={
                    "answer": answer,
                    "debug_info": {
                        "context": context_texts,
                        "references": references,
                        "query": query,
                        "passages_metadata": passages
                    }
                })
            else:
                return True, OnDataResult(output={"answer": answer})

        except Exception as e:
            logger.error(f"[RAG QA Error] {e}", exc_info=True)
            return False, str(e)

    def on_update(self, params):
        # Allow dynamic model switching via update
        if "embed_model" in params:
            if self.use_openai_embeddings and "text-embedding" in params["embed_model"]:
                self.embedding_model = params["embed_model"]
            else:
                self.embedder.switch_model(params["embed_model"])
        if "llm_model" in params and ((self.use_openai and params["llm_model"] in self.available_models) or not self.use_openai):
            self.llm_model = params["llm_model"]
        if "topk" in params:
            self.topk = int(params["topk"])
        if "edge_limit" in params:
            self.edge_limit = int(params["edge_limit"])
        if "generation_config" in params:
            self.generation_config.update(params["generation_config"])
        if "debug" in params:
            self.debug = bool(params["debug"])
            if hasattr(self, 'openai_client'):
                self.openai_client.debug = self.debug
        if "auto_references" in params:
            self.auto_references = bool(params["auto_references"])
        return True, params

    def health(self):
        try:
            # Check if Weaviate is healthy
            nodes = self.client.data_object.get(class_name=self.node_class, limit=1)
            weaviate_exists = len(nodes.get('objects', [])) > 0
            
            # Check if OpenAI API is accessible
            openai_healthy = self.use_openai and len(self.available_models) > 0
            
            # Check if Gemini API is accessible
            gemini_healthy = self.use_gemini and len(self.gemini_models) > 0
            
            return {
                "status": "healthy" if weaviate_exists else "unhealthy", 
                "graph_exists": weaviate_exists,
                "openai_api": "healthy" if openai_healthy else "unavailable",
                "gemini_api": "healthy" if gemini_healthy else "unavailable",
                "using_openai": self.use_openai,
                "using_gemini": self.use_gemini,
                "using_openai_embeddings": self.use_openai_embeddings,
                "debug": self.debug,
                "auto_references": self.auto_references,
                "current_llm": self.llm_model,
                "topk": self.topk,
                "edge_limit": self.edge_limit,
                "current_user": "srikanthcognitifAI",
                "timestamp": "2025-06-17 12:47:37"
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def management(self, action, data):
        if action == "reload_model":
            changes = {}
            
            embed_model = data.get("embed_model")
            if embed_model:
                if self.use_openai_embeddings and "text-embedding" in embed_model:
                    self.embedding_model = embed_model
                else:
                    self.embedder.switch_model(embed_model)
                changes["embed_model"] = embed_model
                
            llm_model = data.get("llm_model")
            if llm_model:
                if self.use_openai and llm_model in self.available_models:
                    self.llm_model = llm_model
                    changes["llm_model"] = llm_model
                elif self.use_gemini and llm_model in self.gemini_models:
                    self.llm_model = llm_model
                    changes["llm_model"] = llm_model
                elif not self.use_openai and not self.use_gemini:
                    # For local model switching
                    logger.warning("Switching local models not implemented")
                
            if changes:
                return {"message": f"Models updated: {changes}"}
            return {"message": "No valid models specified for update"}
            
        if action == "reset":
            self.chat_sessions.clear()
            if not self.use_openai:
                self.utils.chat_sessions.clear()
            return {"message": "Chat sessions cleared"}
            
        if action == "list_models":
            # Refresh the list of available models if using OpenAI
            if self.use_openai:
                try:
                    self.available_models = self.openai_client.get_models()
                except Exception as e:
                    logger.error(f"Failed to refresh OpenAI models: {e}")
                    
            return {
                "openai_models": self.available_models, 
                "gemini_models": self.gemini_models,
                "current_llm": self.llm_model, 
                "current_embed": self.embedding_model if self.use_openai_embeddings else self.embed_model,
                "using_openai": self.use_openai,
                "using_gemini": self.use_gemini,
                "using_openai_embeddings": self.use_openai_embeddings
            }
            
        if action == "toggle_embed_source":
            # Toggle between OpenAI and local embeddings
            if self.use_openai:
                self.use_openai_embeddings = not self.use_openai_embeddings
                source = "OpenAI" if self.use_openai_embeddings else "local"
                return {"message": f"Embedding source changed to {source}"}
            return {"message": "OpenAI not available, using local embeddings"}
            
        if action == "toggle_debug":
            # Toggle debug mode
            self.debug = not self.debug
            if hasattr(self, 'openai_client'):
                self.openai_client.debug = self.debug
            return {"message": f"Debug mode {'enabled' if self.debug else 'disabled'}"}
            
        if action == "toggle_references":
            # Toggle auto references
            self.auto_references = not self.auto_references
            return {"message": f"Auto references {'enabled' if self.auto_references else 'disabled'}"}
            
        if action == "set_limits":
            # Set topk and edge limits dynamically
            changes = {}
            if "topk" in data:
                self.topk = int(data["topk"])
                changes["topk"] = self.topk
            if "edge_limit" in data:
                self.edge_limit = int(data["edge_limit"])
                changes["edge_limit"] = self.edge_limit
            
            if changes:
                return {"message": f"Limits updated: {changes}"}
            return {"message": "No valid limits specified"}
            
        return {"message": f"Unknown action: {action}"}

    def get_muxer(self):
        return None

if __name__ == "__main__":
    Block(RagQAServiceBlock).run()