FROM nvidia/cuda:12.9.1-devel-ubuntu24.04

ARG HASHCAT_VERSION=v7.1.2

ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

WORKDIR /root/

# System packages (based on upstream hashcat runtime image, minus pyenv/rust
# which are only needed for Rust bridge plugin development, not benchmarking)
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
        curl wget unzip tar p7zip-full \
        libjudy-dev libpcre3-dev libmhash-dev \
        git make build-essential \
        jq bc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Remove CUDA OpenCL package (upstream hashcat practice)
RUN removeopencl=$(dpkg --list | awk '/opencl/ && $2 ~ /^cuda-opencl-/ {print $2; exit}') && \
    if [ -n "$removeopencl" ]; then apt-get remove -y $removeopencl; fi && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install hashcat: use pre-built release for tagged versions, build from source otherwise.
# Only versions matching vX.Y.Z or X.Y.Z get the download path.
# Anything else (branch names, commit SHAs) builds from source.
RUN CLEAN_VERSION=$(echo "${HASHCAT_VERSION}" | sed 's/^v//') && \
    if echo "$CLEAN_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then \
        echo "Downloading pre-built hashcat ${CLEAN_VERSION}..." && \
        curl -fSL "https://hashcat.net/files/hashcat-${CLEAN_VERSION}.7z" -o hashcat.7z && \
        7z x hashcat.7z && \
        mv hashcat-${CLEAN_VERSION} /root/hashcat && \
        rm hashcat.7z; \
    else \
        echo "Building hashcat from source (ref: ${HASHCAT_VERSION})..." && \
        git clone https://github.com/hashcat/hashcat.git /root/hashcat-src && \
        cd /root/hashcat-src && \
        git checkout ${HASHCAT_VERSION} && \
        git submodule update --init && \
        make -j$(nproc) && \
        make install && \
        mkdir -p /root/hashcat && \
        cp -r /root/hashcat-src/* /root/hashcat/ && \
        rm -rf /root/hashcat-src; \
    fi

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
