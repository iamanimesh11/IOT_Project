import streamlit as st
import subprocess

# Loki Query URL (update if needed)
LOKI_QUERY_URL = "http://localhost:3100/loki/api/v1/query_range"

from loki_files.loki_request_python import fetch_job_ids, fetch_logs

def main():
        st.title("Loki Logs ")
        st.info("You can query to fetch log sent to loki here also")
        if "log_process" not in st.session_state:
            st.session_state["log_process"] = None


        job_ids=fetch_job_ids()
        selected_job= st.selectbox("select job ids",job_ids) if job_ids else st.sidebar.warning("no job found")


        # Function to start logging
        def start_logging():
            if st.session_state["log_process"] is None:
                st.session_state["log_process"] = subprocess.Popen(["python", "log_sent_to_loki.py"])
                st.success("✅ Logging started!")

        # Function to stop logging
        def stop_logging():
            if st.session_state["log_process"] is not None:
                st.session_state["log_process"].terminate()
                st.session_state["log_process"] = None
                st.warning("🛑 Logging stopped!")

        if selected_job =="python_script":
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Start Sending Logs"):
                    start_logging()
            with col2:
                if st.button("🛑 Stop Logging"):
                    stop_logging()

        # Fetch logs when button is clicked
        if st.button("🔄 Refresh Logs"):
            if not selected_job:
                st.sidebar.warning("Please select a job ID first")

            else:
                logs_df = fetch_logs(selected_job)
                if not logs_df.empty:
                    st.dataframe(logs_df, use_container_width=True)
                else:
                    st.warning("No logs found. Make sure logging is running.")
if __name__ == "__main__":
    main()


