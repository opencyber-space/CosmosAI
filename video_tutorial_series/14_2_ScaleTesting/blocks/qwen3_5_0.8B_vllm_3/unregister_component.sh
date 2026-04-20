curl -X POST http://MANAGEMENTMASTER:30112/api/unregisterComponent \
  -H "Content-Type: application/json" \
  -d '{"uri":"model.qwen3-5-0-8B-vllm:1.0.0-stable"}' | json_pp