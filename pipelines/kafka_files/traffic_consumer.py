import time
# time.sleep(300)
from kafka import KafkaConsumer
import os ,sys,time,json
from kafka import KafkaProducer
from datetime import datetime

AIRFLOW_HOME = os.getenv("AIRFLOW_HOME", "/opt/airflow")
if AIRFLOW_HOME != "/opt/airflow":
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    AIRFLOW_HOME = BASE_DIR
    print(BASE_DIR)

SCRIPTS_PATH = os.path.join(AIRFLOW_HOME, "scripts") 
sys.path.append(SCRIPTS_PATH)
common_PATH = os.path.join(AIRFLOW_HOME, "common") 
sys.path.append(common_PATH)
common_PATH = os.path.join(AIRFLOW_HOME, "common","logging_and_monitoring","logs") 
sys.path.append(common_PATH)


from logging_and_monitoring.centralized_logging import setup_logger

from utils.api_utils import tomtom_api,get_weather_data,get_route
from utils.db_utils import bulk_insert_into_traffic_Data_Table,get_road_id,get_road_data_FROMroad_id,bulk_insert_into_weather_Data_Table
from utils.trafficHelper_utils import filter_significant_points
from utils.Database_connection_Utils import connect_Database

consumer_Script_logs_path=os.path.join(common_PATH, "Traffic_consumer.log")
logger = setup_logger("Traffic_Data_ETL", "consumer_script", "kafka", consumer_Script_logs_path)

#bootstrap_servers='172.19.165.234:9092',

# Set `earliest = True` if you want to read old messages
earliest = True
topic="traffic-topic"


