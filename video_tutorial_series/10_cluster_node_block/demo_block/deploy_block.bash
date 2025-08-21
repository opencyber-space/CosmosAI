#For Create Block
curl -X POST -d @./allocation-demo-mistral.json \
     -H "Content-Type: application/json" \
     http://MANAGEMENTMASTER:30501/api/createBlock