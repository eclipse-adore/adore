import logging
from collections import defaultdict
from typing import List, Dict 

try:
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
    from rosidl_runtime_py.convert import message_to_ordereddict
except ImportError:
    logging.error("rosbag2_py not available. Install with: pip install rosbag2_py")
    raise

class BagFileReader:
    def __init__(self, bag_file_path: str):
        self.bag_file_path = bag_file_path
        self.topics_data = defaultdict(list)
        self._load_bag_data()
    
    def _load_bag_data(self):
        """Load data from ROS2 bag file using rosbag2_py"""
        try:
            storage_options = rosbag2_py.StorageOptions(
                uri=self.bag_file_path,
                storage_id='sqlite3'
            )
            
            converter_options = rosbag2_py.ConverterOptions(
                input_serialization_format='cdr',
                output_serialization_format='cdr'
            )
            
            reader = rosbag2_py.SequentialReader()
            reader.open(storage_options, converter_options)
            
            topic_types = reader.get_all_topics_and_types()
            type_map = {topic.name: topic.type for topic in topic_types}
            
            logging.info(f"Found topics: {list(type_map.keys())}")
            
            message_count = 0
            while reader.has_next():
                (topic, data, timestamp) = reader.read_next()
                
                if topic in type_map:
                    try:
                        msg_type = type_map[topic]
                        msg_class = get_message(msg_type)
                        msg = deserialize_message(data, msg_class)
                        
                        msg_dict = message_to_ordereddict(msg)
                        msg_dict['timestamp'] = timestamp / 1e9  # Convert from nanoseconds
                        msg_dict['topic'] = topic
                        msg_dict['datatype'] = msg_type
                        
                        self.topics_data[topic].append(msg_dict)
                        message_count += 1
                        
                    except Exception as e:
                        logging.debug(f"Failed to deserialize message on topic {topic}: {e}")
            
            reader.close()
            logging.info(f"Loaded {message_count} messages from bag file")
            
        except Exception as e:
            logging.error(f"Failed to load bag file {self.bag_file_path}: {e}")
            raise
    
    def get_topic_data(self, topic_name: str) -> List[Dict]:
        """Get all messages for a specific topic"""
        return self.topics_data.get(topic_name, [])
    
    def get_all_topics(self) -> List[str]:
        """Get list of all available topics"""
        return list(self.topics_data.keys())
