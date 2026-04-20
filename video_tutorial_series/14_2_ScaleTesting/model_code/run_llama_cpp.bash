#!bin/bash

PREFIX="kini_"
FINALDOCKERNAME="magistral_aios_llama_cpp"
FOLDER_NAME="magistral"
container_name="${PREFIX}magistral_test_container_llama_cpp"
# FINALDOCKERNAME="qwen3_aios_llama_cpp"
# FOLDER_NAME="qwen3"
# container_name="${PREFIX}qwen3_test_container_llama_cpp"
CUR_DIR=$(dirname "$(realpath "$0")")

dockertransformerimagename="${PREFIX}${FINALDOCKERNAME}"
version="v1"

docker run -it \
 --network=host \
 -v /home/ubuntu/models:/home/ubuntu/models \
 -v $CUR_DIR:/$FOLDER_NAME \
 --gpus=all \
 --env="BLOCK_ID=hello-001" \
 --env="BLOCKS_DB_URI=http://MANAGEMENTMASTER:30100" \
 --name=$container_name \
 --entrypoint /bin/bash \
  $dockertransformerimagename:$version



# docker commit \
#   -c 'WORKDIR /magistral' \
#   -c 'ENTRYPOINT ["python3", "-u" ,"main.py"]' \
#   kini_magistral_test_container MANAGEMENTMASTER:31280/magistral-small-2506