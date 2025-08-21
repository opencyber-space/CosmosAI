import grpc
import json
import time
import threading
import argparse
import uuid
import random



import sys
sys.path.append('../utils/inference_client')

import grpc
import json
import time

import service_pb2
import service_pb2_grpc

SERVER_ADDRESS = "CLUSTER1MASTER:31500"

QUERIES = [
    "Analyze the following image and generate your objective scene report.",
    "Describe the image in detail. What is happening in the picture?",
    "Provide a summary of the visual content in the attached image.",
    "What are the key objects and actions depicted in this image?",
    "Generate a caption for this image.",
    "Explain the context of this image. What's the story behind it?",
    "Give me a detailed report about the scene in the image provided.",
]

def generate_text(num_tokens):
    """Generates text with a specific number of tokens (approximated)."""
    base_query = random.choice(QUERIES)
    # We can add more words to meet the token count if needed
    words = base_query.split()
    if len(words) < num_tokens:
        extra_words = ["report", "details", "analysis", "scene", "image"]
        for i in range(num_tokens - len(words)):
            words.append(random.choice(extra_words))
    return " ".join(words[:num_tokens])

def run_session(session_id, input_tokens, max_output_tokens):
    """Runs a single gRPC inference session."""
    try:
        channel = grpc.insecure_channel(SERVER_ADDRESS)
        stub = service_pb2_grpc.BlockInferenceServiceStub(channel)

        input_text = generate_text(input_tokens)
        
        generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "max_tokens": max_output_tokens
        }

        request = service_pb2.BlockInferencePacket(
            block_id="gemma3-27b-block2",
            # block_id="llama4-scout-17b-block",
            session_id=session_id,
            seq_no=4001,
            frame_ptr=b"",
            data=json.dumps({
            "mode": "chat",
            "message": "Exaplin the concept of token-based distribution in load balancing.",
            "gen_params":generation_config
            }),
            data=json.dumps({
                "mode": "chat",
                "gen_params": generation_config,
                "messages": [{"content": [
                    {"type": "text", "text": input_text},
                    {"type": "image_url",
                     "image_url": {"url": "https://akm-img-a-in.tosshub.com/indiatoday/images/story/202311/chain-snatching-caught-on-camera-in-bengaluru-293151697-16x9_0.jpg"}}]
                }]
            }),
            query_parameters="",
            ts=time.time(),
            files=[],
            output_ptr=b''
        )

        st = time.time()
        response = stub.infer(request)
        et = time.time()

        print(f"Session {session_id}: Latency: {et - st:.2f}s")

        # # Simple token counting for output
        # output_token_count = len(output_text.split())

        # print(f"Session {session_id}: Latency: {et - st:.2f}s, Input Tokens: {input_tokens}, Output Tokens: ~{output_token_count}")

    except grpc.RpcError as e:
        print(f"gRPC Error for session {session_id}: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"An error occurred in session {session_id}: {e}")


def main():
    """Main function to run the token-based autoscaler test."""
    parser = argparse.ArgumentParser(description="Test client for token-based autoscaler.")
    parser.add_argument(
        "--num-requests",
        type=int,
        default=1,
        help="Number of concurrent requests to send."
    )
    parser.add_argument(
        "--input-tokens",
        type=int,
        default=100,
        help="Number of input tokens for each request."
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=100,
        help="Max number of output tokens for each request."
    )
    args = parser.parse_args()

    print(f"Starting test with {args.num_requests} concurrent requests.")
    print(f"Each request will have {args.input_tokens} input tokens and ask for max {args.max_output_tokens} output tokens.")

    threads = []
    for _ in range(args.num_requests):
        session_id = f"session-{uuid.uuid4()}"
        thread = threading.Thread(target=run_session, args=(session_id, args.input_tokens, args.max_output_tokens))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    print("Test finished.")


if __name__ == "__main__":
    main()
