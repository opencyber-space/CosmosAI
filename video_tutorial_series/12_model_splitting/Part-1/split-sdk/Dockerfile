#FROM MANAGEMENTMASTER:31280/example/llm-runner:latest

FROM pytorch/pytorch:2.7.1-cuda12.6-cudnn9-devel

# ── Environment tweaks ──
ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_PROGRESS_BAR=off \
    MAX_JOBS=2 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1

COPY . /app

WORKDIR /app

RUN pip3 install -r requirements.txt