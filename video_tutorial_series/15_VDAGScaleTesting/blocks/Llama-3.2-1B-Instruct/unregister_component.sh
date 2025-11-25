curl -X POST http://MANAGEMENTMASTER:30112/api/unregisterComponent \
  -H "Content-Type: application/json" \
  -d '{"uri":"model.magistral-small-2506-vllm:1.0.0-stable"}' | json_pp