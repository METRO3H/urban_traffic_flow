
# Using python:3.13.3-slim as base image
FROM python:3.13.3-alpine

# Setting the working directory in the container to /app
WORKDIR /app

# Copying the requirements.txt file to the container
COPY . .

# Installing the required dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Run scraper.py when the container launches
CMD ["python", "scraper.py"]