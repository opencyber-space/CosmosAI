import random
import grpc
import json
import service_pb2
import service_pb2_grpc
import time
import threading

SERVER_ADDRESS = "CLUSTER1MASTER:31500"
#BLOCKID = "mistral-small"
BLOCKID = "qwen3-32b-block"
BLOCKID = "magistral-small-2506-llama-cpp-block"
BLOCKID = "gemma3-27b-block"
SESSION = "session-31002"
INSTANCEID = "in-gocn"

generation_config = {
    "temperature": 0.7,
    "repeat_penalty": 1.0,
    "min_p": 0.01,
    "top_k": -1,
    "top_p": 0.95,
    "max_tokens": 50  # Set a limit for the response length
}

def run(prompt, BLOCKID, SESSION, seq_no, SERVER_ADDRESS, generation_config={}, attached_files=None):
    print(prompt, BLOCKID, SESSION, seq_no, SERVER_ADDRESS, generation_config, attached_files)

    # Example file metadata and binary data
    file_info = service_pb2.FileInfo(
        metadata=json.dumps({"filename": "example.txt", "size": 123}),
        file_data=b"Example file content"
    )

    # Process attached files
    files_list = []
    if attached_files:
        for file_data in attached_files:
            if 'content' in file_data:  # Local file
                file_info_1 = service_pb2.FileInfo(
                    metadata=json.dumps({
                        "filename": file_data['name'],
                        "size": file_data['size'],
                        "type": file_data['type']
                    }),
                    file_data=file_data['content']
                )
                files_list.append(file_info_1)
                print(f"Added local file: {file_data['name']}")
            elif 'url' in file_data:  # URL file
                file_info_1 = service_pb2.FileInfo(
                    metadata=json.dumps({
                        "filename": file_data['name'],
                        "url": file_data['url'],
                        "type": file_data['type']
                    }),
                    file_data=b""  # Empty for URL files
                )
                files_list.append(file_info_1)
                print(f"Added URL file: {file_data['name']} -> {file_data['url']}")
    
    # If no files attached, use default example file
    if not files_list:
        file_info_1 = service_pb2.FileInfo(
            metadata=json.dumps({"filename": "example.txt", "size": 123}),
            file_data=b"Example file content"
        )
        files_list.append(file_info_1)

    '''output_ptr = {
            "is_graph": True,
            "graph": {
                "hello-001": ["hello-002"]
            }
        }
    '''
    if "gemma3" in BLOCKID:
        # Create the BlockInferencePacket request
        if not generation_config:
            generation_config = {
                "temperature": 0.1,
                "repeat_penalty": 1.0,
                "min_p": 0.01,
                "top_k": -1,
                "top_p": 0.95,
                "max_tokens": 200  # Set a limit for the response length
            }
        #prompt = "Analyze the following image and generate your objective scene report?"
        
        # Build message content with text and images
        message_content = [{"type": "text", "text": prompt}]
        
        # Add image URLs from attached files
        if attached_files:
            for file_data in attached_files:
                print(f"Processing file: {file_data}")
                if 'url' in file_data:
                    # Check if it's an image file by looking at the file extension
                    file_type = file_data.get('type', '').lower()
                    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
                    
                    # Check if the type contains any image extension
                    is_image = any(ext in file_type for ext in image_extensions)
                    
                    if is_image:
                        message_content.append({
                            "type": "image_url",
                            "image_url": {"url": file_data['url']}
                        })
                        print(f"✓ Added image URL to message: {file_data['url']}")
                    else:
                        print(f"✗ Skipped non-image file: {file_data['name']} (type: {file_type})")
                else:
                    print(f"✗ Skipped file without URL: {file_data.get('name', 'unknown')}")
        
        request = service_pb2.BlockInferencePacket(
            block_id=BLOCKID,
            session_id=SESSION,
            seq_no=seq_no,
            frame_ptr=b"",  # Empty bytes for now
            data=json.dumps({
                "mode": "chat",
                "gen_params": generation_config,
                "messages": [{"content": message_content}],
                "session_id": SESSION,
                "system_message": "Analyze the following content and generate your objective report."
            }),
            query_parameters="",
            ts=time.time(),
            files=[file_info], #files_list,  # Use the processed files list
            output_ptr=b''
        )
    else:
        if not generation_config:
            generation_config = {
                "temperature": 0.7,
                "repeat_penalty": 1.0,
                "min_p": 0.01,
                "top_k": -1,
                "top_p": 0.95,
                "max_tokens": 50  # Set a limit for the response length
            }
        # Create the BlockInferencePacket request
        request = service_pb2.BlockInferencePacket(
            block_id=BLOCKID,
            session_id=SESSION,
            seq_no=seq_no,
            frame_ptr=b"",  # Empty bytes for now

            data=json.dumps({
                    "mode": "chat",
                    "system_message": "You are a helpful assistant.",
                    "message": prompt,
                    "gen_params": generation_config,
                    "session_id": SESSION,
                    #"message": "provide a code to add two numbers and print it along with my name"
                    #"message": "Looks like we are having an law and order situation. Person is seen to be snatching the victims bag and running away.",
            }), 
            query_parameters="",
            ts=time.time(),
            files=[file_info], #files_list,  # Use the processed files list
            output_ptr=b''
    )

    print(f"Request: {request}")
    

    try:
        # Test connection first
        print("Testing connection to server...")
        channel = grpc.insecure_channel(SERVER_ADDRESS)
        
        # Wait for the channel to be ready
        try:
            grpc.channel_ready_future(channel).result(timeout=5)
            print("✓ Connection to server established")
        except grpc.FutureTimeoutError:
            print("✗ Connection timeout - server might be unreachable")
            return
        
        stub = service_pb2_grpc.BlockInferenceServiceStub(channel)
        
        # Send the request synchronously with a longer timeout
        print("Sending request...")
        print(f"Request details: block_id={request.block_id}, session_id={request.session_id}, seq_no={request.seq_no}")
        
        try:
            # Send with a reasonable timeout to ensure it reaches the server
            response = stub.infer(request, timeout=0.1)
            print("✓ Request sent and response received (but we'll ignore the response)")
            print(f"Response session_id: {response.session_id}")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                print("✓ Request sent (timeout occurred while waiting for response - this is expected)")
            else:
                print(f"✗ gRPC Error: {e.code()} - {e.details()}")
        
        print("Closing connection...")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Close the channel
    try:
        channel.close()
        print("✓ Channel closed")
    except:
        pass

if __name__ == "__main__":
    seq_no = random.randint(1, 1000)  # Generate a random sequence number
    prompt = "Analyze the following image and generate your objective scene report."
    if "gemma3" not in BLOCKID:
        prompt = "hi"
    run(prompt, BLOCKID, SESSION, seq_no, SERVER_ADDRESS, generation_config, attached_files=[])
