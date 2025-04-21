# Use an official Python image as a base
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit app script
COPY . .

# Expose the Streamlit default port
EXPOSE 8501

# Run the Streamlit app on container startup
CMD ["streamlit", "run", "main_Streamlit.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.runOnSave=true"]
