from flask import Flask, request, jsonify
import time
import random

app = Flask(__name__)

@app.route('/v1/infer', methods=['POST'])
def mock_infer():
    print("Received inference request!")
    # Simulate some processing time (LLMs aren't instant)
    # We use a small random delay to make the benchmark realistic
    #time.sleep(random.uniform(0.1, 0.5)) 
    time.sleep(random.uniform(10, 300)) 

    data = request.json
    return jsonify({
        "id": f"chatcmpl-{random.randint(1000, 9999)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": data.get("model", "qwen-mock"),
        "choices": [{
            "message": {"role": "assistant", "content": "This is a mock response."},
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    }), 200

@app.route('/dma-log', methods=['POST'])
def mock_dma():
    print("Received DMA log request!")
    # DMA logging is usually faster
    return jsonify({"status": "logged"}), 200

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(host='0.0.0.0', port=port)