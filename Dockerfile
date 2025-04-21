# Use an official Python image
FROM python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy only the Python scripts
COPY python_Files/ .

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose necessary ports (only if the script runs a web UI like Streamlit)
EXPOSE 8501

# Run the Python script
CMD ["python", "your_logging_script.py"]
