FROM python:3.12-slim
# FROM nvidia/cuda:13.1.0-runtime-ubuntu22.04

WORKDIR /app

ARG USERNAME=user
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# RUN apt-get update && \
#     apt-get install -y python3 python3-pip && \
#     rm -rf /var/lib/apt/lists/*

RUN groupadd --gid $USER_GID $USERNAME \
  && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

USER $USERNAME
ENV PATH="/home/user/.local/bin:$PATH"


ENV CUDA_LAUNCH_BLOCKING=1
ENV TORCH_USE_CUDA_DSA=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=$USER_UID:$USER_GID main.py .
COPY --chown=$USER_UID:$USER_GID . /app


# COPY . /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

