import streamlit as st
from project_flow import main as data_flow

# --- Step confirmation logic ---
def confirm_step(index):
    st.session_state.confirmed_steps[index] = True
    st.session_state.step = min(st.session_state.step + 1, len(st.session_state.confirmed_steps))
    st.session_state.show_error = False

def reset_step(index):
    st.session_state.confirmed_steps[index] = False
    st.session_state.show_error = True

# --- System Setup Check UI ---
def system_setup_check():
    st.markdown("<h2 style='text-align: center;'>🛠️ System Setup Check</h2>", unsafe_allow_html=True)

    steps = [
        {"title": "Docker", "desc": "docker ps /check Docker_Containers section"},
        {"title": "Airflow", "desc": "localhost:8080"},
        {"title": "Grafana", "desc": "localhost:3000"},
        {"title": "Kafka", "desc": "Kafka + DB"},
        {"title": "loki", "desc": "localhost:3100"},
    ]

    max_cols = 3
    total_steps = st.session_state.step

    for start in range(0, total_steps, max_cols):
        end = min(start + max_cols, total_steps)
        cols = st.columns(max_cols)

        for j, i in enumerate(range(start, end)):
            with cols[j]:
                st.markdown(f"### {steps[i]['title']}")
                st.code(steps[i]['desc'])
                btn_cols = st.columns([1, 1])

                if i < len(steps):
                    
                    if st.session_state.confirmed_steps[i]:
                         with btn_cols[0]:
                             st.button("✅ Confirmed", key=f"confirmed_{i}", disabled=True)
                    else:
                        with btn_cols[0]:
                            st.button(
                                f"✔️ Confirm",
                                key=f"btn_{i}",
                                on_click=confirm_step,
                                args=(i,)
                            )
                        with btn_cols[1]:
                            st.button(
                                "❌ No",
                                key=f"close_{i}",
                                on_click=reset_step,
                                args=(i,)
                            )

    if st.session_state.show_error:
        st.error("❌ Docker containers are not running. Please check the Docker Containers section. If issue persists, try restarting the Docker image.")

    if all(st.session_state.confirmed_steps):
        st.success("🚀 System Ready! Data flow option unlocked.")


def main():
    total_steps = 5

    if "step" not in st.session_state:
        st.session_state.step = 1
    if "confirmed_steps" not in st.session_state:
        st.session_state.confirmed_steps = [False] * 5
    if "show_error" not in st.session_state:
        st.session_state.show_error = False

    selected_page1,selected_page2 = st.tabs(["System Setup Check", "Data Flow"])
    
    with selected_page1:
        # Calculate progress
        confirmed = sum(st.session_state.confirmed_steps)
        progress = confirmed / total_steps
        st.markdown(f"**Progress: {int(progress * 100)}%**")
        st.progress(progress)

        # Display the system setup check content
        with selected_page1:
            system_setup_check()

    # Only show the Data Flow content in the second tab
    with selected_page2:
        data_flow()

if __name__ == "__main__":
    main()
