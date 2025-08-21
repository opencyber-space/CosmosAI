import streamlit as st
import asyncio
import websockets
import json
import time
import nest_asyncio
import random
import base64
from io import BytesIO
import sys
import os
import grpc
import subprocess

# This is a workaround for the script being in a subdirectory of the utils folder
# It allows the script to find the inference_client directory
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, 'inference_client'))


try:
    import service_pb2
    import service_pb2_grpc
    from utils import get_websocket_url
    from client_test import run as run_grpc_inference
except ImportError:
    # If the script is run from the utils folder directly, the path might be different
    sys.path.append('inference_client/')
    import service_pb2
    import service_pb2_grpc
    from utils import get_websocket_url
    from client_test import run as run_grpc_inference


# Apply nest_asyncio to allow running asyncio event loops within other event loops (like in Jupyter/Streamlit)
# nest_asyncio.apply()

API_URL = "http://MANAGEMENTMASTER:30501/api/executeMgmtCommand"

def main(block_id, grpc_server_address):
    st.set_page_config(page_title="Streaming Chat", page_icon="🤖")
    st.title("🤖 Streaming WebSocket Chat")
    st.session_state.BLOCKID = block_id
    GRPC_SERVER_ADDRESS = grpc_server_address
    
    # --- Session State Initialization ---  
    # Initialize chat history and other session variables
    if "BLOCKID" not in st.session_state:
        st.session_state.BLOCKID = "gemma3-27b-block2"  # Define your block ID here
        #st.session_state.BLOCKID = "magistral-small-2506-llama-cpp-block"  # Define your block ID here
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        # Using a timestamp for a simple unique session ID
        st.session_state.session_id = f"session-{int(time.time())}"
    if "seq_no" not in st.session_state:
        st.session_state.seq_no = random.randint(1, 1000)

    # Initialize WebSocket URI only once per session
    if "websocket_uri" not in st.session_state:
        # Define the block_id you want to use
        print("BLOCKID:", st.session_state.BLOCKID)
        target_block_id = st.session_state.BLOCKID
        #session_id = "session-2"
        session_id = st.session_state.session_id
        # --- DYNAMICALLY GET WEBSOCKET URI ---
        print("Initializing stream... Please wait.")
        st.session_state.websocket_uri = get_websocket_url(
            API_URL=API_URL,
            block_id=target_block_id, 
            session_id=session_id
        )

    if "system_message" not in st.session_state:
        st.session_state.system_message = "You are a helpful assistant."

    if "attached_files" not in st.session_state:
        st.session_state.attached_files = []

    if "attached_urls" not in st.session_state:
        st.session_state.attached_urls = []

    # --- UI: Display Chat History ---
    # Display past messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Main Logic ---
    # This async function handles the WebSocket communication
    async def get_streaming_response(prompt, attached_files=None, attached_urls=None):
        """Connects to the WebSocket server and streams the response."""
        try:
            async with websockets.connect(
                st.session_state.websocket_uri, 
                ping_interval=60,   # Increase ping interval to 60 seconds
                ping_timeout=120,   # Increase ping timeout to 120 seconds  
                close_timeout=30,   # Increase close timeout
                max_size=10**7,     # Increase max message size to 10MB
                compression=None    # Disable compression for better performance
            ) as websocket:
                # Prepare the message to send
                st.session_state.seq_no += 1
                print(st.session_state.BLOCKID)
                if "gemma" in st.session_state.BLOCKID:
                    print("Using Gemma model for inference")
                    generation_config = {
                        "temperature": 0.1,
                        # "min_p": 0.01,
                        # "top_k": 64,
                        "top_p": 0.95,
                        "max_tokens":1000 # Set a limit for the response length
                    }
                    #prompt = "Analyze the following image and generate your objective scene report.?"
                    # message_to_send = {
                    #     "session_id": st.session_state.session_id,
                    #     "seq_no": st.session_state.seq_no,
                    #     "data": json.dumps({
                    #         "mode": "chat",
                    #         "gen_params": generation_config,
                    #         "messages": [{"content": [
                    #                     {"type": "text", "text": prompt},
                    #                     {"type": "image_url",
                    #                 "image_url": {"url": "https://akm-img-a-in.tosshub.com/indiatoday/images/story/202311/chain-snatching-caught-on-camera-in-bengaluru-293151697-16x9_0.jpg"}}] }],
                    #         "session_id": st.session_state.session_id
                    #         #"system_message": st.session_state.system_message
                    #     }),
                    #     "ts": time.time()
                    # }
                else:
                    generation_config = {
                        "temperature": 0.1,
                        # "min_p": 0.01,
                        # "top_k": 64,
                        "top_p": 0.95,
                        "max_tokens":200 # Set a limit for the response length
                    }
                    # message_to_send = {
                    #     "session_id": st.session_state.session_id,
                    #     "seq_no": st.session_state.seq_no,
                    #     "data": json.dumps({
                    #         "mode": "chat",
                    #         "message": prompt,
                    #         "session_id": st.session_state.session_id
                    #         #"system_message": st.session_state.system_message
                    #     }),
                    #     "ts": time.time()
                    # }
                # print(st.session_state.session_id)
                # print(f"Sending message: {message_to_send}")
                # await websocket.send(json.dumps(message_to_send))

                # Call the run function from client_test.py with the required arguments
                # Prepare file attachments for the gRPC call
                files_data = []
                
                # Process local files
                if attached_files:
                    for file in attached_files:
                        try:
                            file_content = file.read()
                            file.seek(0)  # Reset file pointer
                            files_data.append({
                                "name": file.name,
                                "content": file_content,
                                "type": file.type or "application/octet-stream",
                                "size": len(file_content)
                            })
                            st.info(f"📎 Attached local file: {file.name} ({len(file_content)} bytes)")
                        except Exception as e:
                            st.error(f"Error reading file {file.name}: {e}")
                
                # Process URL files
                if attached_urls:
                    for url_item in attached_urls:
                        files_data.append({
                            "name": url_item['name'],
                            "url": url_item['url'],
                            "type": f"url/{url_item['type']}",
                            "size": 0
                        })
                        st.info(f"🔗 Attached URL: {url_item['name']}")

                run(
                    prompt=prompt,
                    BLOCKID=st.session_state.BLOCKID,
                    SESSION=st.session_state.session_id,
                    seq_no=st.session_state.seq_no,
                    SERVER_ADDRESS=GRPC_SERVER_ADDRESS,
                    generation_config=generation_config,
                    attached_files=files_data  # Pass file data to the run function
                )

                message_to_send = {
                    "session_id": st.session_state.session_id,
                    "connect": True
                }

                await websocket.send(json.dumps(message_to_send))

                # --- UI: Stream response into a container ---
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_response = ""
                    response_placeholder.markdown("🤔 Waiting for LLM response...")
                    
                    # Track activity for connection health monitoring
                    last_activity = time.time()
                    count_tokens = 0
                    tokens_start_time = None
                    while True:
                        try:
                            # Increase timeout and add better error handling
                            try:
                                response_str = await asyncio.wait_for(websocket.recv(), timeout=5.0)  # Increased from 2.0
                                last_activity = time.time()
                            except asyncio.TimeoutError:
                                # Check if connection is still alive
                                current_time = time.time()
                                if current_time - last_activity > 600:  # Increased to 10 minutes
                                    response_placeholder.markdown("⚠️ No response from server for 10 minutes. Checking connection...")
                                    try:
                                        # Send a ping to check if connection is alive
                                        pong_waiter = await websocket.ping()
                                        await asyncio.wait_for(pong_waiter, timeout=30)  # Wait up to 30 seconds for pong
                                        response_placeholder.markdown("✅ Connection is still alive, continuing to wait...")
                                        last_activity = time.time()  # Reset activity timer after successful ping
                                        continue
                                    except (asyncio.TimeoutError, Exception) as ping_error:
                                        st.error(f"❌ Connection lost during ping: {ping_error}")
                                        break
                                else:
                                    # Print a waiting indicator every 30 seconds
                                    elapsed = int(current_time - last_activity)
                                    if elapsed % 30 == 0 and elapsed > 0:
                                        response_placeholder.markdown(f"⏳ Still waiting for response... ({elapsed}s elapsed)")
                                continue
                            
                            # Process received data
                            if tokens_start_time is None:
                                tokens_start_time = time.time()
                            count_tokens += 1
                            print(f"< Received: {response_str}")
                            
                            try:
                                response_data = json.loads(response_str)
                                
                                # Handle different response formats
                                token = ""
                                if 'choices' in response_data and len(response_data['choices']) > 0:
                                    delta = response_data['choices'][0].get('delta', {})
                                    token = delta.get("content", "")
                                elif 'content' in response_data:
                                    token = response_data['content']
                                elif 'token' in response_data:
                                    token = response_data['token']
                                elif 'text' in response_data:
                                    token = response_data['text']
                                elif 'delta' in response_data:
                                    token = response_data['delta']
                                
                                # Check for end of stream
                                if (token == "[END_OF_STREAM]" or 
                                    response_data.get("done", False) or 
                                    response_data.get("finished", False)):
                                    print("\n✅ Stream completed successfully")
                                    break
                                
                                if token:
                                    full_response += token
                                    print(token, end='', flush=True)
                                    response_placeholder.markdown(full_response + "▌")

                            except (json.JSONDecodeError, KeyError) as parse_error:
                                print(f"Parse error: {parse_error}, Raw response: {response_str}")
                                # Handle as plain text
                                if response_str.strip():
                                    full_response += response_str
                                    response_placeholder.markdown(full_response + "▌")
                                
                        except websockets.exceptions.ConnectionClosed as e:
                            st.error(f"🔌 Connection closed by server: {e}")
                            break
                        except Exception as e:
                            st.error(f"❌ Error in main loop: {e}")
                            break
                    tokens_end_time = time.time()
                    print(f"Total tokens received: {count_tokens}")
                    print(f"Time taken for tokens: {tokens_end_time - tokens_start_time:.2f} seconds")
                    print(f"Tokens per second: {count_tokens / (tokens_end_time - tokens_start_time):.2f}")
                # Final update without cursor
                if full_response:
                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    response_placeholder.markdown("❌ No response received from server")
                print(st.session_state.session_id) 
        except Exception as e:
            st.error(f"Failed to connect to WebSocket server: {e}")

    # --- UI: Chat Input ---
    if prompt := st.chat_input("Ask me anything..."):
        # Prepare attachment info for display in chat
        total_attachments = len(st.session_state.attached_files) + len(st.session_state.attached_urls)
        attachment_info = ""
        if total_attachments > 0:
            attachment_info = f"\n\n📎 **Attachments ({total_attachments}):**\n"
            for file in st.session_state.attached_files:
                attachment_info += f"- 📄 {file.name}\n"
            for url_item in st.session_state.attached_urls:
                attachment_info += f"- 🔗 {url_item['name']}\n"
        
        # Add user message to history and display it
        display_content = prompt + attachment_info
        st.session_state.messages.append({"role": "user", "content": display_content})
        with st.chat_message("user"):
            st.markdown(display_content)

        # Call the async function to get the response with attachments
        asyncio.run(get_streaming_response(
            prompt, 
            attached_files=st.session_state.attached_files,
            attached_urls=st.session_state.attached_urls
        ))
        
        # Clear attachments after sending
        st.session_state.attached_files = []
        st.session_state.attached_urls = []
        st.rerun()

    # --- File Attachments Section ---
    st.markdown("---")
    with st.expander("📎 **File Attachments**", expanded=True):
        # Define allowed file types
        ALLOWED_FILE_TYPES = ["jpg", "jpeg", "png", "gif", "bmp", "webp", "pdf", "txt", "docx", "doc", "csv", "xlsx", "json"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("� Upload Files")
            uploaded_files = st.file_uploader(
                "Choose files",
                type=ALLOWED_FILE_TYPES,
                accept_multiple_files=True,
                key="file_uploader"
            )
            if uploaded_files:
                st.session_state.attached_files = uploaded_files
                st.success(f"✅ {len(uploaded_files)} file(s) attached")
        
        with col2:
            st.subheader("🌐 Add URLs")
            url_input = st.text_input(
                "Enter file URL:",
                placeholder="https://example.com/image.jpg",
                key="url_input"
            )
            
            url_col1, url_col2 = st.columns(2)
            with url_col1:
                if st.button("➕ Add", disabled=not url_input):
                    if url_input and url_input.startswith(('http://', 'https://')):
                        if url_input not in [item['url'] for item in st.session_state.attached_urls]:
                            file_ext = url_input.split('.')[-1].lower().split('?')[0]
                            st.session_state.attached_urls.append({
                                'url': url_input,
                                'name': url_input.split('/')[-1].split('?')[0],
                                'type': file_ext
                            })
                            st.success("URL added!")
                            st.rerun()
                        else:
                            st.warning("URL already added")
                    else:
                        st.error("Invalid URL")
            
            with url_col2:
                if st.button("🗑️ Clear"):
                    st.session_state.attached_urls = []
                    st.rerun()
        
        # Show current attachments
        total_attachments = len(st.session_state.attached_files) + len(st.session_state.attached_urls)
        if total_attachments > 0:
            st.markdown("**Current Attachments:**")
            attachment_names = []
            for file in st.session_state.attached_files:
                attachment_names.append(f"📄 {file.name}")
            for url_item in st.session_state.attached_urls:
                attachment_names.append(f"🔗 {url_item['name']}")
            
            st.info(" • ".join(attachment_names))

def start_app(block_id, grpc_server_address, port=8501):
    """
    Launches the Streamlit app in a separate process and returns the external URL.
    """
    # Kill existing processes to ensure a clean start
    subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)

    # Command to run the streamlit app
    command = [
        "streamlit", "run", __file__,
        "--server.port", str(port),
        "--server.headless", "true", # Recommended for running on a server
        "--server.address","0.0.0.0",
        "--",
        "--block_id", block_id,
        "--grpc_server_address", grpc_server_address
    ]
    
    # Start streamlit in the background
    subprocess.Popen(command)
    time.sleep(5)  # Wait for the app to start

    try:
        # Get public IP address
        result = subprocess.run(['curl', '-s', 'ifconfig.me'], capture_output=True, text=True)
        external_ip = result.stdout.strip()
        public_url = f"http://{external_ip}:{port}"
        return public_url
    except Exception as e:
        return f"Error getting public IP: {e}"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Streamlit Chat App for a specific model block.")
    parser.add_argument("--block_id", type=str, required=True, help="The ID of the block to interact with.")
    parser.add_argument("--grpc_server_address", type=str, required=True, help="The gRPC server address.")
    args = parser.parse_args()
    
    main(block_id=args.block_id, grpc_server_address=args.grpc_server_address)
