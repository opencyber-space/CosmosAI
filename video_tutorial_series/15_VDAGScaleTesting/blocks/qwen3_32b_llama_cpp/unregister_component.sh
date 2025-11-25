curl -X POST http://MANAGEMENTMASTER:30112/api/unregisterComponent \
  -H "Content-Type: application/json" \
  -d '{"uri":"model.qwen3-32b-llama_cpp:1.0.0-stable"}' | json_pp