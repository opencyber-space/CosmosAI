#For Get Block Details after creation if needed
curl -X GET http://MANAGEMENTMASTER:30100/blocks/demo-magistral-llama_cpp \
    -H "Content-Type: application/json" | json_pp