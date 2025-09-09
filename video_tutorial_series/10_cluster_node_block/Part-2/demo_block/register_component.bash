curl -X POST http://MANAGEMENTMASTER:30112/api/registerComponent \
  -H "Content-Type: application/json" \
  -d @./component_demo_magistral.json | json_pp