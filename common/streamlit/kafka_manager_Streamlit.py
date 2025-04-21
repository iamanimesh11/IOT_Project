import streamlit as st
from kafka.admin import KafkaAdminClient, NewTopic, NewPartitions
from kafka.errors import TopicAlreadyExistsError
from kafka import KafkaConsumer, TopicPartition
import json
def get_admin_client():
    return KafkaAdminClient(bootstrap_servers=['kafka:9092'], client_id="kafka_topic_manager")

def create_kafka_topic(admin_client, topic_name, num_partitions, replication_factor):
    try:
        topic = NewTopic(name=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)
        admin_client.create_topics(new_topics=[topic], validate_only=False)
        return f"Topic '{topic_name}' created successfully"
    except TopicAlreadyExistsError:
        return f"Topic '{topic_name}' already exists!"
    except Exception as e:
        return f"Error creating topic: {e}"

def delete_kafka_topic(admin_client, topic_name):
    try:
        admin_client.delete_topics(topics=[topic_name])
        return f"Topic '{topic_name}' deleted successfully!"
    except Exception as e:
        return f"Error deleting topic: {e}"

def describe_kafka_topic(admin_client, topic_name):
    try:
        topics_metadata = admin_client.describe_topics(topics=[topic_name])
        return topics_metadata
    except Exception as e:
        return f"Error describing topic: {e}"

def alter_kafka_topic(admin_client, topic_name, num_partitions):
    try:
        existing_topics = admin_client.list_topics()
        if topic_name not in existing_topics:
            return f"Error: The topic '{topic_name}' does not exist."
        
        topics_metadata = admin_client.describe_topics(topics=[topic_name])
        topic_metadata = next((entry for entry in topics_metadata if entry['topic'] == topic_name), None)
        if not topic_metadata:
            return f"Error: Could not retrieve metadata for topic '{topic_name}'."
        
        current_partition_count = len(topic_metadata['partitions'])
        if num_partitions <= current_partition_count:
            return f"Error: Requested partitions ({num_partitions}) must be greater than the current count ({current_partition_count})."
        
        new_partitions = {topic_name: NewPartitions(total_count=num_partitions)}
        admin_client.create_partitions(new_partitions)
        return f"Topic '{topic_name}' altered to {num_partitions} partitions successfully."
    except Exception as e:
        return f"Error altering topic: {e}"

def list_all_topics(admin_client):
    try:
        return admin_client.list_topics()
    except Exception as e:
        return f"Error listing topics: {e}"

def consume_messages(topic_name,earliest):
    
    consumer = KafkaConsumer(
            topic_name,  # Kafka topic

            bootstrap_servers='kafka:9092',  # Replace with your Kafka server
            auto_offset_reset="earliest" if earliest else "latest",  # Choose based on checkbox
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            enable_auto_commit=False , # Disable auto commit to handle offsets manually
    )


    print("Chat Consumer started. Listening for messages on Partition 0:")
    messages = []
    for message in consumer:
        messages.append(message.value)
        if len(messages) > 10:  # Limit messages displayed
            messages.pop(0)
        yield messages  # Stream data
    # for message in consumer:
        # partition = message.partition
        # data = message.value
        # user=data['user']
        # msg_content=data['message']
        # timestamp=data['timestamp']

        # print(f"{user} : {msg_content}  {timestamp}")
        # save_to_db(user,msg_content,timestamp, partition)
        # consumer.commit()



def main():
    st.title("Kafka Topicss Manager")
    admin_client = get_admin_client()
    
    option = st.selectbox("Choose an operation", ["Create Topic", "Delete Topic", "Alter Topic", "Describe Topic", "List Topics","Consume_messages"])
    
    if option == "Create Topic":
        topic_name = st.text_input("Enter topic name:")
        num_partitions = st.number_input("Enter number of partitions:", min_value=1, step=1)
        replication_factor = st.number_input("Enter replication factor:", min_value=1, step=1)
        if st.button("Create Topic"):
            st.write(create_kafka_topic(admin_client, topic_name, num_partitions, replication_factor))
    
    elif option == "Delete Topic":
        topics = list_all_topics(admin_client)
        topic_name = st.selectbox("Select topic to delete:", topics)
        if st.button("Delete Topic"):
            st.write(delete_kafka_topic(admin_client, topic_name))
    
    elif option == "Alter Topic":
        topics = list_all_topics(admin_client)
        topic_name = st.selectbox("Select topic to alter:", topics)
        num_partitions = st.number_input("Enter new number of partitions:", min_value=1, step=1)
        if st.button("Alter Topic"):
            st.write(alter_kafka_topic(admin_client, topic_name, num_partitions))
    
    elif option == "Describe Topic":
        topics = list_all_topics(admin_client)
        topic_name = st.selectbox("Select topic to describe:", topics)
        if st.button("Describe Topic"):
            st.json(describe_kafka_topic(admin_client, topic_name))
    
    elif option == "List Topics":
        if st.button("Show Topics"):
            st.write(list_all_topics(admin_client))
     
    elif option == "Consume_messages":
        st.subheader("Kafka Topic: chat-messages")
        earliest = st.checkbox("Consume from beginning (earliest)", value=False)

        topics = list_all_topics(admin_client)
        topic_name = st.selectbox("Select topic to consume messages:", topics)
        message_container = st.empty()  # Placeholder for messages
        for messages in consume_messages(topic_name,earliest):
            message_container.json(messages)  # Update messages dynamically
    
    admin_client.close()
    
if __name__ == "__main__":
    main()
