# MIT License

# Copyright (c) 2026 Jaime Álvarez Díaz
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


FROM ubuntu:24.04 AS pyspin-installer

# Change working directory
WORKDIR /tmp/

# Copy installation files
COPY packages/pyspin-4.4.tar.gz /tmp/packages/

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Python
    python3.12 \
    python3.12-venv \
    python3-pip \
    # Create Python symbolic links
    && ln -s /bin/python3.12 /bin/python \
    && ln -s /bin/python3.12 /bin/py \
    # Create Python virtual environment
    && python -m venv /app/.venv \
    && /app/.venv/bin/python3 -m pip install --no-cache-dir --upgrade pip \
    && /app/.venv/bin/python3 -m pip install --no-cache-dir "numpy" \
    # && /app/.venv/bin/python3 -m pip install git+https://github.com/jaimead7/SpinCam.git@main \
    && /app/.venv/bin/python3 -m pip install --no-cache-dir jaimead7-spincam[headless] \
    # Install PySpin
    && tar -xzf packages/pyspin-4.4.tar.gz --wildcards '*.whl' \
    && /app/.venv/bin/python3 -m pip install --no-cache-dir /tmp/*.whl \
    # Clear
    && rm -rf /tmp/* \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean


FROM ubuntu:24.04 AS spinnaker-installer

# Change working directory
WORKDIR /tmp/

# Copy installation files
COPY packages/spinnaker-sdk-4.4.tar.gz /tmp/packages/
COPY tools/*.sh /tmp/tools/

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Spinnaker SDK dependency
    libusb-1.0-0 \
    # Spinnaker SDK dependency libgomp.so.1
    libgomp1 \
    # Spinnaker SDK dependency libswscale.so.7
    libswscale7 \
    # Spinnaker SDK dependency libavcodec.so.60
    libavcodec-extra60 \
    # Spinnaker SDK dependency libavformat.so.60
    libavformat-extra60 \
    # Install Spinnaker
    && sh tools/spinnaker_silent_install.sh packages/spinnaker-sdk-4.4.tar.gz \
    # Clear
    && rm -rf /tmp/* \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean


FROM scratch AS builder

# Copy spinnaker final stage
COPY --from=spinnaker-installer / /

# Copy python environment
COPY --from=pyspin-installer /app/.venv /app/.venv

# Install python
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Python
    python3.12 \
    && ln -s /bin/python3.12 /bin/python \
    && ln -s /bin/python3.12 /bin/py \
    # Clear
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Update linker for Spinnaker
RUN ldconfig 2>/dev/null || true

# Change working directory
WORKDIR /app/

# Copy application files
COPY --exclude="packages/" --exclude="tools/" . .


FROM scratch AS production

# Copy builder final stage
COPY --from=builder / /

# Change working directory
WORKDIR /app/

# Copy project files
COPY . .

# Set Python environment path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Container command
CMD ["python3", "./main.py"]
