"""
MCP Vision Pipeline Client for Jupyter Notebooks

This module provides a simplified interface to execute the MCP vision pipeline 
from Jupyter notebooks and return the final response that can be parsed by 
mcp_response_final_parser.py
"""

import json
import pathlib
import traceback
from typing import Dict, List, Any, Optional

# Handle OpenAI imports with error handling for version compatibility
try:
    import backoff
    from openai import OpenAI, APIError, RateLimitError
    from openai._exceptions import APITimeoutError, APIConnectionError
    OPENAI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  OpenAI SDK import issue: {e}")
    print("   Trying alternative import approach...")
    try:
        # Try importing without backoff first
        from openai import OpenAI
        # Create simple retry classes if backoff not available
        class APIError(Exception):
            pass
        class RateLimitError(Exception):
            pass
        class APITimeoutError(Exception):
            pass
        class APIConnectionError(Exception):
            pass
        OPENAI_AVAILABLE = True
        backoff = None
    except ImportError as e2:
        print(f"❌ Could not import OpenAI SDK: {e2}")
        OPENAI_AVAILABLE = False
        OpenAI = None
        backoff = None

class MCPVisionPipelineClient:
    """MCP Vision Pipeline Client for Jupyter Notebooks"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK is not available. Please install with: pip install openai")
        
        self.client = OpenAI()
        self.model = model
        self.tools = []
        self.seen_servers = set()
        
    def reset_state(self, registry_url: str):
        """Reset the client state for a new execution"""
        self.tools = [{
            "type": "mcp",
            "server_label": "ror",
            "server_url": registry_url,
            "require_approval": "never"
        }]
        self.seen_servers = {registry_url}
        
    def run_conversation_with_retry(self, messages, tools, max_retries=3):
        """Run a conversation with simple retry logic"""
        for attempt in range(max_retries):
            try:
                return self.client.responses.create(
                    model=self.model, 
                    input=messages, 
                    tools=tools,
                    stream=True, 
                    timeout=150
                )
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"⚠️  Attempt {attempt + 1} failed, retrying...")
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
        
    def run_conversation(self, messages, tools):
        """Run a conversation with the model"""
        if backoff:
            # Use backoff decorator if available
            @backoff.on_exception(backoff.expo, (Exception,), max_tries=4)
            def _run_with_backoff():
                return self.client.responses.create(
                    model=self.model, 
                    input=messages, 
                    tools=tools,
                    stream=True, 
                    timeout=150
                )
            return _run_with_backoff()
        else:
            # Use simple retry logic
            return self.run_conversation_with_retry(messages, tools)
        
    def extract_and_register_servers_from_output(self, output_data, server_label):
        """Helper function to extract and register server URLs from response data"""
        added_servers = False
        
        if not isinstance(output_data, dict):
            try:
                output_data = json.loads(output_data)
            except (json.JSONDecodeError, TypeError):
                return False
        
        # Check for servers list (from registryServers)
        if "servers" in output_data:
            for srv in output_data.get("servers", []):
                url = srv.get("server_url")
                srv_id = srv.get("id")
                if url and url not in self.seen_servers:
                    self.tools.append({
                        "type": "mcp",
                        "server_label": srv_id,
                        "server_url": url,
                        "require_approval": "never"
                    })
                    self.seen_servers.add(url)
                    added_servers = True
        
        # Check for model_url in response
        model_url = output_data.get("model_url")
        model_id = output_data.get("id", f"{server_label}-models")
        
        if model_url and model_url not in self.seen_servers:
            self.tools.append({
                "type": "mcp",
                "server_label": model_id,
                "server_url": model_url,
                "require_approval": "never"
            })
            self.seen_servers.add(model_url)
            added_servers = True
                
        return added_servers
        
    def execute_pipeline(self, image_path: str, registry_url: str = "http://localhost:8000/mcp", 
                        max_rounds: int = 5, verbose: bool = False) -> Dict[str, Any]:
        """
        Execute the MCP vision pipeline and return the final response.
        
        Args:
            image_path: Path to the image file to analyze
            registry_url: Registry of Registries URL
            max_rounds: Maximum discovery rounds
            verbose: Print execution details
            
        Returns:
            dict: Contains the final response data for parsing
        """
        self.reset_state(registry_url)
        
        # Create the prompt
        IMG = pathlib.Path(image_path).absolute()
        prompt = (
            f"Here is an image file://{IMG}. "
            "Using the OpenOS registry extract vehicle attributes from this image. "
            
            "**FOLLOW THESE 3 PHASES IN ORDER:**\n"
            "\n"
            "**PHASE 1 - DISCOVERY (NO MODEL CALLS)**\n"
            "1. Discover available registries using registryList\n"
            "2. Use registryServers to get the asset registry MCP server URLs\n"
            "3. Connect to asset registry, get metadata and list available models\n"
            "4. Identify vehicle-related analysis capabilities and extract model_url\n"
            "❌ FORBIDDEN: Do not call any analysis tools before getting pipeline\n"
            "❌ FORBIDDEN: Do not register model servers yet\n"
            "\n"
            "**PHASE 2 - PIPELINE PLANNING (MANDATORY)**\n"
            "5. Connect to pipeline-composer service from registries\n"
            "6. Send relevant model names to pipeline-composer for vehicle analysis\n"
            "7. Get the execution plan with proper order\n"
            "❌ FORBIDDEN: Do not register model servers until Phase 3\n"
            "❌ FORBIDDEN: Do not call any analysis tools until Phase 3\n"
            "\n"
            "**PHASE 3 - EXECUTION (FOLLOW PIPELINE ORDER)**\n"
            "8. Register the model server from Phase 1\n"
            "9. Execute analysis tools in EXACT order from pipeline-composer\n"
            "10. Use ONLY the tools specified in the pipeline response\n"
            "\n"
            "**CRITICAL RULES:**\n"
            "- Complete each phase before moving to next\n"
            "- Never call analysis tools before getting pipeline\n"
            "- Never register model servers before Phase 3\n"
            "- Always follow pipeline execution order exactly\n"
            "\n"
            "Start with Phase 1 and continue with Phase 2 and Phase 3"
        )
        
        messages = [{"role": "user", "content": prompt}]
        discovery_round = 0
        final_response = None
        
        if verbose:
            print(f"🚀 Starting MCP Vision Pipeline with {self.model}")
            print(f"📋 Registry URL: {registry_url}")
            print(f"🖼️ Image: {image_path}")
            print()
        
        try:
            while discovery_round < max_rounds:
                discovery_round += 1
                if verbose:
                    print(f"--- Discovery Round {discovery_round} ---")
                    print(f"🔌 Active tools: {len(self.tools)}")
                
                stream = self.run_conversation(messages, self.tools)
                added = False
                
                for ev in stream:
                    if verbose and ev.type in ["response.mcp_call.in_progress", "response.mcp_call.completed"]:
                        if ev.type == "response.mcp_call.in_progress":
                            print("Calling",ev)
                            name = getattr(ev, 'name', 'unknown')
                            server_label = getattr(ev, 'server_label', 'unknown')
                            # print(f"  📞 Calling {name} on {server_label}")
                        elif ev.type == "response.mcp_call.completed":
                            print("Completed",ev)
                            name = getattr(ev, 'name', 'unknown')
                            server_label = getattr(ev, 'server_label', 'unknown')
                            # print(f"  ✅ Completed {name} on {server_label}")
                    
                    # Handle MCP call completion for server registration
                    if ev.type == "response.mcp_call.completed":
                        output = getattr(ev, 'output', {})
                        name = getattr(ev, 'name', None)
                        server_label = getattr(ev, 'server_label', 'unknown')
                        
                        # Handle server registration
                        if name == "registryServers":
                            try:
                                server_data = json.loads(output) if isinstance(output, str) else output
                                if self.extract_and_register_servers_from_output(server_data, server_label):
                                    added = True
                            except (json.JSONDecodeError, TypeError):
                                pass
                        else:
                            try:
                                response_data = json.loads(output) if isinstance(output, str) else output
                                if self.extract_and_register_servers_from_output(response_data, server_label):
                                    added = True
                            except (json.JSONDecodeError, TypeError):
                                pass
                    
                    # Capture the final response
                    elif ev.type == "response.completed":
                        final_response = ev
                        if verbose:
                            print("  🏁 Response completed")
                        
                        # Process the response to find server URLs
                        if hasattr(ev, 'response') and hasattr(ev.response, 'output'):
                            for output_item in ev.response.output:
                                if hasattr(output_item, 'type') and output_item.type == "mcp_call":
                                    call_output = getattr(output_item, 'output', None)
                                    server_label = getattr(output_item, 'server_label', "unknown")
                                    
                                    if call_output:
                                        try:
                                            output_data = json.loads(call_output) if isinstance(call_output, str) else call_output
                                            if self.extract_and_register_servers_from_output(output_data, server_label):
                                                added = True
                                        except (json.JSONDecodeError, TypeError):
                                            pass
                
                if not added:
                    if verbose:
                        print("🏁 No new endpoints discovered, execution complete.")
                    break
                else:
                    if verbose:
                        print(f"🔄 New endpoints registered, continuing...")
                    messages.append({
                        "role": "system",
                        "content": f"New endpoints have been registered in round {discovery_round}. Continue your analysis with the expanded capabilities."
                    })
            
            if final_response:
                # Convert the response to a dictionary format for parsing
                response_dict = {
                    'type': 'response.completed',
                    'response': final_response.response.model_dump() if hasattr(final_response.response, 'model_dump') else str(final_response.response)
                }
                
                return {
                    'status': 'success',
                    'final_response': response_dict,
                    'total_rounds': discovery_round,
                    'total_servers': len(self.tools)
                }
            else:
                return {
                    'status': 'error',
                    'error': 'No final response received',
                    'total_rounds': discovery_round,
                    'total_servers': len(self.tools)
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'total_rounds': discovery_round,
                'total_servers': len(self.tools)
            }

# Convenience functions for Jupyter notebook usage
def check_dependencies():
    """Check if all required dependencies are available"""
    issues = []
    
    if not OPENAI_AVAILABLE:
        issues.append("❌ OpenAI SDK not available")
        issues.append("   Fix: pip install openai")
    
    # Check for API key
    import os
    if not os.getenv('OPENAI_API_KEY'):
        issues.append("❌ OPENAI_API_KEY environment variable not set")
        issues.append("   Fix: export OPENAI_API_KEY=your_api_key")
    
    # Check Python version for compatibility
    import sys
    if sys.version_info < (3, 7):
        issues.append("❌ Python 3.7+ required")
        issues.append(f"   Current version: {sys.version}")
    
    if issues:
        print("🔍 Dependency Issues Found:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("✅ All dependencies are available")
        return True

def execute_mcp_vision_pipeline(image_path: str, 
                               registry_url: str = "http://localhost:8000/mcp",
                               model: str = "gpt-4o-mini",
                               verbose: bool = True) -> Dict[str, Any]:
    """
    Execute the MCP vision pipeline from Jupyter notebook.
    
    Args:
        image_path: Path to the image file to analyze
        registry_url: Registry of Registries URL
        model: OpenAI model to use
        verbose: Print execution progress
        
    Returns:
        Dictionary containing the final response and execution info
        
    Example:
        >>> # First check dependencies
        >>> if check_dependencies():
        ...     result = execute_mcp_vision_pipeline("/path/to/car.jpg")
        ...     # Save result for parsing
        ...     with open('final_response.txt', 'w') as f:
        ...         json.dump(result['final_response'], f, indent=2)
    """
    if not OPENAI_AVAILABLE:
        return {
            'status': 'error',
            'error': 'OpenAI SDK not available. Please install with: pip install openai'
        }
    
    try:
        client = MCPVisionPipelineClient(model=model)
        return client.execute_pipeline(image_path, registry_url, verbose=verbose)
    except Exception as e:
        return {
            'status': 'error',
            'error': f'Failed to execute pipeline: {str(e)}',
            'traceback': traceback.format_exc()
        }

def save_response_for_parsing(result: Dict[str, Any], output_file: str = "final_response.txt") -> bool:
    """
    Save the final response to a text file for parsing with mcp_response_final_parser.py
    
    Args:
        result: Result from execute_mcp_vision_pipeline()
        output_file: Output file path
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        if result['status'] == 'success' and 'final_response' in result:
            with open(output_file, 'w') as f:
                json.dump(result['final_response'], f, indent=2)
            print(f"✅ Final response saved to {output_file}")
            print(f"   You can now parse it with: python mcp_response_final_parser.py")
            return True
        else:
            print(f"❌ No successful response to save. Status: {result['status']}")
            if 'error' in result:
                print(f"   Error: {result['error']}")
            return False
    except Exception as e:
        print(f"❌ Error saving response: {str(e)}")
        return False
