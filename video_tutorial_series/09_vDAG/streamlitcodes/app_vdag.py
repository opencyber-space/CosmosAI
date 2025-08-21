#pip install streamlit websockets nest_asyncio
import streamlit as st
import asyncio
import websockets
import json
import time
import nest_asyncio
import graphviz
import base64
import requests
from io import BytesIO

from utils import get_websocket_url, get_vdag_info, get_vdag_infer_api, get_vdag_inference_api
from client_test import run

# The base URL for your management API
MGMTCOMMAND_API = "http://MANAGEMENTMASTER:30501/api/executeMgmtCommand"
VDAG_URI = "llm-analyzer-aug6:0.0.6-stable"
VDAG_INFO_API = "http://MANAGEMENTMASTER:30103/vdag/"+VDAG_URI
VDAG_CONTROLLER = "aug6-controller"
VDAG_CONTROLLER_GET_API = "http://MANAGEMENTMASTER:30103/vdag-controller"

#CURRENT_SESSION_ID = f"session-{int(time.time())}"
CURRENT_SESSION_ID = "session2"

# Apply the nest_asyncio patch to allow running asyncio in Streamlit
nest_asyncio.apply()

# --- Page Setup ---
st.set_page_config(
    page_title="Streaming Chat", 
    page_icon="🤖",
    layout="wide"  # This makes the layout use full width
)
st.title("🤖 Streaming LLM VDAG")

# --- Session State Initialization ---
# Initialize chat history and other session variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    # Using a timestamp for a simple unique session ID
    st.session_state.session_id = CURRENT_SESSION_ID
if "seq_no" not in st.session_state:
    st.session_state.seq_no = 0

# Initialize WebSocket URIs for each output block
if "websocket_uris" not in st.session_state:
    st.session_state.websocket_uris = {}

if "system_message" not in st.session_state:
    st.session_state.system_message = "You are a helpful assistant."

if "attached_files" not in st.session_state:
    st.session_state.attached_files = []

if "attached_urls" not in st.session_state:
    st.session_state.attached_urls = []

if "connections_for_graphviz" not in st.session_state:
    connections_for_graphviz, output_blocks, all_blocks = get_vdag_info(VDAG_INFO_API, VDAG_URI)
    st.session_state.connections_for_graphviz = connections_for_graphviz
    st.session_state.output_blocks = output_blocks
    st.session_state.all_blocks = all_blocks

    # Initialize WebSocket URIs for each output block
    #for block_id in st.session_state.output_blocks:
    for block_id in st.session_state.all_blocks:
        session_id = st.session_state.session_id #f"session-{block_id}-{int(time.time())}"
        simple_session_id = "vdag::" + VDAG_URI + "::" + session_id
        websocket_uri = get_websocket_url(
            API_URL=MGMTCOMMAND_API,
            block_id=block_id, 
            session_id=simple_session_id
        )
        st.session_state.websocket_uris[block_id] = websocket_uri

    st.session_state.VDAG_INFER_API=get_vdag_inference_api(VDAG_CONTROLLER_GET_API, VDAG_CONTROLLER)
    if not st.session_state.VDAG_INFER_API:
        st.error("Failed to retrieve V-DAG inference API URL. Please check the V-DAG controller configuration.")
# Initialize block responses
if "block_responses" not in st.session_state:
    st.session_state.block_responses = {}
    #for block_id in st.session_state.output_blocks:
    for block_id in st.session_state.all_blocks:
        st.session_state.block_responses[block_id] = ""

# --- V-DAG Graph Visualization (Always at Top) ---
if st.session_state.connections_for_graphviz:
    st.markdown("---")
    st.subheader("🔗 V-DAG Block Connection Diagram")
    
    # Create a new directed graph using connections from V-DAG info
    dot = graphviz.Digraph()
    
    # Graph Attributes
    dot.attr(rankdir='LR')
    dot.attr('node', shape='box', style='rounded', color='darkseagreen3', fontname='Helvetica')
    dot.attr('edge', color='gray40', arrowsize='0.8')
    
    # Find all unique node IDs from the V-DAG connections
    all_nodes = set(st.session_state.connections_for_graphviz.keys())
    for dest_list in st.session_state.connections_for_graphviz.values():
        if isinstance(dest_list, list):
            all_nodes.update(dest_list)
        else:
            all_nodes.add(dest_list)
    
    # Add all nodes to the graph
    for node in all_nodes:
        # Highlight output blocks differently
        if node in st.session_state.output_blocks:
            dot.node(node, node, color='lightblue', style='rounded,filled')
        else:
            dot.node(node, node)
    
    # Add the edges
    for source, destinations in st.session_state.connections_for_graphviz.items():
        if isinstance(destinations, list):
            for destination in destinations:
                dot.edge(source, destination)
        else:
            dot.edge(source, destinations)
    
    # Display the graph
    st.graphviz_chart(dot)
    
    # Show block information
    col1, col2 = st.columns(2)
    with col1:
        total_blocks = len(all_nodes) - 2
        st.info(f"**Total Blocks:** {total_blocks}")
    with col2:
        st.success(f"**Output Blocks:** {', '.join(st.session_state.output_blocks)}")
    
    st.markdown("---")

