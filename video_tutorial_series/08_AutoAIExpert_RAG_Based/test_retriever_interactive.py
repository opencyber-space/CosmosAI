#!/usr/bin/env python3
"""
Interactive Chat Interface for Computer Vision Pipeline Knowledge Base
Enables conversational queries about use case composition and parameter optimization
"""

import os
import json
import sys
import time
from datetime import datetime
from block_retriever import RagQAServiceBlock
from aios_instance import TestContext, BlockTester

class CVPipelineChatInterface:
    """Interactive chat interface for CV pipeline knowledge base"""
    
    def __init__(self):
        self.session_id = f"cv_pipeline_chat_{int(time.time())}"
        self.setup_retriever()
        self.conversation_history = []
        
    def setup_retriever(self):
        """Setup the RAG retriever with CV pipeline knowledge"""
        context = TestContext()
        modelType = "gemini"
        llm_model = None
        if modelType == "gemini":
            llm_model = 'gemini-2.5-pro' #'gemini-2.5-flash' #'gemini-2.5-pro' #"gemini-2.5-pro-001" #"gemini-2.5-pro-latest"
        elif modelType == "openai":
            llm_model = 'gpt-4.1-mini-2025-04-14' #"gpt-4.1-nano", #'gpt-4o-mini-2024-07-18', #"gpt-3.5-turbo", #'gpt-4.1-mini', #"gpt-4", #"gpt-3.5-turbo", #'gpt-4', #"gpt-4.1-nano", #"gpt-3.5-turbo",  # Will fallback to local if OpenAI not available
        
        generation_kwargs = {}
        if modelType == "gemini":
            generation_kwargs = {
                "maxOutputTokens": 16384,  # Increased for full passage processing
                "temperature": 0.2,
                "top_p": 0.95
            }
        elif modelType == "openai":
            generation_kwargs = {
                #"max_tokens": 8192,        # Longer for complete architectures
                "max_tokens": 16384,        # Longer for complete architectures
                "temperature": 0.25,       # Slightly more creative
                "top_p": 0.95,
                "frequency_penalty": 0.1,  # Reduce repetition
                "presence_penalty": 0.05   # Encourage new concepts
            }
        
        context.block_init_data = {
            "weaviate_url": "http://localhost:8080",
            "node_class": "PassageNode", 
            "edge_class": "PassageEdge",
            "llm_model": llm_model,
            #"embed_model": "sentence-transformers/all-MiniLM-L6-v2",
            "embed_model": "openai/text-embedding-3-large",
        }
        #if emdedding model sentance transfomer then dimension is 384 by default
        # this is for openai embedding model
        EMBEDDING_DIM = 1024
        RERANKING_MODEL = "cross-encoder/ms-marco-MiniLM-L-12-v2"  # For reranking
        #RERANKING_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # For reranking


        # Prepare output paths
        OUTPUT_DIR = "tests/output"
        PASSAGES_JSON = os.path.join(OUTPUT_DIR, "psgs_w100.jsonl")
        INDEX_PATH    = os.path.join(OUTPUT_DIR, "psgs_w100.index")
        context.block_init_parameters = {
            "topk": 200,
            "reranking_topk": 30,
            "max_length": EMBEDDING_DIM, #4096,
            "edge_limit": 50,
            "debug": False,
            "passages_json": PASSAGES_JSON,
            "similarity_threshold": 0.45,
            "auto_references": True,
            "generation_config": generation_kwargs,
            "reranking_model": RERANKING_MODEL
        }
        
        # Initialize the block
        self.tester = BlockTester.init_with_context(RagQAServiceBlock, context)
        
        # Initialize with minimal, unbiased system message
        # Let the LLM respond purely based on RAG data without predefined constraints
        # self.tester.run({
        #     "mode": "chat",
        #     "session_id": self.session_id,
        #     #"system_message": "You are a helpful assistant. Answer questions based on the provided context. You must read and reason over all provided context chunks. Do not answer unless you have checked the relevant information in the context. Never ask user to estimate anything. If it is about AppLayout creation then dont check about scalelayout. If it is about Deployment planning, then understand the Complete process walkthrough Step by Step present in Scalelayout guides for Deployment Planning(Given the camera vs usecase matrix, Step1:use the minimum common FPS per camera, Step2:create sets per Set Creation rules, Step3:sum vCPU/CPU RAM from pod_metrics, Step4:sum GPU RAM from pod_gpumemory_and_gpuutility,if needed iterate again from Step2 so that best set can be get, and Step5:assign sets to nodes/GPUs ensuring all resource limits and assignment rules are followed.)",
        #     #"system_message": "You are a specialized assistant for answering questions based on provided context. Your primary directive is to adhere strictly to the following rules:\n\n1.  **Context is King:** You must base your answers exclusively on the information present in the provided context chunks. Do not use any prior knowledge or external information.\n2.  **No Assumptions:** If the context does not provide the necessary information to answer a question, state that the information is not available. Never ask the user to estimate or provide missing details.\n3.  **Topic-Specific Logic:**\n    * **For AppLayout Creation:** When a question is about creating an `AppLayout`, you must ignore any context or information related to `ScaleLayout`.\n    * **For Deployment Planning:** When a question is about deployment planning, you must follow this exact five-step process using the provided context:\n        1.  **Determine FPS:** Identify the minimum common Frames Per Second (FPS) for each camera from the camera vs. use case matrix.\n        2.  **Create Sets:** Group the cameras into sets based on the 'Set Creation Rules' provided.\n        3.  **Calculate System Resources:** Sum the required vCPU/CPU and RAM for each set using the `pod_metrics` data.\n        4.  **Calculate GPU Resources:** Sum the required GPU RAM for each set using the `pod_gpumemory_and_gpuutility` data. If the initial sets are not optimal, you may need to iterate and re-run from Step 2 to find a better configuration.\n        5.  **Assign to Nodes:** Assign the finalized sets to the appropriate nodes or GPUs, ensuring that all resource limits and assignment rules are strictly followed.",
        #     "system_message": "You are a specialized assistant for answering questions based on provided context. Your primary directive is to adhere strictly to the following rules:\n\n1.  **Context is King:** You must base your answers exclusively on the information present in the provided context chunks. Do not use any prior knowledge or external information.\n\n2.  **Cite Your Sources Precisely:** For every piece of information, data point, or decision step you take, you must cite its source. The citation must include **both the name of the source** (e.g., `pod_metrics`) **and the chunk number** it came from in brackets (e.g., `[4]`).\n    * **Correct Format Example:** `The required vCPU is 2.0 (from pod_metrics [3]).`\n    * **Correct Format Example:** `Cameras must be grouped by use case (as per Set Creation Rules [2]).`\n\n3.  **No Assumptions:** If the context does not provide the necessary information to answer a question, state that the information is not available. Never ask the user to estimate or provide missing details.\n\n4.  **Topic-Specific Logic:**\n    * **For AppLayout Creation:** When a question is about creating an `AppLayout`, you must ignore any context or information related to `ScaleLayout`.\n    * **For Deployment Planning:** When a question is about deployment planning, you must follow this exact five-step process, providing precise citations (source name and chunk number) for each step:\n        1.  **Determine FPS:** Identify the minimum common FPS for each camera, referencing the **camera vs usecase matrix [X]**.\n        2.  **Create Sets:** Group the cameras into sets, explaining the grouping based on the **'Set Creation Rules' [X]**.\n        3.  **Calculate System Resources:** Sum the required vCPU/CPU and RAM for each set, explicitly stating that the data comes from **`pod_metrics` [X]**.\n        4.  **Calculate GPU Resources:** Sum the required GPU RAM for each set, citing the **`pod_gpumemory_and_gpuutility` [X]** data. For optimizing the Hardware resource always see if you need to iterate, explain why based on the resource constraints.\n        5.  **Assign to Nodes:** Assign the finalized sets to the appropriate nodes or GPUs, ensuring you follow and reference the **resource limits and assignment rules [X]**.",
        #     "message": "Hello! I'm ready to help with your questions."
        # })
        
    def display_welcome(self):
        """Display welcome message and usage instructions"""
        print("=" * 80)
        print("🔍 RAG-Powered Computer Vision Assistant")
        print("=" * 80)
        print()
        print("This assistant queries a knowledge base containing:")
        print("• 🔧 Use case composition and parameter recommendations")
        print("• ⚙️  Computer vision pipeline configurations")
        print("• 🏗️  Environmental optimization guidelines")
        print("• 💡 Hardware-specific settings")
        print()
        print("The assistant responds based purely on retrieved information")
        print("without predefined biases, letting the knowledge base guide the answers.")
        print()
        print("Example questions:")
        print("• 'How do I configure loitering detection for an ATM?'")
        print("• 'What parameters should I adjust for low light conditions?'")
        print("• 'How do I reduce false positives in crowded areas?'")
        print("• 'What's the difference between indoor and outdoor parameter settings?'")
        print()
        print("Commands:")
        print("• 'help' - Show this help message")
        print("• 'history' - Show conversation history")
        print("• 'clear' - Clear conversation history")
        print("• 'quit' or 'exit' - Exit the chat")
        print()
        print("=" * 80)
    
    def save_conversation(self, query, response):
        """Save conversation to history"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.conversation_history.append({
            "timestamp": timestamp,
            "query": query,
            "response": response
        })
    
    def show_history(self):
        """Display conversation history"""
        if not self.conversation_history:
            print("No conversation history yet.")
            return
            
        print("\n" + "=" * 60)
        print("📝 Conversation History")
        print("=" * 60)
        
        for i, entry in enumerate(self.conversation_history, 1):
            print(f"\n[{i}] {entry['timestamp']}")
            print(f"Q: {entry['query']}")
            print(f"A: {entry['response'][:200]}{'...' if len(entry['response']) > 200 else ''}")
        print("=" * 60)
    
    def clear_history(self):
        """Clear conversation history and start fresh"""
        self.conversation_history = []
        
        # Clear the RAG block's chat session using its management interface
        try:
            self.tester.run({
                "mode": "management",
                "action": "reset"
            })
        except Exception as e:
            print(f"Warning: Could not clear chat session: {e}")
        
        # Create new session
        self.session_id = f"cv_pipeline_chat_{int(time.time())}"
        self.tester.run({
            "mode": "chat",
            "session_id": self.session_id,
            #"system_message": "You are a helpful assistant. Answer questions based on the provided context. You must read and reason over all provided context chunks. Do not answer unless you have checked the relevant information in the context. If it is about AppLayout creation dont check about scalelayout. If it is about Deployment planning, then understand the Complete process walkthrough Step by Step present in Scalelayout guides for Deployment Planning(Given the camera vs usecase matrix, use the minimum common FPS per camera, create sets per Set Creation rules, sum vCPU/CPU RAM from pod_metrics, sum GPU RAM from pod_gpumemory_and_gpuutility, and assign sets to nodes/GPUs ensuring all resource limits and assignment rules are followed.)",
            #"system_message" : "You are a specialized assistant for answering questions based on provided context. Your primary directive is to adhere strictly to the following rules:\n\n1.  **Context is King:** You must base your answers exclusively on the information present in the provided context chunks. Do not use any prior knowledge or external information.\n2.  **No Assumptions:** If the context does not provide the necessary information to answer a question, state that the information is not available. Never ask the user to estimate or provide missing details.\n3.  **Topic-Specific Logic:**\n    * **For AppLayout Creation:** When a question is about creating an `AppLayout`, you must ignore any context or information related to `ScaleLayout`.\n    * **For Deployment Planning:** When a question is about deployment planning, you must follow this exact five-step process using the provided context:\n        1.  **Determine FPS:** Identify the minimum common Frames Per Second (FPS) for each camera from the camera vs. use case matrix.\n        2.  **Create Sets:** Group the cameras into sets based on the 'Set Creation Rules' provided.\n        3.  **Calculate System Resources:** Sum the required vCPU/CPU and RAM for each set using the `pod_metrics` data.\n        4.  **Calculate GPU Resources:** Sum the required GPU RAM for each set using the `pod_gpumemory_and_gpuutility` data. If the initial sets are not optimal, you may need to iterate and re-run from Step 2 to find a better configuration.\n        5.  **Assign to Nodes:** Assign the finalized sets to the appropriate nodes or GPUs, ensuring that all resource limits and assignment rules are strictly followed.",
            "system_message": "You are a specialized assistant for answering questions based on provided context. Your primary directive is to adhere strictly to the following rules:\n\n1.  **Context is King:** You must base your answers exclusively on the information present in the provided context chunks. Do not use any prior knowledge or external information.\n\n2.  **Cite Your Sources Precisely:** For every piece of information, data point, or decision step you take, you must cite its source. The citation must include **both the name of the source** (e.g., `pod_metrics`) **and the chunk number** it came from in brackets (e.g., `[4]`).\n    * **Correct Format Example:** `The required vCPU is 2.0 (from pod_metrics [3]).`\n    * **Correct Format Example:** `Cameras must be grouped by use case (as per Set Creation Rules [2]).`\n\n3.  **No Assumptions:** If the context does not provide the necessary information to answer a question, state that the information is not available. Never ask the user to estimate or provide missing details.\n\n4.  **Topic-Specific Logic:**\n    * **For AppLayout Creation:** When a question is about creating an `AppLayout`, you must ignore any context or information related to `ScaleLayout`.\n    * **For Deployment Planning:** When a question is about deployment planning, you must follow this exact five-step process, providing precise citations (source name and chunk number) for each step:\n        1.  **Determine FPS:** Identify the minimum common FPS for each camera, referencing the **camera vs usecase matrix [X]**.\n        2.  **Create Sets:** Group the cameras into sets, explaining the grouping based on the **'Set Creation Rules' [X]**.\n        3.  **Calculate System Resources:** Sum the required vCPU/CPU and RAM for each set, explicitly stating that the data comes from **`pod_metrics` [X]**.\n        4.  **Calculate GPU Resources:** Sum the required GPU RAM for each set, citing the **`pod_gpumemory_and_gpuutility` [X]** data. For optimizing the Hardware resource always see if you need to iterate, explain why based on the resource constraints.\n        5.  **Assign to Nodes:** Assign the finalized sets to the appropriate nodes or GPUs, ensuring you follow and reference the **resource limits and assignment rules [X]**.",
            "message": "Hello! Starting a fresh session."
        })
        print("✅ Conversation history and chat session cleared.")
        
    def process_query(self, query):
        """Process user query and return response"""
        try:
            # Use RAG-enhanced chat for technical questions
            result = self.tester.run({
                "mode": "rag-chat",
                "session_id": self.session_id,
                "message": query
            })
            
            if result and len(result) > 0:
                response = result[0].get("reply", "Sorry, I couldn't generate a response.")
            else:
                response = "Sorry, I couldn't process your query. Please try rephrasing."
                
            return response
            
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    def run_interactive_session(self):
        """Run the main interactive chat loop"""
        self.display_welcome()
        
        print("💬 Chat started! Type your question or 'help' for assistance.\n")
        
        while True:
            try:
                # Get user input
                query = input("🎯 You: ").strip()
                
                if not query:
                    continue
                    
                # Handle special commands
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye! Thanks for using CV Pipeline Assistant.")
                    break
                    
                elif query.lower() == 'help':
                    self.display_welcome()
                    continue
                    
                elif query.lower() == 'history':
                    self.show_history()
                    continue
                    
                elif query.lower() == 'clear':
                    self.clear_history()
                    continue
                    
                # Process the query
                print("🤔 Processing your question...")
                response = self.process_query(query)
                
                # Display response
                print(f"\n🤖 Assistant: {response}\n")
                print("-" * 80)
                
                # Save to history
                self.save_conversation(query, response)
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("Please try again or type 'quit' to exit.\n")

def main():
    """Main function to run the chat interface"""
    try:
        chat = CVPipelineChatInterface()
        chat.run_interactive_session()
    except Exception as e:
        print(f"❌ Failed to initialize chat interface: {str(e)}")
        print("\nPlease ensure:")
        print("• Weaviate is running on http://localhost:8080")
        print("• Knowledge base has been indexed")
        print("• Required dependencies are installed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
