FROM python:3.11-slim

WORKDIR /app

# Install build tools for libpostal
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    autoconf \
    automake \
    libtool \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Build and install libpostal
RUN git clone https://github.com/openvenues/libpostal /tmp/libpostal && \
    cd /tmp/libpostal && \
    ./bootstrap.sh && \
    ./configure --datadir=/usr/share/libpostal && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    rm -rf /tmp/libpostal

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code and data
COPY address_classification_dataset/ address_classification_dataset/
COPY src/ src/

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