# --- Block Control Panel ---
st.subheader("🎛️ Block Control Panel")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Reset All Blocks"):
        for block_id in st.session_state.all_blocks:
            st.session_state.block_responses[block_id] = ""
        st.success("All blocks reset!")
        st.rerun()

with col2:
    if st.button("📊 Show Block Details"):
        with st.expander("📋 Detailed Block Information", expanded=True):
            for block_id in st.session_state.all_blocks:
                block_type = "🎯 OUTPUT" if block_id in st.session_state.output_blocks else "🔧 PROCESS"
                response = st.session_state.block_responses.get(block_id, "No activity yet")
                
                st.markdown(f"**{block_type} {block_id}:**")
                if response:
                    st.text_area(f"Response from {block_id}:", response, height=100, key=f"detail_{block_id}")
                else:
                    st.info("No response yet")
                st.markdown("---")

with col3:
    if st.button("🔍 WebSocket URIs"):
        with st.expander("🔗 WebSocket Connection Details", expanded=True):
            for block_id, uri in st.session_state.websocket_uris.items():
                st.markdown(f"**{block_id}:**")
                st.code(uri, language="text")

st.markdown("---")

# --- UI: Display Chat History ---
# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Main Logic ---
# This async function handles the WebSocket communication for a specific block
async def get_streaming_response_for_block(block_id, prompt, response_placeholder):
    """Connects to the WebSocket server and streams the response for a specific block."""
    try:
        print(st.session_state.websocket_uris)
        websocket_uri = st.session_state.websocket_uris[block_id]
        print(websocket_uri)
        if not websocket_uri:
            response_placeholder.markdown(f"❌ No WebSocket URI for block {block_id}")
            return
            
        async with websockets.connect(
            websocket_uri, 
            ping_interval=60,   # Increase ping interval to 60 seconds
            ping_timeout=120,   # Increase ping timeout to 120 seconds  
            close_timeout=30,   # Increase close timeout
            max_size=10**7,     # Increase max message size to 10MB
            compression=None    # Disable compression for better performance
        ) as websocket:
            
            # Only send connect message to listen for streaming output
            simple_session_id = "vdag::" + VDAG_URI + "::" + st.session_state.session_id
            message = {
                "session_id": simple_session_id,
                "connect": True
                #"seq_no": 7,
                #"data": json.dumps({"system_message": "You are a helpful assistant.","mode": "chat", "message": query,"session_id": session_id}),
                #"ts": time.time()
            }

            await websocket.send(json.dumps(message))
            print(f"> Sent connect message for {block_id}: {message}")
            print(f"[{block_id}] Using session_id: {st.session_state.session_id}")

            # Stream response for this specific block
            response_placeholder.markdown(f"🤔 Waiting for response from {block_id}...")
            full_response = ""
            
            # Track activity for connection health monitoring
            last_activity = time.time()
            
            while True:
                try:
                    # Increase timeout and add better error handling
                    try:
                        response_str = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        last_activity = time.time()
                        print(f"[{block_id}] Received: {response_str}")
                    except asyncio.TimeoutError:
                        # Check if connection is still alive
                        current_time = time.time()
                        if current_time - last_activity > 600:  # Increased to 10 minutes
                            response_placeholder.markdown(f"⚠️ No response from {block_id} for 10 minutes. Checking connection...")
                            try:
                                # Send a ping to check if connection is alive
                                pong_waiter = await websocket.ping()
                                await asyncio.wait_for(pong_waiter, timeout=30)
                                response_placeholder.markdown(f"✅ Connection to {block_id} is still alive, continuing to wait...")
                                last_activity = time.time()
                                continue
                            except (asyncio.TimeoutError, Exception) as ping_error:
                                response_placeholder.markdown(f"❌ Connection to {block_id} lost during ping: {ping_error}")
                                break
                        else:
                            # Print a waiting indicator every 30 seconds
                            elapsed = int(current_time - last_activity)
                            if elapsed % 30 == 0 and elapsed > 0:
                                response_placeholder.markdown(f"⏳ Still waiting for {block_id} response... ({elapsed}s elapsed)")
                        continue
                    
                    # Process received data
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
                            print(f"\n✅ Stream completed successfully for {block_id}")
                            break
                        
                        if token:
                            full_response += token
                            print(f"[{block_id}] {token}", end='', flush=True)
                            response_placeholder.markdown(full_response + "▌")

                    except (json.JSONDecodeError, KeyError) as parse_error:
                        print(f"Parse error for {block_id}: {parse_error}, Raw response: {response_str}")
                        # Handle as plain text
                        if response_str.strip():
                            full_response += response_str
                            response_placeholder.markdown(full_response + "▌")
                        
                except websockets.exceptions.ConnectionClosed as e:
                    response_placeholder.markdown(f"🔌 Connection closed by server for {block_id}: {e}")
                    break
                except Exception as e:
                    response_placeholder.markdown(f"❌ Error in main loop for {block_id}: {e}")
                    break

            # Final update without cursor
            if full_response:
                response_placeholder.markdown(full_response)
                st.session_state.block_responses[block_id] = full_response
            else:
                response_placeholder.markdown(f"❌ No response received from {block_id}")
                
    except Exception as e:
        response_placeholder.markdown(f"Failed to connect to WebSocket server for {block_id}: {e}")

