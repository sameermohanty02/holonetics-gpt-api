# Use the official Python 3.9 image as a base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set the environment variable to tell Flask to run in production
ENV FLASK_ENV=production

# Expose the port that the Flask app will run on
EXPOSE 9000

# Command to run the Flask application
CMD ["flask", "run", "--host=0.0.0.0", "--port=9000"]