def consumer1():
    try: 
        consumer = KafkaConsumer(
            topic,  # Kafka topic
            bootstrap_servers='kafka:9092',  # Replace with  Kafka server
            auto_offset_reset="latest", #if earliest else "latest",
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            enable_auto_commit=True,  # Enable auto-commit
        )
        producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
                
        logger.info("Connected tooo Kafka. Listening for messages...")
        conn= connect_Database()
       
        logger.info(f"conn: {conn}")
    
        if conn is None:
            logger.critical("Failed to establish database connection.", extra={"stage": "start"})
            exit()
        
        messages = []
        logger.critical("starting for message in consumer", extra={"stage": "start"})

        while True: 
            for message in consumer:
                Received_message=message.value
                road_id=Received_message.get('road_id')
                logger.info(f"Received message: {message.value}")
                
                traffic_data_list = []
                status=get_road_data_FROMroad_id(road_id,conn)
                logger.info(f"Status : {status}")
                road=status[0]
                
                road_id, start_lat, start_lon, end_lat, end_lon, road_name = road[0], road[1], road[2], road[3], road[4], road[5]
                logger.info(f"Processing road: {road_name} (ID: {road_id})", extra={"stage": "loop_roadData"})
                
                intermediate_points, route_length = get_route(start_lat, start_lon, end_lat, end_lon)
                logger.info(f"intermediate_points: {intermediate_points} ,{route_length}")

                if not intermediate_points:
                    logger.warning(f"No intermediate points found for road: {road_name} (ID: {road_id})",
                                                 extra={"stage": "loop_roadData"})
                    continue  # Skip this road if no route found
                interval = max(250, min(route_length / 10, 2000))  # Adaptive interval
                filtered_points = filter_significant_points(intermediate_points, interval)
                # Get weather data only once (for the first point in the list)
                if not filtered_points:
                    logger.warning(f"No significant points found in filtered points for road: {road_name} (ID: {road_id})",
                                                 extra={"stage": "loop_roadData"})
                    continue  # Skip if no valid points
               
                first_point = filtered_points[0]
                
                for attempt in range(3):
                    try:
                        logger.info(f"get_weather_data() calling  attempt: {attempt} with {first_point['latitude']},{first_point['longitude']}",
                                                      extra={"stage": "loop_roadData"})

                        weather_conditions, temperature, humidity = get_weather_data(first_point['latitude'],
                                                                                     first_point['longitude'])
                        if weather_conditions is not None:  # Stop retrying if successful
                                  break
                    except Exception as e:
                        logger.error(f"Attempt {attempt + 1}: Failed to fetch weather data: {e}", exc_info=True,
                                                       extra={"stage": "loop_roadData"})
                        if attempt == 2:  # Last attempt
                            weather_conditions, temperature, humidity = "Unknown", "Unknown", "Unknown"

                print(f"📍 Intermediate Coordinates Along the Road (Interval: {interval}m):")


                for point in filtered_points:
                    try:
                        logger.info(f"tomotom_Api() calling with ({point['latitude']}{point['longitude']})",
                                                      extra={"stage": "loop_roadData_filtered_point"})
                        traffic_data = tomtom_api(point['latitude'], point['longitude'])
                        logger.info(f"point: {len(traffic_data)}", extra={"stage": "loop_roadData_filtered_point"})

                        logger.info(f"tomotom_Api() completed ", extra={"stage": "loop_roadData_filtered_point"})

                        # Extract values safely, with default fallbacks
                        current_speed = traffic_data.get("flowSegmentData", {}).get("currentSpeed", "Unknown")
                        free_flow_speed = traffic_data.get("flowSegmentData", {}).get("freeFlowSpeed", "Unknown")

                        traffic_condition = ("Free Flow" if current_speed >= free_flow_speed
                                             else "Moderate" if current_speed >= 0.5 * free_flow_speed
                        else "Heavy" if current_speed >= 0.3 * free_flow_speed
                        else "Severe")

                        current_travel_time = traffic_data.get("flowSegmentData", {}).get("currentTravelTime", "Unknown")
                        free_flow_travel_time = traffic_data.get("flowSegmentData", {}).get("freeFlowTravelTime", "Unknown")
                        road_closure = traffic_data.get("flowSegmentData", {}).get("roadClosure", "Unknown")


                        traffic_data_list.append({
                            "road_id": road_id,
                            "road_name": road_name,
                            "latitude": float(round(point['latitude'], 6)),
                            "longitude": float(round(point['longitude'], 6)),
                            "current_speed": current_speed,
                            "free_flow_speed": free_flow_speed,
                            "current_travel_time": current_travel_time,
                            "free_flow_travel_time": free_flow_travel_time,
                            "roadClosure": road_closure,
                            "mapurl": f"https://www.google.com/maps?q={point['latitude']},{point['longitude']}",
                            "weather_conditions": weather_conditions,
                            "temperature": temperature,
                            "humidity": humidity,
                            "traffic_condition": traffic_condition,
                            "recorded_at":datetime.utcnow()
                        })
                        logger.info(f"count of traffic_data_list:{len(traffic_data_list)} ", extra={"stage": "loop_roadData_filtered_point"})

                    except KeyError as ke:
                        logger.error(f"Missing expected traffic data key: {ke}", exc_info=True,
                                                       extra={"stage": "loop_roadData_filtered_point"})
                    except Exception as e:
                        logger.error(f"Unexpected error while processing traffic data: {e}",
                                                       exc_info=True, extra={"stage": "loop_roadData_filtered_point"})
                        # print(f" - {point['latitude']}, {point['longitude']}")
                        # print(f"https://www.google.com/maps?q={point['latitude']},{point['longitude']}")
                if traffic_data_list:
                        try:
                            logger.info(f"bulk_insert_into_weather_Data_Table() calling with : {traffic_data_list}",
                                                          extra={"stage": "loop_roadData_filtered_point"})
                            weather_id_map = bulk_insert_into_weather_Data_Table(traffic_data_list, conn)
                            
                            logger.info(f"bulk_insert_into_weather_Data_Table() completed",
                                                          extra={"stage": "loop_roadData_filtered_point"})         
                            logger.info(f"bulk_insert_into_traffic_Data_Table() calling with : {len(traffic_data_list)}",
                                                          extra={"stage": "loop_roadData_filtered_point"})
                            bulk_insert_into_traffic_Data_Table(traffic_data_list, conn,weather_id_map)
                            
                            logger.info(f"bulk_insert_into_traffic_Data_Table() completed",
                                                          extra={"stage": "loop_roadData_filtered_point"})
                                                          
                                                
                            traffic_data_list.clear()  # Clear list after insertion
                        except Exception as e:
                            logger.critical(f"Failed to insert traffic data: {e}", exc_info=True,
                                                              extra={"stage": "loop_roadData_filtered_point"})
                        
                   
                                
    except Exception as e:
        logger.error(f"Exception occurred: {str(e)}")
        consumer.close()


# Run consumer forever
if __name__ == "__main__":
        consumer1()
       
