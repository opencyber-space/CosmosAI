#!bin/bash

PREFIX="kini_"
CUR_DIR=$(dirname "$(realpath "$0")")

dockertransformerimagename="${PREFIX}run_aios_transformers"
dockertransformerimagename="kini_magistral_aios_transformers"
container_name="kini_rag_weaviate_test_container"

#-v /home/:/root/.cache/huggingface \

docker run -it \
 --network=host \
 -v /home/ubuntu/models:/home/ubuntu/models \
 -v $CUR_DIR:$CUR_DIR \
 --gpus='"device=3"' \
 --env="BLOCK_ID=hello-001" \
 --env="BLOCKS_DB_URI=http://MANAGEMENTMASTER:30100" \
 --name=$container_name \
 --entrypoint /bin/bash \
  $dockertransformerimagename:v1