# Async function to handle all blocks concurrently
async def get_streaming_responses_for_all_blocks(prompt, response_placeholders, attached_files=None, attached_urls=None):
    """Handle streaming responses for all output blocks concurrently."""
    
    # Process file attachments for the V-DAG inference
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
                st.info(f"📎 Processing local file: {file.name} ({len(file_content)} bytes)")
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
            st.info(f"🔗 Processing URL: {url_item['name']}")

    # First, trigger the V-DAG inference with the initial prompt
    st.session_state.seq_no += 1
    API_URL = st.session_state.VDAG_INFER_API
    vdag_uri = VDAG_URI
    session_id = st.session_state.session_id
    seq_no = st.session_state.seq_no
    gen_params = {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 2048
    }
    text = prompt
    
    # Extract image URLs from attached files for vision models
    image_url = None
    if files_data:
        for file_data in files_data:
            if 'url' in file_data:
                # Check if it's an image file
                file_type = file_data.get('type', '').lower()
                image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
                is_image = any(ext in file_type for ext in image_extensions)
                
                if is_image:
                    image_url = file_data['url']
                    break  # Use the first image URL found
    
    get_vdag_infer_api(
        API_URL=API_URL,
        vdag_uri=vdag_uri,
        session_id=session_id,
        seq_no=seq_no,
        gen_params=gen_params,
        text=text,
        image_url=image_url
    )
    
    print(f"🚀 V-DAG inference triggered with session_id: {session_id}")
    if image_url:
        print(f"📸 Image URL attached: {image_url}")
    if files_data:
        print(f"📎 Total attachments: {len(files_data)}")
    print("⏳ Waiting 2 seconds for V-DAG processing to start...")
    await asyncio.sleep(2)  # Give V-DAG time to start processing

    
    # Now connect to all WebSockets to listen for streaming responses
    tasks = []
    for i, block_id in enumerate(st.session_state.all_blocks):
        task = asyncio.create_task(
            get_streaming_response_for_block(block_id, prompt, response_placeholders[i])
        )
        tasks.append(task)
    
    # Use asyncio.wait instead of gather to avoid blocking on slow tasks
    try:
        done, pending = await asyncio.wait(
            tasks, 
            timeout=300,  # 5 minute timeout
            return_when=asyncio.FIRST_EXCEPTION
        )
        
        # Cancel any pending tasks
        if pending:
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            
    except Exception as e:
        print(f"Error in WebSocket listeners: {e}")
        # Cancel all tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        
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

    # Create dynamic columns based on output_blocks length
    # num_blocks = len(st.session_state.output_blocks)
    num_blocks = len(st.session_state.all_blocks)

    if num_blocks > 0:
        # Create columns for each output block
        cols = st.columns(num_blocks)
        response_placeholders = []
        
        # Create chat_message containers in each column
        # for i, block_id in enumerate(st.session_state.output_blocks):
        for i, block_id in enumerate(st.session_state.all_blocks):
            with cols[i]:
                with st.chat_message("assistant"):
                    st.markdown(f"**{block_id}**")  # Block identifier
                    response_placeholder = st.empty()
                    response_placeholders.append(response_placeholder)
        
        # Call the async function to get responses from all blocks
        asyncio.run(get_streaming_responses_for_all_blocks(
            prompt, 
            response_placeholders,
            attached_files=st.session_state.attached_files,
            attached_urls=st.session_state.attached_urls
        ))
        
        # Add all responses to session state messages
        combined_response = ""
        # for i, block_id in enumerate(st.session_state.output_blocks):
        for i, block_id in enumerate(st.session_state.all_blocks):
            if st.session_state.block_responses[block_id]:
                combined_response += f"**{block_id}:**\n{st.session_state.block_responses[block_id]}\n\n"
        
        if combined_response:
            st.session_state.messages.append({"role": "assistant", "content": combined_response})
        
        # Clear attachments after sending
        st.session_state.attached_files = []
        st.session_state.attached_urls = []
        st.rerun()
    else:
        st.error("No output blocks found. Please check your V-DAG configuration.")



