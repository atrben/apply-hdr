# Dockerfile for HDR Emoji Maker on Render

# Use a full Python runtime based on Debian Bullseye for better dependency support
FROM python:3.9-bullseye

# Set working directory
WORKDIR /app

# Install build dependencies for ImageMagick
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    libgif-dev \
    libx11-dev \
    libxml2-dev \
    libfreetype6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download and build ImageMagick from source
RUN wget https://download.imagemagick.org/ImageMagick/download/ImageMagick.tar.gz && \
    tar -xzf ImageMagick.tar.gz && \
    cd ImageMagick-* && \
    ./configure --prefix=/usr/local && \
    make && \
    make install && \
    ldconfig /usr/local/lib && \
    cd .. && \
    rm -rf ImageMagick*

# Debug: Check for ImageMagick binaries in common locations
RUN echo 'Checking /usr/bin for ImageMagick binaries:' && ls -l /usr/bin/*magick* /usr/bin/convert 2>/dev/null || echo 'No ImageMagick binaries found in /usr/bin'
RUN echo 'Checking /usr/local/bin for ImageMagick binaries:' && ls -l /usr/local/bin/*magick* /usr/local/bin/convert 2>/dev/null || echo 'No ImageMagick binaries found in /usr/local/bin'

# Verify ImageMagick installation by checking for the binary
RUN which convert && convert -version || { echo 'ImageMagick installation failed, convert not found'; exit 1; }
RUN if [ -f /usr/local/bin/magick ]; then /usr/local/bin/magick -version; else echo 'magick binary not found, trying convert'; convert -version || { echo 'ImageMagick installation failed'; exit 1; }; fi

# Additional step: Ensure ImageMagick policy allows operations
RUN if [ -f /etc/ImageMagick-6/policy.xml ]; then sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<policy domain="coder" rights="read|write" pattern="PDF" \/>/' /etc/ImageMagick-6/policy.xml; fi

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