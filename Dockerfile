# Dockerfile
FROM python:3.10.15-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=flask_app.py
ENV FLASK_ENV=production

# We'll use a shell script to manage multiple processes
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]