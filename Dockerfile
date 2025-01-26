FROM python:3.11-slim 

# Make directory for the app
RUN mkdir /opt/app

# Set the working directory in the container
WORKDIR /opt/app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the project files to the container
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8000

# Set environment variables (optional, but useful for production)
ENV PYTHONUNBUFFERED=1

# Run the FastAPI application with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
