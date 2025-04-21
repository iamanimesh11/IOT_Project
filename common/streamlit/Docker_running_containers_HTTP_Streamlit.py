import requests
import streamlit as st

# Define the Docker Remote API URL
DOCKER_API_URL = "http://localhost:2375"

def get_running_containers():
    try:
        # Send GET request to Docker Remote API to get all containers
        response = requests.get(f"{DOCKER_API_URL}/containers/json")
        response.raise_for_status()  # Check for HTTP errors

        # Parse the JSON response
        containers = response.json()

        # Extract container information (ID, Name, and Status)
        container_info = [(container['Id'], container['Names'][0], container['Status']) for container in containers]

        # Show parsed containers in Streamlit
        st.write("Parsed containers:", container_info)

        return container_info

    except requests.exceptions.RequestException as e:
        st.error(f"Error: {str(e)}")
        return []

def get_container_logs(container_id):
    try:
        # Send GET request to Docker Remote API to fetch logs for a specific container
        logs_url = f"{DOCKER_API_URL}/containers/{container_id}/logs?stdout=true&stderr=true"
        response = requests.get(logs_url)
        response.raise_for_status()  # Check for HTTP errors

        # Get the logs as text
        logs = response.text

        return logs

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching logs: {str(e)}")
        return ""

def main():
    # Show list of running containers
    containers = get_running_containers()
    if containers:
        container_names = [container[1] for container in containers]
        selected_container = st.selectbox("Select a container to view logs", container_names)

        # Get the container ID for the selected container
        container_id = next(container[0] for container in containers if container[1] == selected_container)

        # Display logs of the selected container
        if selected_container:
            st.write(f"Fetching logs for container: {selected_container}")
            logs = get_container_logs(container_id)
            
            if logs:
                st.text_area("Container Logs", logs, height=300)

if __name__ == "__main__":
    main()
