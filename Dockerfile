# Dockerfile for HDR Emoji Maker on Render

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including ImageMagick
RUN apt-get update && apt-get install -y \
    imagemagick \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify ImageMagick installation
RUN magick -version || { echo 'ImageMagick installation failed'; exit 1; }

# Copy the application code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables
ENV PORT=5000

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"] 