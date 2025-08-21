curl -X POST http://MANAGEMENTMASTER:30101/clusters/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
        "regionId": "us-west-2",
        "status": "live"
    }
  }'
