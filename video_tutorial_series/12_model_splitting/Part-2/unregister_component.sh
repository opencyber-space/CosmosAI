curl -X POST http://MANAGEMENTMASTER:30112/api/unregisterComponent \
  -H "Content-Type: application/json" \
  -d '{"uri":"model.vllm-runner-demo:1.0.0-stable"}' | json_pp