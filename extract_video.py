from pathlib import Path
import cv2
import numpy as np
import argparse
import yaml
from tqdm import tqdm
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_typestore

parser = argparse.ArgumentParser(description='Extract MP4 from ROS2 bag')
parser.add_argument('bag_path', type=str, help='Path to input bag')
parser.add_argument('-c', '--config', default='video.yaml', type=str, 
                    help='Filename of YAML config inside configs/, defaults to video.yaml')
parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')

class VideoExtractor:

    def __init__(self):
        self.typestore = get_typestore(Stores.ROS2_HUMBLE)
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.convert_funcs = {
            'rgb8': self._convert_rgb,
            'bgr8': self._convert_bgr,
            'mono8': self._convert_mono,
            '16UC1': self._convert_depth,
        }

    def _handle_overwrite(self, output_path):
        if Path(output_path).exists():
            print(f'Warning: {output_path} already exists')
            while True:
                usrin = input('Do you want to overwrite it? (y/n)\n').strip().lower()
                if usrin in ('y', 'n'):
                    break
                print("Invalid input. Please enter 'y' or 'n'")
            
            if usrin == 'n':
                raise FileExistsError('Avoiding overwrite. Exiting...')
            
    def _gen_output_path(self, bag_path, topic):
        bag_name = Path(bag_path).stem
        topic_name = topic.lstrip('/').replace('/', '-')
        output_path = f'data/{bag_name}_{topic_name}.mp4'
        
        return output_path

    def _convert_rgb(self, msg):
        arry = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, 3))
        bgr_arry = cv2.cvtColor(arry, cv2.COLOR_RGB2BGR)
        
        return bgr_arry
    
    def _convert_bgr(self, msg):
        bgr_arry = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, 3))
        
        return bgr_arry
    
    def _convert_mono(self, msg):
        arry = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width)
        bgr_arry = cv2.cvtColor(arry, cv2.COLOR_GRAY2BGR)
        
        return bgr_arry

    def _convert_depth(self, msg):
        arry = np.frombuffer(msg.data, dtype=np.uint16).reshape(msg.height, msg.width)
        norm_arry = cv2.normalize(arry, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        colored_norm_arry = cv2.applyColorMap(norm_arry, cv2.COLORMAP_JET)
        colored_norm_arry[arry == 0] = [0, 0, 0]
        
        return colored_norm_arry
                
    def _to_cv2(self, msg, ts):
        if msg.encoding not in self.convert_funcs:
            raise ValueError(f'Unsupported image encoding: {msg.encoding}')
        
        try:
            return self.convert_funcs[msg.encoding](msg)
        except Exception as e:
            print(f'Error converting image at {ts}: {e}')
            return None
        
    def extract(self, bag_path, config_name, verbose=False):

        config_path = Path('configs') / config_name
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f'Using configuration: {config_name}')

        if verbose:
            print(f"\ntopic: \"{config['topic']}\"")
            print(f"output_path: {config.get('output_path')}")
            print(f"fps: {config['fps']}")
            print(f"width: {config['width']}")
            print(f"height: {config['height']}\n")

        output_path = config.get('output_path')
        topic = config['topic']
        if output_path is None:
            output_path = self._gen_output_path(bag_path, topic)

        self._handle_overwrite(output_path)
        video_writer = cv2.VideoWriter(output_path, self.fourcc, config['fps'], (config['width'], config['height']))

        with AnyReader([Path(bag_path)], default_typestore=self.typestore) as reader:
            connections = [x for x in reader.connections if x.topic == topic]

            if not connections:
                print(f'No messages found for topic: {topic}')
                return

            print(f'Reading {bag_path} ...')
            msg_count = sum(1 for _ in reader.messages(connections=connections))
            with tqdm(total=msg_count, desc='Processing', unit='frames') as pbar:
                for connection, timestamp, rawdata in reader.messages(connections=connections):
                    msg = reader.deserialize(rawdata, connection.msgtype)
                    img = self._to_cv2(msg, timestamp)

                    if img is not None:
                        video_writer.write(img)
                    pbar.update(1)

        video_writer.release()
        print(f'Success! Video saved to {output_path}')

if __name__ == '__main__':

    args = parser.parse_args()
    
    extractor = VideoExtractor()
    extractor.extract(args.bag_path, args.config, args.verbose)