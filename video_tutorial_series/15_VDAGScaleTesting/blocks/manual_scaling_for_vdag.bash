GATEWAY_URL="MANAGEMENTMASTER:30600"

#first create the block
#log in to node where this block is allocated
#run nvidia-smi to which GPU this model is allocated or check controllers pod
# kubectl get pods -n controllers
# kubectl logs -f -n controllers gcp-cluster-2-controller-64c745f7dc-d9tcp infra --tail 100
# the log will tell which GPU this instance would have allocated
# based on that plan you allocation of instance in all nodes

curl -X POST "http://$GATEWAY_URL/controller/block-scaling/gcp-cluster-2" \
     -H "Content-Type: application/json" \
     -d '{
           "operation": "scale",
           "block_id": "qwen3-1-7b-vllm-block",
           "instances_count": 5,
           "allocation_data": [
               {
                   "node_id": "wc-gpu-node1",
                   "gpu_ids": [0]
               },
               {
                   "node_id": "wc-gpu-node4",
                   "gpu_ids": [0]
               },
               {
                   "node_id": "wc-gpu-node4",
                   "gpu_ids": [1]
               },
               {
                   "node_id": "wc-gpu-node4",
                   "gpu_ids": [2]
               },
               {
                   "node_id": "wc-gpu-node4",
                   "gpu_ids": [3]
               }
           ]
         }' | json_pp


curl -X POST "http://$GATEWAY_URL/controller/block-scaling/gcp-cluster-2" \
     -H "Content-Type: application/json" \
     -d '{
           "operation": "scale",
           "block_id": "phi-4-mini-instruct-vllm-block",
           "instances_count": 7,
           "allocation_data": [
               {
                   "node_id": "wc-gpu-node9",
                   "gpu_ids": [0]
               },
               {
                   "node_id": "wc-gpu-node9",
                   "gpu_ids": [1]
               },
               {
                   "node_id": "wc-gpu-node9",
                   "gpu_ids": [1]
               },
               {
                   "node_id": "wc-gpu-node9",
                   "gpu_ids": [2]
               },
               {
                   "node_id": "wc-gpu-node9",
                   "gpu_ids": [2]
               },
               {
                   "node_id": "wc-gpu-node9",
                   "gpu_ids": [3]
               },
               {
                   "node_id": "wc-gpu-node9",
                   "gpu_ids": [3]
               }
           ]
         }' | json_pp


# curl -X POST "http://$GATEWAY_URL/controller/block-scaling/gcp-cluster-2" \
#      -H "Content-Type: application/json" \
#      -d '{
#            "operation": "scale",
#            "block_id": "deepseek-r1-distill-qwen-1-5b-vllm-block",
#            "instances_count": 3,
#            "allocation_data": [
#                {
#                    "node_id": "wc-gpu-node2",
#                    "gpu_ids": [0]
#                },
#                {
#                    "node_id": "wc-gpu-node2",
#                    "gpu_ids": [1]
#                },
#                {
#                    "node_id": "wc-gpu-node2",
#                    "gpu_ids": [1]
#                }
#            ]
#          }' | json_pp

curl -X POST "http://$GATEWAY_URL/controller/block-scaling/gcp-cluster-2" \
     -H "Content-Type: application/json" \
     -d '{
           "operation": "scale",
           "block_id": "llama-3-2-1b-instruct-vllm-block",
           "instances_count": 3,
           "allocation_data": [
               {
                   "node_id": "wc-gpu-node2",
                   "gpu_ids": [0]
               },
               {
                   "node_id": "wc-gpu-node2",
                   "gpu_ids": [1]
               },
               {
                   "node_id": "wc-gpu-node2",
                   "gpu_ids": [1]
               }
           ]
         }' | json_pp

curl -X POST "http://$GATEWAY_URL/controller/block-scaling/gcp-cluster-2" \
     -H "Content-Type: application/json" \
     -d '{
           "operation": "scale",
           "block_id": "gemma-3-1b-it-vllm-block",
           "instances_count": 3,
           "allocation_data": [
               {
                   "node_id": "wc-gpu-node7",
                   "gpu_ids": [0]
               },
               {
                   "node_id": "wc-gpu-node7",
                   "gpu_ids": [1]
               },
               {
                   "node_id": "wc-gpu-node7",
                   "gpu_ids": [1]
               }
           ]
         }' | json_pp