# Use official Python 3.11 image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Upgrade pip, setuptools, wheel
RUN pip install --upgrade pip setuptools wheel

# Install project dependencies
RUN pip install -r requirements.txt

# Expose the port your app uses (Flask default is 5000)
EXPOSE 5000

# Command to run your app
CMD ["python", "app.py"]