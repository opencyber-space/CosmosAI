#!/bin/bash

#run this like: bash docker/build_aios_transformers.bash true

apt install -y git

CUR_DIR=$(dirname "$(realpath "$0")")

#git clone https://github.com/OpenCyberspace/AIGr.id.git

cd "$CUR_DIR/../AIGr.id/services/applications/aios-sdk/instance-sdk"

# Parameter to control which Dockerfile to use
USE_TRANSFORMER=${1:-false}
PREFIX="kini_"
dockerimagename="${PREFIX}aios_instance"
if [ "$USE_TRANSFORMER" = "true" ]; then
    # Copy Dockerfile to Dockerfile_transformer
    cp Dockerfile Dockerfile_aios_instance_base

    # Comment out the FROM python:3.11-buster line
    sed -i 's/^FROM python:3\.11-buster/# &/' Dockerfile_aios_instance_base

    # Append custom content to Dockerfile_transformer
    cat <<'EOF' > temp_dockerfile
# ────────────────────────────────────────────────────────────────
# Base: PyTorch 2.2.2 + CUDA 12.1 + cuDNN 8  (has git & build tools)
# ────────────────────────────────────────────────────────────────
FROM pytorch/pytorch:2.2.2-cuda12.1-cudnn8-devel

# ── Environment tweaks ──
ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_PROGRESS_BAR=off \
    MAX_JOBS=2 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1

# ── Install Python dependencies ──
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ── Copy your inference code ──
WORKDIR /app
#COPY generic_llm.py models.yaml ./

# ── Default command; change flags here, not as standalone lines ──
#CMD [
#  "python", "generic_llm.py",
#  "--model", "llama3-8b-instruct",
#  "--quantized", "yes"
#]
EOF

    cat Dockerfile_aios_instance_base >> temp_dockerfile
    mv temp_dockerfile Dockerfile_aios_instance_base
    #do a sed in Dockerfile_aios_instance_base to remove ```CMD ["python3", "main.py"]` with ```RUN pip3 install -e .```
    docker build . -t $dockerimagename:v1 -f Dockerfile_aios_instance_base
else
    # for python buster image of aios_instance:v1
    #do a sed in Dockerfile_aios_instance_base to remove ```CMD ["python3", "main.py"]` with ```RUN pip3 install -e .```
    docker build . -t $dockerimagename:v1 -f Dockerfile
fi

cd "$CUR_DIR/../AIGr.id/services/applications/aios-sdk/llm-utils/aios_transformers"

# Insert the RUN sed command into the Dockerfile before building
sed -i '/RUN pip3 install -e \./i RUN sed -i '\''/long_description=open("README.md").read(),/d;/long_description_content_type="text\\/markdown",/d'\'' /installer/setup.py' Dockerfile

sed -i "s/^FROM aios_instance:v1/FROM ${dockerimagename}:v1/" Dockerfile
dockertransformerimagename="${PREFIX}aios_transformers"
docker build . -t $dockertransformerimagename:v1 -f Dockerfile

cd "$CUR_DIR/"

dockertransformerimagename="${PREFIX}run_aios_transformers"
docker build . -t $dockertransformerimagename:v1 -f Dockerfile