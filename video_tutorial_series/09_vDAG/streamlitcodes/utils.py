import requests
import json
import time,os,sys




def get_websocket_url(API_URL: str, block_id: str, session_id: str) -> str | None:
    """
    Calls two management APIs sequentially to enable streaming and get the WebSocket URL.

    Args:
        block_id: The block ID for the first API call.
        session_id: The session ID for the second API call.

    Returns:
        The WebSocket URL as a string if successful, otherwise None.
    """
    headers = {"Content-Type": "application/json"}

    # --- Step 1: Call the 'enable_streaming' endpoint ---
    payload_1 = {
        "header": {"templateUri": "Parser/V1", "parameters": {}},
        "body": {
            "spec": {
                "values": {
                    "blockId": block_id,
                    "service": "executor",
                    "mgmtCommand": "enable_streaming",
                    "mgmtData": {}
                }
            }
        }
    }
    
    try:
        print("Step 1: Enabling streaming...")
        response_1 = requests.post(API_URL, headers=headers, json=payload_1, timeout=10)
        response_1.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        print("Step 1: Successfully enabled streaming.")

    except requests.exceptions.RequestException as e:
        print(f"Error calling 'enable_streaming' API: {e}")
        return None

    # --- Step 2: Call the 'get_streaming_url' endpoint ---
    payload_2 = {
        "header": {"templateUri": "Parser/V1", "parameters": {}},
        "body": {
            "spec": {
                "values": {
                    "blockId": block_id,
                    "service": "executor",
                    "mgmtCommand": "get_streaming_url",
                    "mgmtData": {"session_id": session_id}
                }
            }
        }
    }
    
    try:
        print("Step 2: Getting streaming URL...")
        response_2 = requests.post(API_URL, headers=headers, json=payload_2, timeout=10)
        response_2.raise_for_status()
        
        # --- Step 3: Parse the response and extract the URL ---
        data = response_2.json()
        if data.get("result", {}).get("success"):
            ws_url = data["result"].get("url")
            if ws_url:
                print(f"Step 2: Successfully retrieved URL: {ws_url}")
                return ws_url
            else:
                print("Error: 'url' not found in the response from the second API.")
                return None
        else:
            print(f"Error: The second API call was not successful. Response: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error calling 'get_streaming_url' API: {e}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing response from the second API: {e}")
        return None

def get_vdag_info(API_URL: str, vdag_uri: str):
    """
    Fetches the V-DAG information from the specified API URL.

    Args:
        API_URL: The base URL for the V-DAG API.
        vdag_uri: The specific URI for the V-DAG.

    Returns:
        A dictionary containing the V-DAG information.
    """
    try:
        response = requests.get(f"{API_URL}", timeout=60)
        response.raise_for_status()
        vdag_info = response.json()
        all_blocks = []
        if "data" in vdag_info:
            #print("V-DAG Info:", json.dumps(vdag_info["data"], indent=2))
            if "compiled_graph_data" in vdag_info["data"]:
                compiled_graph_data = vdag_info["data"]["compiled_graph_data"]
                head = compiled_graph_data["head"]
                t2_graph = compiled_graph_data["t2_graph"]
                t3_graph = compiled_graph_data["t3_graph"]
                output_blocks = []
                for k,v in t2_graph.items():
                    all_blocks.append(k)
                    if len(v) == 0:
                        print(f"output block is: {v}")
                        output_blocks.append(k)
                connections_for_graphviz = {}
                connections_for_graphviz["User_Input"] = [head]
                for k, v in t2_graph.items():
                    if len(v) > 0:
                        connections_for_graphviz[k] = v
                    else:
                        connections_for_graphviz[k] = ['Done']
        return connections_for_graphviz, output_blocks, all_blocks
    except requests.exceptions.RequestException as e:
        print(f"Error fetching V-DAG info: {e}")
        return {}, [], []

def get_vdag_infer_api(API_URL: str, vdag_uri: str, session_id: str, seq_no: str, gen_params: dict, \
                       text: str, image_url: str) -> dict | None:
    """
    Calls the V-DAG inference API with the provided parameters.

    Args:
        API_URL: The base URL for the V-DAG inference API.
        vdag_uri: The specific URI for the V-DAG (not used in current implementation).
        session_id: The session ID for the inference call.
        seq_no: The sequence number for the inference call.
        gen_params: Dictionary containing generation parameters (temperature, top_p, max_tokens).
        text: The text content to analyze.
        image_url: The URL of the image to analyze.

    Returns:
        The response from the API as a string if successful, otherwise None.
    """
    headers = {"Content-Type": "application/json"}
    
    # Build the content array based on what's provided
    content = []
    
    # Add text content if provided
    if text:
        content.append({
            "type": "text",
            "text": text
        })
    else:
        print("No text provided, using default text.")
        content.append({
            "type": "text",
            "text": "Analyze the following text and generate your objective scene report."
        })

    # Add image content if provided
    if image_url:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": image_url
            }
        })
    else:
        default_image_url = "https://akm-img-a-in.tosshub.com/indiatoday/images/story/202311/chain-snatching-caught-on-camera-in-bengaluru-293151697-16x9_0.jpg"
        print("No image URL provided, using default image.", default_image_url)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": default_image_url
            }
        })

    
    # Build the payload
    payload = {
        "session_id": session_id,
        "seq_no": int(seq_no),
        "data": {
            "mode": "chat",
            "gen_params": gen_params,
            "messages": [
                {
                    "content": content
                }
            ]
        },
        "graph": {},
        "selection_query": {}
    }
    
    try:
        print(f"Calling V-DAG inference API with session_id: {session_id}, seq_no: {seq_no}")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=0.5)
        response.raise_for_status()
        
        print("Successfully called V-DAG inference API")
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error calling V-DAG inference API: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in V-DAG inference API call: {e}")
        return None
        

def get_vdag_inference_api(URL: str, VDAG_CONTROLLER_NAME: str) -> str | None:
    """
    Calls the V-DAG controller API to get the inference API URL.

    Args:
        URL: The base URL for the V-DAG controller API.
        VDAG_CONTROLLER_NAME: The name of the V-DAG controller.

    Returns:
        The api_url from the response if successful, otherwise None.
    """
    # Construct the full URL
    full_url = f"{URL}/{VDAG_CONTROLLER_NAME}"
    
    try:
        print(f"Calling V-DAG controller API: {full_url}")
        response = requests.get(full_url, timeout=30)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        
        # Parse the JSON response
        data = response.json()
        
        # Check if the request was successful
        if data.get("success", False):
            # Extract api_url from the nested structure
            config = data.get("data", {}).get("config", {})
            api_url = config.get("api_url")
            
            if api_url:
                print(f"Successfully retrieved api_url: {api_url}")
                return api_url+"/v1/infer"
            else:
                print("Error: 'api_url' not found in the response config.")
                print(f"Available config keys: {list(config.keys())}")
                return None
        else:
            print(f"Error: API call was not successful. Response: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error calling V-DAG controller API: {e}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing response from V-DAG controller API: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in V-DAG controller API call: {e}")
        return None
        

if __name__ == "__main__":
    VDAG_URI = "llm-analyzer:0.0.1-stable"
    VDAG_INFO_API = "http://MANAGEMENTMASTER:30103/vdag/"+VDAG_URI
    VDAG_INFER_API = "http://CLUSTER1MASTER:30893/v1/infer"
    connections_for_graphviz, output_blocks = get_vdag_info(VDAG_INFO_API, VDAG_URI)
    print("Connections for Graphviz:", connections_for_graphviz)
    print("Output Blocks:", output_blocks)
