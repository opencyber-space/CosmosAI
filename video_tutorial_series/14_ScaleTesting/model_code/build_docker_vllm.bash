PREFIX="MANAGEMENTMASTER:31280/"
FINALDOCKERNAME="vllm_batching_aios" #for vllm
FOLDER_NAME="magistral"
CUR_DIR=$(dirname "$(realpath "$0")")

dockertransformerimagename="${PREFIX}${FINALDOCKERNAME}"
version="v1"

docker build . -t $dockertransformerimagename:$version --build-arg FOLDER_NAME=$FOLDER_NAME -f Dockerfile_vllm



#for squashing
#pip install docker-squash
#docker-squash -t MANAGEMENTMASTER:31280/vllm_batching_aios:squashed MANAGEMENTMASTER:31280/vllm_batching_aios:v1