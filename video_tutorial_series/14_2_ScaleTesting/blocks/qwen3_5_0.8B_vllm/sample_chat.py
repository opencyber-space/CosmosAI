import grpc
import json
import service_pb2
import service_pb2_grpc
import time

SERVER_ADDRESS = "localhost:50052"
#BLOCKID = "mistral-small"
BLOCKID = "qwen3-32b-block"
#BLOCKID = "magistral-small-2506-llama-cpp-block"
#BLOCKID = "gemma3-27b-block"
BLOCKID = "qwen3-1-7b-vllm-block"

SESSION = "session-110"
INSTANCEID = "in-gocn"

generation_config = {
    "temperature": 0.7,
    "min_p": 0.01,
    "top_k": -1,
    "top_p": 0.95,
    "max_tokens": 50  # Set a limit for the response length
}

#"repeat_penalty":1.0

def run():
    # Connect to the gRPC server
    channel = grpc.insecure_channel("CLUSTER_2_MASTER_NODE:31500")
    #channel = grpc.insecure_channel(SERVER_ADDRESS)
    stub = service_pb2_grpc.BlockInferenceServiceStub(channel)

    # Example file metadata and binary data
    file_info = service_pb2.FileInfo(
        metadata=json.dumps({"filename": "example.txt", "size": 123}),
        file_data=b"Example file content"
    )

    '''output_ptr = {
            "is_graph": True,
            "graph": {
                "hello-001": ["hello-002"]
            }
        }
    '''
    if "gemma3" in BLOCKID:
        # Create the BlockInferencePacket request
        generation_config = {
            "temperature": 0.7,
            "repeat_penalty": 1.0,
            "min_p": 0.01,
            "top_k": -1,
            "top_p": 0.95,
            "max_tokens": 200  # Set a limit for the response length
        }
        request = service_pb2.BlockInferencePacket(
            block_id=BLOCKID,
            session_id=SESSION,
            seq_no=9,
            frame_ptr=b"",  # Empty bytes for now
            data=json.dumps({
                            "mode": "chat",
                            "gen_params": generation_config,
                            "messages": [{"content": [
                                        {"type": "text", "text": "Analyze the following image and generate your objective scene report.?"},
                                        {"type": "image_url",
                                    "image_url": {"url": "https://akm-img-a-in.tosshub.com/indiatoday/images/story/202311/chain-snatching-caught-on-camera-in-bengaluru-293151697-16x9_0.jpg"}}] }],
                            "session_id": SESSION,
                            "system_message": "Analyze the following text and generate your objective scene report."
                        }),
            query_parameters="",
            ts=1234567890.0,
            files=[file_info],  # Attach the file
            output_ptr=b''
        )
    else:
        generation_config = {
            "temperature": 0.7,
            "min_p": 0.01,
            "top_k": -1,
            "top_p": 0.95,
            "max_tokens": 50  # Set a limit for the response length
        }
        # Create the BlockInferencePacket request
        request = service_pb2.BlockInferencePacket(
            block_id=BLOCKID,
            session_id=SESSION,
            seq_no=7,
            frame_ptr=b"",  # Empty bytes for now

            data=json.dumps({
                    "mode": "chat",
                    "system_message": "You are a helpful assistant.",
                    "message": "hi",
                    "gen_params": generation_config,
                    "session_id": SESSION,
                    #"message": "provide a code to add two numbers and print it along with my name"
                    #"message": "Looks like we are having an law and order situation. Person is seen to be snatching the victims bag and running away.",
            }), 
            query_parameters="",
        ts=1234567890.0,
        files=[file_info],  # Attach the file
        output_ptr=b''
    )

    try:

        st = time.time()
        # Make the gRPC call
        response = stub.infer(request)

        et = time.time()


        print("\n=== Response Received ===")
        print(f"Latency: {et - st}s")
        print(f"Session ID: {response.session_id}")
        print(f"Sequence No: {response.seq_no}")
        print(f"Data: {response.data}")
        print(f"Timestamp: {response.ts}")
        print(f"Output Ptr: {response.output_ptr}")
        print(f"Files Received: {len(response.files)}")

        # Parse JSON response data
        try:
            response_data = json.loads(response.data)
            print(f"Parsed Response: {response_data}")
        except json.JSONDecodeError:
            print("Response data is not a valid JSON string.")

    except grpc.RpcError as e:
        print(f"gRPC Error: {e.code()} - {e.details()}")

if __name__ == "__main__":
    run()
