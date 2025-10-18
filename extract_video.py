from pathlib import Path
import cv2
import numpy as np
import tyro
import yaml
from tqdm import tqdm
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_typestore

class VideoExtractor:
    """Extract MP4 videos from ROS2 bags"""

    def __init__(self):
        self.typestore = get_typestore(Stores.ROS2_HUMBLE)
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.convert_funcs = {
            'rgb8': self._convert_rgb,
            'bgr8': self._convert_bgr,
            'mono8': self._convert_mono,
            '16UC1': self._convert_depth,
        }

    def _handle_overwrite(self, output_path: Path) -> None:
        if output_path.exists():
            print(f'Warning: {output_path} already exists')
            while True:
                usrin = input('Do you want to overwrite it? (y/n)\n').strip().lower()
                if usrin in ('y', 'n'):
                    break
                print("Invalid input. Please enter 'y' or 'n'")
            
            if usrin == 'n':
                raise FileExistsError('Avoiding overwrite. Exiting...')
            
    def _gen_output_path(self, bag_path: Path, topic: str) -> Path:
        bag_name = bag_path.stem
        topic_name = topic.lstrip('/').replace('/', '-')
        output_path = Path(f'data/{bag_name}_{topic_name}.mp4')
        return output_path

    def _convert_rgb(self, msg) -> np.ndarray:
        arry = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, 3))
        bgr_arry = cv2.cvtColor(arry, cv2.COLOR_RGB2BGR)
        return bgr_arry
    
    def _convert_bgr(self, msg) -> np.ndarray:
        bgr_arry = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, 3))
        return bgr_arry
    
    def _convert_mono(self, msg) -> np.ndarray:
        arry = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width)
        bgr_arry = cv2.cvtColor(arry, cv2.COLOR_GRAY2BGR)
        return bgr_arry

    def _convert_depth(self, msg) -> np.ndarray:
        arry = np.frombuffer(msg.data, dtype=np.uint16).reshape(msg.height, msg.width)
        norm_arry = cv2.normalize(arry, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        colored_norm_arry = cv2.applyColorMap(norm_arry, cv2.COLORMAP_JET)
        colored_norm_arry[arry == 0] = [0, 0, 0]
        return colored_norm_arry
        
    def _to_cv2(self, msg, timestamp) -> np.ndarray | None:
        if msg.encoding not in self.convert_funcs:
            raise ValueError(f'Unsupported image encoding: {msg.encoding}')
        
        try:
            return self.convert_funcs[msg.encoding](msg)
        except Exception as e:
            print(f'Error converting image at {timestamp}: {e}')
            return None
        
    def extract(self, bag_path: Path, config_path: Path, verbose: bool = False) -> None:
        bag_path = Path(bag_path)
        config_path = Path(config_path)
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f'Using configuration: {config_path.name}')

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
        else:
            output_path = Path(output_path)

        self._handle_overwrite(output_path)
        video_writer = cv2.VideoWriter(str(output_path), self.fourcc, config['fps'], (config['width'], config['height']))

        with AnyReader([bag_path], default_typestore=self.typestore) as reader:
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

def main(bag_path: Path, /, config_path: Path, verbose: bool = False) -> None:
    """Extract MP4 video from ROS2 bag

    Args:
        bag_path: Path to input bag
        config_path: Path to YAML config
        verbose: Enable verbose output
    """
    extractor = VideoExtractor()
    extractor.extract(bag_path, config_path, verbose)

if __name__ == '__main__':
    tyro.cli(main)