# Use an NVIDIA CUDA base image to support GTX 950 (CUDA 11.8 is generally compatible with older cards like Maxwell, but checking PyTorch requirements is key)
# For simplicity, using a standard python image and installing PyTorch with CUDA support.
FROM python:3.10-slim

# Install system dependencies for audio (librosa/soundfile) and git
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt .

# Install PyTorch with CUDA 11.8 (compatible with GTX 950)
RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install other requirements
RUN pip install -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Command to run the backend server (to be implemented e.g., via FastAPI/Flask, here just a placeholder)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
