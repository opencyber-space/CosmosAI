curl -X POST  http://CLUSTER2MASTER:31126/v1/infer \
  -H "Content-Type: application/json" \
  -d '{
  "timeout": 1200,
  "retries": 3,
  "session_id": "session1",
  "seq_no": 3,
  "data": {
    "mode": "generate",
    "generation_config": {
      "temperature": 0.7,
      "repetition_penalty": 1.0,
      "min_p": 0.01,
      "top_k": -1,
      "top_p": 0.95,
      "max_tokens": 256
    },
    "messages": [
      {
        "content": [
          {
            "type": "text",
            "text": "write a one lines about photosynthesis"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": ""
            }
          }
        ]
      }
    ]
  },
  "graph": {},
  "selection_query": {}
}' | json_pp &

curl -X POST  http://CLUSTER2MASTER:31126/v1/infer \
  -H "Content-Type: application/json" \
  -d '{
  "timeout": 1200,
  "retries": 3,
  "session_id": "session1",
  "seq_no": 4,
  "data": {
    "mode": "generate",
    "generation_config": {
      "temperature": 0.7,
      "repetition_penalty": 1.0,
      "min_p": 0.01,
      "top_k": -1,
      "top_p": 0.95,
      "max_tokens": 256
    },
    "messages": [
      {
        "content": [
          {
            "type": "text",
            "text": "write a one lines about color theory"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": ""
            }
          }
        ]
      }
    ]
  },
  "graph": {},
  "selection_query": {}
}' | json_pp &

curl -X POST  http://CLUSTER2MASTER:31126/v1/infer \
  -H "Content-Type: application/json" \
  -d '{
  "timeout": 1200,
  "retries": 3,
  "session_id": "session1",
  "seq_no": 5,
  "data": {
    "mode": "generate",
    "generation_config": {
      "temperature": 0.7,
      "repetition_penalty": 1.0,
      "min_p": 0.01,
      "top_k": -1,
      "top_p": 0.95,
      "max_tokens": 256
    },
    "messages": [
      {
        "content": [
          {
            "type": "text",
            "text": "write a one lines about army"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": ""
            }
          }
        ]
      }
    ]
  },
  "graph": {},
  "selection_query": {}
}' | json_pp &

curl -X POST  http://CLUSTER2MASTER:31126/v1/infer \
  -H "Content-Type: application/json" \
  -d '{
  "timeout": 1200,
  "retries": 3,
  "session_id": "session1",
  "seq_no": 6,
  "data": {
    "mode": "generate",
    "generation_config": {
      "temperature": 0.7,
      "repetition_penalty": 1.0,
      "min_p": 0.01,
      "top_k": -1,
      "top_p": 0.95,
      "max_tokens": 256
    },
    "messages": [
      {
        "content": [
          {
            "type": "text",
            "text": "write a one lines about sports"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": ""
            }
          }
        ]
      }
    ]
  },
  "graph": {},
  "selection_query": {}
}' | json_pp &

wait