# --- Block Status Dashboard ---
if st.session_state.all_blocks:
    st.subheader("📊 Real-time Block Status")
    
    # Create status cards for each block
    num_cols = min(len(st.session_state.all_blocks), 3)  # Max 3 columns
    status_cols = st.columns(num_cols)
    
    for i, block_id in enumerate(st.session_state.all_blocks):
        with status_cols[i % num_cols]:
            # Get current response and truncate for status display
            current_response = st.session_state.block_responses.get(block_id, "")
            
            # Remove the typing indicator and truncate
            clean_response = current_response.replace(" ▌", "").replace("▌", "")
            truncated = clean_response[:50] + "..." if len(clean_response) > 50 else clean_response
            
            # Determine status color based on content
            if "✅" in clean_response or "completed successfully" in clean_response.lower():
                status_color = "#d4edda"  # Green
                border_color = "#c3e6cb"
            elif "❌" in clean_response or "error" in clean_response.lower():
                status_color = "#f8d7da"  # Red
                border_color = "#f5c6cb"
            elif "⏳" in clean_response or "waiting" in clean_response.lower():
                status_color = "#fff3cd"  # Yellow
                border_color = "#ffeaa7"
            else:
                status_color = "#f9f9f9"  # Default gray
                border_color = "#ddd"
            
            # Display status card
            block_type = "🎯 OUTPUT" if block_id in st.session_state.output_blocks else "🔧 PROCESS"
            st.markdown(f"""
            <div style="
                border: 2px solid {border_color}; 
                border-radius: 8px; 
                padding: 12px; 
                margin: 5px 0;
                background-color: {status_color};
                min-height: 80px;
            ">
                <strong>{block_type}</strong><br>
                <strong style="color: #333;">{block_id}</strong><br>
                <small style="color: #666; margin-top: 5px; display: block;">{truncated if truncated else "Ready..."}</small>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")

# --- Advanced Debug Information ---
if st.session_state.all_blocks:
    with st.expander("🔧 Advanced Debug & Configuration", expanded=False):
        st.markdown("### 📊 Current Block Responses")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📝 Responses", "🔗 Connections", "⚙️ Configuration"])
        
        with tab1:
            for block_id in st.session_state.all_blocks:
                block_type = "🎯 OUTPUT" if block_id in st.session_state.output_blocks else "🔧 PROCESS"
                st.markdown(f"**{block_type} {block_id}:**")
                response = st.session_state.block_responses.get(block_id, "No response yet")
                if response:
                    st.code(response, language="text")
                else:
                    st.info("No activity recorded")
                st.markdown("---")
        
        with tab2:
            st.markdown("### V-DAG Connection Map")
            st.json(st.session_state.connections_for_graphviz)
            
            st.markdown("### Block Categories")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**All Blocks:**")
                for block in st.session_state.all_blocks:
                    st.text(f"• {block}")
            with col2:
                st.markdown("**Output Blocks:**")
                for block in st.session_state.output_blocks:
                    st.text(f"🎯 {block}")
        
        with tab3:
            st.markdown("### Session Configuration")
            st.text(f"Session ID: {st.session_state.session_id}")
            st.text(f"Sequence Number: {st.session_state.seq_no}")
            st.text(f"V-DAG URI: {VDAG_URI}")
            
            st.markdown("### API Endpoints")
            st.code(f"Management API: {MGMTCOMMAND_API}", language="text")
            st.code(f"V-DAG Info API: {VDAG_INFO_API}", language="text")
            st.code(f"V-DAG Inference API: {st.session_state.VDAG_INFER_API}", language="text")

# --- File Attachments Section ---
st.markdown("---")
with st.expander("📎 **File Attachments**", expanded=True):
    # Define allowed file types
    ALLOWED_FILE_TYPES = ["jpg", "jpeg", "png", "gif", "bmp", "webp", "pdf", "txt", "docx", "doc", "csv", "xlsx", "json"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 Upload Files")
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
