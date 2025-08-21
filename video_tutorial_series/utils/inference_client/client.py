import grpc
import json
import time
import sys

# Add the inference_client directory to the Python path
sys.path.append('./inference_client')

import service_pb2
import service_pb2_grpc

SERVER_ADDRESS = "CLUSTER1MASTER:31500"

def run():
    # Connect to the gRPC server
    channel = grpc.insecure_channel(SERVER_ADDRESS)
    stub = service_pb2_grpc.BlockInferenceServiceStub(channel)

    generation_config = {
        "temperature": 0.1,
        "top_p": 0.95,
        "max_tokens": 512
    }

    # Create the BlockInferencePacket request
    request = service_pb2.BlockInferencePacket(
        block_id="gemma3-27b-block",
        session_id="session_notebook_test",
        seq_no=1,
        data=json.dumps({
            "mode": "chat",
            "message": "Explain the concept of token-based distribution in load balancing.",
            "gen_params": generation_config
        }),
        ts=time.time()
    )

    try:
        st = time.time()
        # Make the gRPC call
        response = stub.infer(request)
        et = time.time()

        print("\\n=== Response Received ===")
        print(f"Latency: {et - st}s")
        print(f"Session ID: {response.session_id}")
        print(f"Sequence No: {response.seq_no}")
        print(f"Data: {response.data}")
        print(f"Timestamp: {response.ts}")

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
