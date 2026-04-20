PREFIX="kini_"
FINALDOCKERNAME="magistral_aios_llama_cpp"  #for llamacpp-python kini
#FINALDOCKERNAME="magistral-small-2506-llama-cpp-block-debater" #for sriknath
FOLDER_NAME="magistral"
# FINALDOCKERNAME="qwen3_aios_llama_cpp"
# FOLDER_NAME="qwen3"
CUR_DIR=$(dirname "$(realpath "$0")")

dockertransformerimagename="${PREFIX}${FINALDOCKERNAME}"
version="v1"

#we have commeneted one line in aios_llama_cpp/__init__.py to use vllm library

docker build . -t $dockertransformerimagename:$version --build-arg FOLDER_NAME=$FOLDER_NAME -f Dockerfile_llama_cpp

