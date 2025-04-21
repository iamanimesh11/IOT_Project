import streamlit as st
import os
import json
import requests
import time
import threading
import sys
import requests 
from streamlit_option_menu import option_menu
from streamlit_autorefresh import st_autorefresh

# if "just_started" not in st.session_state:
    # st.session_state.just_started = True
    # st.rerun()


st.set_page_config(page_title="ETL Helper Streamlit App",page_icon="🌐",layout="wide")  # Optional: Gives more screen real estate
# # === Clear cache ===
# # === Run this block ONLY once to clear cache and rerun ===
# if "cache_cleared" not in st.session_state:
    # st.cache_data.clear()
    # st.cache_resource.clear()
    # st.session_state.cache_cleared = True
    # st.rerun()

from kafka_manager_Streamlit import main as script1_app
from PostgreSQL_streamlit_app import main as postgres_app
from Docker_container_Status import main as docker_app
from ETL_walkthrough_Streamlit import main as steps_main
#from loki_streamlit import main as  loki_main
from lokii_streamlit import main as  loki_main   

def is_inside_docker():
    try:
        with open("/proc/1/cgroup", "rt") as f:
            return "docker" in f.read()
    except Exception:
        return False

def shutdown_app():
    if is_inside_docker():
        os.system("kill 1")
    else:
        os._exit(0)

if is_inside_docker():
    SHARED_PATH = "/shared"
else:
    SHARED_PATH = os.path.join(os.path.dirname(os.path.dirname(os.getcwd())), "shared")

webhook_config_cache=None
# === Constants ===
FORM_TIMEOUT = 120  # 2 minutes
total_time=60
INFO_FLAG = os.path.join(SHARED_PATH, "info_collected.flag")
USER_INFO = os.path.join(SHARED_PATH, "user_info.json")

def get_discord_URL(retries=3, backoff_factor=1.5, delay=1):
    global webhook_config_cache
    if webhook_config_cache:
        return webhook_config_cache

    url = "https://realtimeetlroadtrafficweather.vercel.app/get_discord_URL"

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers={"X-Docker-Request": "true"},timeout=5)  # Add timeout to prevent hanging
            if response.status_code == 200:
                webhook_config = response.json()
                webhook_config_cache = webhook_config
                return webhook_config_cache
            else:
                print(f"[Attempt {attempt}] Failed with status code: {response.status_code}")
        except requests.RequestException as e:
             print(f"[Attempt {attempt}] Request failed: {e}")

        # Wait before retrying (exponential backoff)
        sleep_time = delay * (backoff_factor ** (attempt - 1))
        print(f"Retrying in {sleep_time:.1f} seconds...")
        time.sleep(sleep_time)

    raise RuntimeError("Failed to fetch Firebase config after multiple attempts")

if "webhook_url" not in st.session_state:
    DISCORD_WEBHOOK_URL = get_discord_URL()
    st.session_state.webhook_url = DISCORD_WEBHOOK_URL
else:
    DISCORD_WEBHOOK_URL = st.session_state.webhook_url


# === Setup shutdown timer ===
if "app_start_time" not in st.session_state:
    st.session_state.app_start_time = time.time()

def shutdown_container():
    print(f"🧨 Shutting down container after {str(FORM_TIMEOUT)} minutes...")
    sys.exit("💀 Time's up. Container shutting down.")

if "shutdown_started" not in st.session_state:
    threading.Timer(FORM_TIMEOUT, shutdown_container).start()
    st.session_state.shutdown_started = True

# === User Info Check ===
def check_user_info():
    return os.path.exists(INFO_FLAG)



