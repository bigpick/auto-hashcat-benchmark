FROM nvidia/cuda:12.9.1-devel-ubuntu24.04

ARG HASHCAT_VERSION=v7.1.2

ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

WORKDIR /root/

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        git make build-essential \
        libjudy-dev libpcre3-dev libmhash-dev \
        jq bc \
    && rm -rf /var/lib/apt/lists/*

# Remove CUDA OpenCL package (upstream hashcat practice)
RUN removeopencl=$(dpkg --list | awk '/opencl/ && $2 ~ /^cuda-opencl-/ {print $2; exit}') && \
    if [ -n "$removeopencl" ]; then apt-get remove -y $removeopencl; fi && \
    rm -rf /var/lib/apt/lists/*

# Build hashcat from source with portable flags.
# -march=x86-64 ensures the binary runs on any x86-64 host (no AVX/SSE4 dependency).
RUN git clone https://github.com/hashcat/hashcat.git /root/hashcat && \
    cd /root/hashcat && \
    git checkout ${HASHCAT_VERSION} && \
    git submodule update --init && \
    make -j$(nproc) BUILD_MODE=cross && \
    make install && \
    rm -rf /root/hashcat/.git

RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
