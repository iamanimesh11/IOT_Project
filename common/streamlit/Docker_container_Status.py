import streamlit as st
import requests
import time

from PostgreSQL_streamlit_app import check_postgres_connection
from network_utils import check_connection as check_connection


postgresql_status="true"


def main():


    if "first_load" not in st.session_state:
        st.session_state.first_load = True

   
    
    SERVICES = {
        "Airflow Webserver": {
            "url": "http://airflow:8080/health",
            "description": "Airflow UI for monitoring and managing workflows.",
            "logo": "https://icon.icepanel.io/Technology/svg/Apache-Airflow.svg",
            "host": "airflow-webserver",
            "port": 8080,
        },
        "Zookeeper": {
            "url": "http://zookeeper:2181",
            "description": "Centralized service for maintaining configuration information.",
            "logo": "https://svn.apache.org/repos/asf/zookeeper/logo/zookeeper.jpg",
            "host": "zookeeper",
            "port": 2181,
        },
        "kafka": {
            "url": "http://kafka:9092",
            "description": "Distributed event streaming platform.",
            "logo": "https://kafka.apache.org/images/apache-kafka.png",
            "host": "kafka",
            "port": 9092
        },
        "Grafana": {
            "url": "http://grafana:3000",
            "description": "Data visualization and monitoring tool.",
            "logo": "https://www.skedler.com/blog/wp-content/uploads/2021/08/grafana-logo-768x384.png",
            "host": "grafana",
            "port": 3000,
        },
        "Loki": {
            "url": "http://loki:3100/ready",
            "description": "Log aggregation system.",
            "logo": "https://image.pngaaa.com/608/4821608-middle.png",
            "host": "loki",
            "port": 3100
        },
        "Postgres": {
            "url": postgresql_status,
            "description": "Open-source relational database.",
            "logo": "https://www.logo.wine/a/logo/PostgreSQL/PostgreSQL-Logo.wine.svg",
            "host": "postgres",
            "port": 5432
        },
    }
    # Setup session state
    for service in SERVICES:
        st.session_state.setdefault(f"{service}_status", "🔘 Not Checked")
        st.session_state.setdefault(f"{service}_color", "gray")
        st.session_state.setdefault(f"{service}_last_checked", "Never")
        st.session_state.setdefault(f"{service}_response", "")

    st.markdown(f"""
        <style>
            div.card-container {{
                background-color: black;
                border-radius: 15px;
                padding: 20px;
                margin: 10px;
                box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
                height: 220px; /* Increased height to accommodate logo and more content */
                display: flex;
                flex-direction: column;
                align-items: center; /* Center items horizontally */
            }}
            div.card-logo {{
                width: 150px; /* Adjust logo size as needed */
                height: 60px;
                margin-bottom: 10px;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            div.card-logo img {{
                max-width: 100%;
                max-height: 100%;
                border-radius: 10px; /* Optional: round the corners of the logo */
            }}
            div.card-title {{
                font-size: 18px;
                font-weight: 600;
                text-align: center;
                color: white;
                margin-bottom: 5px;
            }}
            div.card-description {{
                font-size: 12px;
                color: white;
                text-align: center;
                margin-bottom: 10px;
                overflow: hidden; /* To handle longer descriptions */
            }}
            div.card-status-container {{
                text-align: center;
                margin-top: auto; /* Push status to the bottom */
            }}
            div.card-status {{
                font-size: 18px;
            }}
            div.card-last-checked {{
                font-size: 10px;
                color: #777;
                text-align: center;
                margin-top: 3px;
            }}
            div.card-response {{
                font-size: 10px;
                color: white;
                overflow: auto;
                max-height: 60px;
                margin-top: 5px;
                background-color: black;
                padding: 5px;
                border-radius: 5px;
            }}
            div.card-guide {{
                font-size: 11px;
                color: orange;
                text-align: left;
                margin-top: 5px;
            }}
        </style>
    """, unsafe_allow_html=True)

    # Dashboard title
    st.title("🐳 Docker Containers & Service Status")
    st.markdown("Monitor the health of Docker containers and their internal services.")
    st.markdown("---")

    # Calculate the number of columns needed
    num_services = len(SERVICES)
    num_cols = (num_services + 2) // 3  # Ensure at most 3 cards per row

    # Create rows of columns
    for i in range(num_cols):
        cols = st.columns(3)
        for j in range(3):
            index = i * 3 + j
            if index < num_services:
                name = list(SERVICES.keys())[index]
                service_info = SERVICES[name]
                url = service_info["url"]
                description = service_info["description"]
                logo_url = service_info["logo"]
                host = service_info["host"]
                port = service_info["port"]
                restart_command = service_info.get("restart_command", f"docker restart {host}") # Example restart command

                with cols[j]:
                    with st.container():
                        st.markdown(f'<div class="card-container"><div class="card-logo"><img src="{logo_url}" alt="{name} Logo"></div><div class="card-title">{name}</div><div class="card-description">{description}</div>', unsafe_allow_html=True)

                        button_clicked = st.button("Check Status", key=f"{name}_btn")

                        if st.session_state.first_load or button_clicked:
                            with st.spinner(f"Checking {name}..."):
                                time.sleep(3)
                                try:
                                    start_time = time.time()
                                    result = check_connection(host, port)
                                    end_time = time.time()
                                    response_time = f"{(end_time - start_time):.2f}s"
                                    st.session_state[f"{name}_last_checked"] = time.strftime("%Y-%m-%d %H:%M:%S")

                                    if result == True:
                                        st.session_state[f"{name}_status"] = "✅ Running"
                                        st.session_state[f"{name}_color"] = "green"

                                    else:
                                        st.session_state[f"{name}_status"] = "❌ Down"
                                        st.session_state[f"{name}_response"] = result
                                        st.session_state[f"{name}_color"] = "red"
                                except requests.exceptions.RequestException as e:
                                    st.session_state[f"{name}_status"] = "❌ Error"
                                    st.session_state[f"{name}_color"] = "red"
                                    st.session_state[f"{name}_last_checked"] = time.strftime("%Y-%m-%d %H:%M:%S")
                                    st.session_state[f"{name}_response"] = f"Error: {e}"
                                except Exception as e:
                                    st.session_state[f"{name}_status"] = "❌ Error"
                                    st.session_state[f"{name}_color"] = "red"
                                    st.session_state[f"{name}_last_checked"] = time.strftime("%Y-%m-%d %H:%M:%S")
                                    st.session_state[f"{name}_response"] = f"An unexpected error occurred: {e}"

                        st.markdown(f'<div class="card-status-container">', unsafe_allow_html=True)
                        status = st.session_state[f"{name}_status"]
                        color = st.session_state[f"{name}_color"]
                        
                        st.markdown(
                            f'<div class="card-status" style="color:{color}">{status}</div>',
                            unsafe_allow_html=True
                        )

                        st.markdown(
                            f'<div class="card-last-checked">Last Checked: {st.session_state[f"{name}_last_checked"]}</div>',
                            unsafe_allow_html=True
                        )
                        if status == "❌ Down" or status == "❌ Error":
                            st.markdown(f'<div class="card-guide">Run: <code>{restart_command}</code></div>', unsafe_allow_html=True)
                            
                        if st.session_state[f"{name}_response"]:
                            st.markdown(f'<div class="card-response">{st.session_state[f"{name}_response"]}</div>', unsafe_allow_html=True)

                        st.markdown(f'</div>', unsafe_allow_html=True) # End status container

                        st.markdown(f'</div>', unsafe_allow_html=True)
                        

    st.session_state.first_load = False

if __name__ == "__main__":
    main()