def send_container_started_alert():
    embed = {
        "title": "🚀 Container Accessed",
        "color": 3066993,
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
    except Exception as e:
        print(f"Failed to send container start alert: {e}")

if not os.path.exists("/shared/start_logged.txt"):
    send_container_started_alert()
    with open("/shared/start_logged.txt", "w") as f:
        f.write("started")

def send_skip_alert_to_discord():
    embed = {
        "title": "⏭️ Info Form Skipped",
        "color": 15158332,
        "description": "Someone **ran the container** and skipped the info form.",
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
    except Exception as e:
        st.warning(f"⚠️ Could not send to Discord: {e}")

def send_to_discord(name, contact, role, purpose, message):
    embed = {
        "title": "🚀 Portfolio Visitor Info",
        "color": 3447003,
        "fields": [
            {"name": "🧑 Name", "value": name, "inline": True},
            {"name": "📫 Contact", "value": contact if contact else "Not provided", "inline": True},
            {"name": "🎯 Role / Interest", "value": role, "inline": False},
            {"name": "📝 Purpose", "value": purpose, "inline": False},
        ]
    }
    if message:
        embed["fields"].append({"name": "💬 Feedback / Comment", "value": message, "inline": False})

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
        if response.status_code != 204:
            st.warning(f"⚠️ Discord webhook failed with status {response.status_code}")
    except Exception as e:
        st.warning(f"⚠️ Could not send to Discord: {e}")

def run_timer(total_time, progress_bar_placeholder, status_placeholder):
    for seconds_left in range(total_time, -1, -1):
        progress = (total_time - seconds_left) / total_time
        st.write(f"Timer thread: Progress = {progress}, Seconds Left = {seconds_left}")  # Debugging

        progress_bar_placeholder.progress(progress)
        status_placeholder.markdown(f"⏳ Time left: **{seconds_left}** seconds")
        time.sleep(1)
    status_placeholder.markdown("✅ Time's up!")
    
def show_user_form():
    time_elapsed = time.time() - st.session_state.app_start_time
    time_left = int(FORM_TIMEOUT - time_elapsed)
    progress = time_elapsed / FORM_TIMEOUT

    progress_bar = st.empty()  # Initialize progress bar here
    status_text = st.empty()  # Initialize status text here

    # Create a thread for the timer
    timer_thread = threading.Thread(target=run_timer, args=(FORM_TIMEOUT, progress_bar, status_text))
    timer_thread.daemon = True  # Allow the main script to exit even if the thread is running
    timer_thread.start()    


    if time_left <= 0:
        st.warning("⏰ Time's up! The form timed out.\n\nGo ahead and re-run the image to start fresh 😊")
        time.sleep(2)  # Let user see the message before shutdown
        try:
            shutdown_app()
        except Exception as e:
            st.error(f"❌ Failed to kill container: {e}")
            st.stop()
    
    else:
        # Show countdown and progress bar
        progress = min(time_left / FORM_TIMEOUT, 1.0)
        progress_bar = st.progress(progress)
        countdown_text = st.empty()
        countdown_text.markdown(f"⏳ Time left: **{time_left} seconds**")
        mins = time_left // 60
        secs = time_left % 60
        st.markdown(
            f"""
            <div style="background-color: #dceefb; padding: 12px 18px; border-left: 6px solid #1e88e5; border-radius: 6px; color: #0d47a1;">
                🕒 <strong>The data pipeline's heartbeat is steady.</strong><br>
                You’ve got {mins}m {secs}s to submit your input before the system cycles.
            </div>
            """,
            unsafe_allow_html=True
        )

    st.title("🚪 Knock knock...")
    st.markdown("---")
    st.markdown("<div style='text-align: center;'>Made with ❤️ by <strong>Animesh</strong></div>", unsafe_allow_html=True)
    st.markdown("Before jumping into the app, I'd love to know a bit about who's visiting. \
                 Whether you're a recruiter, dev, or just curious, this helps me improve and connect. 🚀")

    # 1️⃣ Name + Contact side-by-side
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your Name")

    with col2:
        contact = st.text_input("Email or LinkedIn (optional)")

    # 2️⃣ Role + Purpose side-by-side
    col3, col4 = st.columns(2)
    with col3:
        role = st.selectbox("You're here as a...", ["Select !","Recruiter", "Developer", "Friend", "Just Curious 👀", "Other"])

    with col4:
        purpose = st.selectbox("What brings you here?", ["Select !","Hiring", "Checking out portfolio", "Collaboration", "Giving Feedback", "Other"])

    # 3️⃣ Feedback - full width
    message = st.text_area("Anything you'd like to share? (Optional)", height=100)

    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button("Submit"):
            if name:
                os.makedirs("/shared", exist_ok=True)
                with open(USER_INFO, "w") as f:
                    json.dump({
                        "name": name,
                        "contact": contact,
                        "role": role,
                        "purpose": purpose,
                        "message": message
                    }, f)
                with open(INFO_FLAG, "w") as f:
                    f.write("info_collected")

                send_to_discord(name, contact, role, purpose, message)

                return ("🙌 That was kind of you! Thanks for dropping in.\n\n🔁 If the page gets stuck, try a hard refresh when you're ready to explore.", "success")
            else:
                st.error("Please enter your name at minimum.")

    with col2:
        if st.button("Skip for now"):
            os.makedirs("/shared", exist_ok=True)
            with open(USER_INFO, "w") as f:
                json.dump({"skipped": True}, f)
            with open(INFO_FLAG, "w") as f:
                f.write("info_skipped")
            send_skip_alert_to_discord()
            return ("😎 Totally cool — no pressure at all.\n\n🔄 Hard refresh if page stucked and jump right in.", "info")
    time.sleep(1)
    st_autorefresh(interval=2000, key="refresh_5s")

    return None, None

# === Main Routing ===
if  not check_user_info():
    msg, msg_type = show_user_form()
    if msg:
        if msg_type == "success":
            st.success(msg)
            st.toast(msg)
        elif msg_type == "info":
            st.info(msg)
            time.sleep(3)
            st.rerun()
        else:
            st.write(msg)
        st.stop()
    else:
        st.stop()
    st.rerun()
    st_autorefresh(interval=2000,limit=1, key="refresh_5s")



# === Sidebar Navigation ===
# # Sidebar with menu
# page = option_menu(
    # None,
    # ["Steps", "Docker_Containers", "Readme", "flask", "kafka", "postgres"],
    # icons=["list-task", "box", "book", "server", "broadcast", "database"],
    # menu_icon="cast",
    # default_index=0,
    # orientation="horizontal"
# )


# Function to load and display JSON data from a local directory
@st.cache_data(show_spinner="Fetching data ,Hold on..")
def display_json_from_github(name):
    # GitHub raw file URL
    if name =="Airflow Log Analytics":
        github_url="https://raw.githubusercontent.com/iamanimesh11/Real-time-traffic-and-weather-ETL-project-Streamlit-app/refs/heads/main/Airflow%20Log%20Analytics"
        
    else:
        github_url = "https://raw.githubusercontent.com/iamanimesh11/Real-time-traffic-and-weather-ETL-project-Streamlit-app/refs/heads/main/ETL.json"  # Replace with your file URL
    
    # Fetch the file
    response = requests.get(github_url)

    if response.status_code == 200:
        try:
            json_data = response.json()
            # Display the JSON data in the app
            st.write(f"### {name} JSON:")
            st.json(json_data)
        except ValueError as e:
            st.error(f"Error decoding JSON: {e}")
    else:
        st.error(f"Failed to fetch data: {response.status_code} - {response.text}")


# Sidebar with menu
with st.sidebar:
    page = option_menu(
        "Navigation",  # Menu title
        ["ETL Walkthrough", "Docker_Containers", "Readme", "flask", "kafka", "postgres","grafana/loki"],  # Menu items
        icons=["list-task", "box", "book", "server", "broadcast", "database","activity"],  # Icons (optional)
        menu_icon="cast",  # Icon for menu title
        default_index=0,  # Default selected item

    )
   
 
# contact detials
import streamlit as st

st.sidebar.markdown(
    """
### 📬 Contact Me

<div style="display: flex; flex-wrap: wrap; justify-content: space-between;">
    <div style="width: 50%; margin-bottom: 10px;">
        <a href="mailto:iamanimesh11june@gmail.com" target="_blank" style="text-decoration: none; display: flex; align-items: center;">
            <img src="https://img.icons8.com/color/24/gmail-new.png" style="vertical-align:middle; margin-right: 8px;"/>
            <span>Email</span>
        </a>
    </div>
    <div style="width: 50%; margin-bottom: 10px;">
        <a href="https://www.linkedin.com/in/animesh-singh11/" target="_blank" style="text-decoration: none; display: flex; align-items: center;">
            <img src="https://img.icons8.com/color/24/linkedin.png" style="vertical-align:middle; margin-right: 8px;"/>
            <span>LinkedIn</span>
        </a>
    </div>
    <div style="width: 50%;">
        <a href="https://github.com/iamanimesh11" target="_blank" style="text-decoration: none; display: flex; align-items: center;">
            <img src="https://img.icons8.com/material-outlined/24/000000/github.png" style="vertical-align:middle; margin-right: 8px;"/>
            <span>GitHub</span>
        </a>
    </div>
    <div style="width: 50%;">
        <a href="https://realtimeetlroadtrafficweather.vercel.app/feedback" target="_blank" style="text-decoration: none; display: flex; align-items: center;">
            <img src="https://cdnjs.cloudflare.com/ajax/libs/ionicons/2.0.1/png/512/earth.png" style="vertical-align:middle; width:24px; margin-right: 8px;"/>
            <span>Feedback</span>
        </a>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


if page == "ETL Walkthrough":
    # Sidebar with instructions
#    st.header("⚙️ System Prerequisite")
    steps_main()

elif page == "Docker_Containers":
    # Sidebar with instructions
    st.sidebar.header("⚙️ System Prerequisite")
    st.sidebar.markdown("""
    **Make sure you've enabled Telnet on Windows:**

    1. Press `Windows + R`
    2. Type `optionalfeatures` → Enter
    3. Enable **Telnet Client** and let it install

    ✅ Required for certain network checks
    """)
    docker_app()

elif page == "flask":
    st.title("🧩  Flask App")

    flask_url = "https://realtimeetlroadtrafficweather.vercel.app/"

    with st.spinner("Hold on,Loading ..."):
        # Add a small delay to show the spinner (optional but helpful for effect)
        import time
        time.sleep(3)  # Simulate loading

        st.markdown(f"""
        <style>
            .responsive-iframe {{
                position: relative;
                width: 100%;
                height: 90vh;
                border: none;
            }}
        </style>

        <iframe src="{flask_url}" class="responsive-iframe"></iframe>
        """, unsafe_allow_html=True)


elif page == "Readme":
    st.title("📘 GitHub README Viewer")

    @st.cache_data(ttl=3600)  # Cache for 1 hour (3600 seconds)
    def load_readme(raw_url):
        response = requests.get(raw_url)
        if response.status_code == 200:
            return response.text
        else:
            return f"Failed to load README. Status code: {response.status_code}"

    raw_url = "https://raw.githubusercontent.com/iamanimesh11/Real-Time-ETL-of-Road-Traffic-Weather-Monitoring./refs/heads/main/README.md"
    readme_md = load_readme(raw_url)
    st.markdown(readme_md, unsafe_allow_html=True)

elif page == "kafka":
    script1_app()

elif page == "postgres":
    postgres_app()

elif page =="grafana/loki":
    with st.spinner("loading"):
        time.sleep(5)
        tab1,tab2,tab3,tab4=st.tabs(["Need Guide ?","Airflow Log Analytics","ETL dashboard","loki logs"])
        
        with tab2:
            st.info("Copy the JSON code below and use in Import Dashoard in Grafana.")
            display_json_from_github("Airflow Log Analytics")
        with tab3:
            st.info("Copy the JSON code below and use in Import Dashoard in Grafana.")
            display_json_from_github("ETL dashboard")

        with tab1:

            # Page Title
            st.title("📊 How to view Grafana dashbaords")
            
            # Step 1: Ensure Grafana Container is Running
            st.subheader("1️⃣ Make Sure Grafana Container is Running")
            st.markdown("""
                To verify that your Grafana container is running, check the **Docker Containers** section:

                1. Open your terminal and run:
                   ```bash
                   docker ps
                   ```
                2. Ensure that the **Grafana** container is listed as running (it should show the image name `grafana/grafana:latest` and be bound to port 3000).
                3. If the Grafana container is not running, start it with the following command:
                   ```bash
                   docker run -d -p 3000:3000 --name=grafana --link loki:localhost grafana/grafana:latest
                   ```
                **Note:** Ensure that your **Loki container** is also running. You can verify this by running:
                ```bash
                docker ps
                ```
                And to start it (if needed):
                ```bash
                docker run -d -p 3100:3100 --name=loki grafana/loki:latest
                ```
            """)

            # Step 2: Access Grafana Dashboard
            
            st.subheader("2️⃣ Access Grafana on Localhost")
            st.markdown("""
                Open your browser and navigate to **http://localhost:3000**.
                - **Username:** `admin`
                - **Password:** `animesh16` (you can change this after the first login)
                - Login to Grafana to get started with your dashboards.
            """)
            st.image("images/Grafana_guide_1.png", caption="Grafana container running", width=300)

            # Step 3: Set Up Data Source (Loki)
            st.warning("Note: Although ,Dashboard must be listed under dashboards section if not then please follow the below approach: ")
            st.subheader("3️⃣ Set Up Data Source (Loki)")
            st.markdown("""
                1. In Grafana, click on the **Gear icon** (⚙️) on the left sidebar and go to **Data Sources**.
                2. Click on **Add Data Source** and select **Loki** from the list.
                3. For the URL, enter:
                   ```
                   http://localhost:3100
                   ```
                4. Click **Save & Test** to ensure that Grafana is successfully connected to Loki.
            """)
            st.image("images/Grafana_guide_2.png", caption="Grafana container running", width=300)
            st.image("images/Grafana_guide_3.png", caption="Grafana container running", width=300)


            # Step 4: Import the Pre-configured Dashboard JSON
            st.subheader("4️⃣ Import the Dashboard JSON")
            st.markdown("""
                1. After clicking **Import**, paste the **ETL dashboard JSON** in the provided field.
                2. Make sure that **Loki** is selected as the **Data Source**.
                3. Click **Import** to add the dashboard to Grafana.
                4. You should now see your logs and data visualized in the imported dashboard!
            """)
            st.info("Similarly import Dashbaord -Airflow Log Analytics")
            # Troubleshooting
            st.subheader("5️⃣ Troubleshooting Common Errors")
            st.markdown("""
                - **Error: Cannot connect to Loki**:
                    - Ensure Loki is running and accessible at `localhost:3100`. Restart it if necessary.
                - **Error: Dashboard Import Failed**:
                    - Verify that  Loki data source is properly set up.
            """)

            # Conclusion
            st.markdown("""
                Once you’ve followed these steps, you should be able to view your logs and metrics on Grafana.
                You can interact with the dashboard, customize it, and analyze the data in real-time.
            """)

        with tab4:
               loki_main()

