FROM python:3.13-slim

# Install Chrome and dependencies using modern method
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    software-properties-common \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome-keyring.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create output directory
RUN mkdir -p output

# Run the server
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
