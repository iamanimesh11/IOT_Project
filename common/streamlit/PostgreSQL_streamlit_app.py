import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import plotly.express as px

# Database connection details

def is_docker():
    try:
        with open('/proc/1/cgroup', 'r') as f:
            if 'docker' in f.read():
                return True
    except FileNotFoundError:
        return False
    return False


DB_HOST = "postgres" if is_docker() else "localhost"  # Inside Docker use service name, else use localhost
DB_PORT = "5432"
DB_NAME = "iot_project"
DB_USER = "postgres"
DB_PASS = "animesh11"

POSTGRES_CONTAINER_NAME = "postgres"

def check_postgres_connection():
        DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        try:
            engine = create_engine(DB_URL)
            
            connection = engine.connect()
            connection.close()
            return True,engine
        except SQLAlchemyError:
            return False,str(SQLAlchemyError)

def load_data(schema, table,engine):
        query = f'SELECT * FROM "{schema}"."{table}" LIMIT 100;'
        return pd.read_sql(query, engine)
        

def count_rows(schema, table,engine):
        query = f'SELECT Count(*) FROM "{schema}"."{table}";'
        return pd.read_sql(query, engine)
st.write(check_postgres_connection())

def main():
    # running_containers = get_running_containers()
    # if not any(POSTGRES_CONTAINER_NAME in container[1] for container in running_containers):
        # st.error(f"❌ PostgreSQL container `{POSTGRES_CONTAINER_NAME}` is not running. Start your Docker container.")
        # if running_containers:
            # st.write("### 🔥 Running Docker Containers")
            # st.dataframe(pd.DataFrame(running_containers, columns=["Container ID", "Name", "Status"]))
        # st.stop()
    
    # Database connection
    DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    try:
        engine = create_engine(DB_URL)
        connection = engine.connect()
        connection.close()
        db_connected = True
    except SQLAlchemyError:
        db_connected = False

    if not db_connected:
        st.error("❌ Unable to connect to the database. Check your container status.")
        st.stop()

    st.title("📊 PostgreSQL Database")

    def get_schemas():
        query = "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog', 'information_schema');"
        return pd.read_sql(query, engine)["schema_name"].tolist()

    def get_tables(schema):
        query = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema}';"
        return pd.read_sql(query, engine)["table_name"].tolist()
    
  
    schemas = get_schemas()
    selected_schema = st.selectbox("🗂 Select Schema", schemas)

    if selected_schema:
        tables = get_tables(selected_schema)
        selected_table = st.selectbox("📋 Select Table", tables)

        if st.button("🔄 Fetch Data"):
            if selected_table:
                data = load_data(selected_schema, selected_table,engine)
                c =count_rows(selected_schema,selected_table,engine)
                st.write(f"length of data is : {c}")
                st.dataframe(data)
                csv = data.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", data=csv, file_name=f"{selected_table}.csv", mime="text/csv")

                if 'recorded_at' in data.columns and selected_table=="traffic_data":
                    data['recorded_at'] = pd.to_datetime(data['recorded_at'])
                    fig = px.line(data, x="recorded_at", y="current_speed", title="Current Speed Over Time")
                    st.plotly_chart(fig)

    custom_checkbox=st.checkbox("🔍 Custom SQL Query")
    if custom_checkbox:
        custom_query = st.text_area("Enter your SQL query:", height=200)

        if st.button("Execute Query"):
            if custom_query:
                try:
                    with engine.connect() as connection:
                        query = text(custom_query.strip())

                        # Check if it's a SELECT query
                        if custom_query.strip().lower().startswith("select"):
                            result = pd.read_sql(query, connection)
                            st.dataframe(result)

                            # Provide CSV download option
                            csv = result.to_csv(index=False).encode("utf-8")
                            st.download_button("⬇️ Download CSV", data=csv, file_name="query_result.csv", mime="text/csv")
                        else:
                            connection.execute(query)
                            connection.commit()
                            st.success("✅ Query executed successfully!")

                except SQLAlchemyError as e:
                    st.error(f"❌ SQL Error: {e}")
                except Exception as e:
                    st.error(f"❌ Unexpected Error: {e}")
        else:
            st.warning("⚠️ Please enter a SQL query.")

if __name__ == "__main__":
    main()
