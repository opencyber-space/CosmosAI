from block_indexer import IndexDocumentsBlock
#from block_indexer_notopk import IndexDocumentsBlock
from aios_instance import TestContext, BlockTester
import os
import shutil

# --- Setup test environment ---

# Clean and recreate a small test PDF directory (you can substitute real PDFs here)
#TEST_PDF_DIR = "tests/repo"
TEST_PDF_DIR = "knowledge_base"
os.makedirs(TEST_PDF_DIR, exist_ok=True)
# Optionally copy or generate a dummy PDF into TEST_PDF_DIR
# shutil.copy("some_small.pdf", os.path.join(TEST_PDF_DIR, "sample.pdf"))
# Prepare output paths
OUTPUT_DIR = "tests/output"
PASSAGES_JSON = os.path.join(OUTPUT_DIR, "psgs_w100.jsonl")
INDEX_PATH    = os.path.join(OUTPUT_DIR, "psgs_w100.index")
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

#if emdedding model sentance transfomer then dimension is 384 by default
# this is for openai embedding model
EMBEDDING_DIM = 1024  # Increased for full passage processing

# Create TestContext and configure the block
context = TestContext()
context.block_init_data = {
    "repo_dir": TEST_PDF_DIR,
    "passages_json": PASSAGES_JSON,
    "index_path": INDEX_PATH,
    # optional: "device": "cpu",
    # optional: "dpr_model": "facebook/dpr-ctx_encoder-single-nq-base"
    #"embed_model": "sentence-transformers/all-MiniLM-L6-v2",
    # "embed_model": "openai/text-embedding-ada-002",
    # "embed_model": "openai/text-embedding-3-small",
    "embed_model": "openai/text-embedding-3-large",
    "client_type": "weaviate",
    "client_config": {
        "uri": "http://localhost:8080",
        "user": "coguser1",                 # Add the username
        "password": "sdf345BJw44HMy",    # Add the password
        "dim": EMBEDDING_DIM
    }
    # "client_type": "milvus",
    # "client_config": {
    #     "uri": "http://localhost:9091",  # Default Milvus URL for HTTP
    #     "user": "user1",                 # Add the username
    #     "password": "da^&wrerkjb673",    # Add the password
    #     "collection_name": "test_app_collection",  # Name for your collection
    #     "dim": EMBEDDING_DIM,                      # The dimension of your embeddings
    #     "overwrite": True,               # Overwrite collection if it already exists
    # }
}
context.block_init_parameters = {
    # Text Processing Parameters
    "chunk_size": 200,              # Increased from 50 for better context
    "chunk_overlap": 50,            # Added: overlap between chunks for continuity
    "max_length": EMBEDDING_DIM,             # Increased from 128 for full passage processing
    "similarity_threshold": 0.4,    # Lower threshold for more connections in graph
    # Additional Parameters
    "include_filename_prefix": True  # Added: preserve source information in chunks
}

# Initialize the tester
tester = BlockTester.init_with_context(IndexDocumentsBlock, context)
tester.block_instance.management("reset",{})
# Run the indexing block
results = tester.run({})   # on_data will perform the index build
print("Indexer output:", results)

# Verify files were created
print("Passages JSON exists?", os.path.exists(PASSAGES_JSON))
print("FAISS index exists?   ", os.path.exists(INDEX_PATH))