GATEWAY_URL="MANAGEMENTMASTER:30600"

#first create the block
#log in to node where this block is allocated
#run nvidia-smi to which GPU this model is allocated or check controllers pod
# kubectl get pods -n controllers
# kubectl logs -f -n controllers gcp-cluster-2-controller-64c745f7dc-d9tcp infra --tail 100
#the log will tell which GPU this instance would have allocated
# based on that plan you allocation of instance in all nodes

curl -X POST "http://$GATEWAY_URL/controller/block-scaling/gcp-cluster-2" \
     -H "Content-Type: application/json" \
     -d '{
           "operation": "scale",
           "block_id": "qwen3-5-0-8b-vllm-block",
           "instances_count": 15,
           "allocation_data": [
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [0]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [0]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [1]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [2]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [2]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [3]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [3]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [4]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [4]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [5]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [5]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [6]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [6]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [1]
               },
               {
                   "node_id": "b200-node1",
                   "gpu_ids": [7]
               }
           ]
         }' | json_pp

# curl -X POST "http://$GATEWAY_URL/controller/block-scaling/gcp-cluster-2" \
#      -H "Content-Type: application/json" \
#      -d '{
#            "operation": "scale",
#            "block_id": "qwen3-5-0-8b-vllm-block",
#            "instances_count": 2,
#            "allocation_data": [
#                {
#                    "node_id": "b200-node1",
#                    "gpu_ids": [0]
#                },
#                {
#                    "node_id": "b200-node1",
#                    "gpu_ids": [1]
#                }
#            ]
#          }' | json_pp