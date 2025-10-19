from datetime import datetime
from pathlib import Path

import tyro
import yaml


def extract_info(bag_path: Path, /) -> None:
    """Extract information from ROS2 bag metadata

    Args:
        bag_path: Path to input bag
    """

    bag_path = Path(bag_path)
    metadata_file = bag_path / "metadata.yaml"
    if not metadata_file.exists():
        print(f"Error: metadata.yaml not found in {bag_path}")
        return

    total_size = sum(f.stat().st_size for f in bag_path.rglob("*") if f.is_file())
    if total_size > 1024**3:
        print(f"\nSize: {total_size / 1024**3:.3g} GB")
    else:
        print(f"\nSize: {total_size / 1024**2:.3g} MB")

    with open(metadata_file) as f:
        bag_info = yaml.safe_load(f)["rosbag2_bagfile_information"]

    duration_ns = bag_info["duration"]["nanoseconds"]
    start_time_ns = bag_info["starting_time"]["nanoseconds_since_epoch"]

    print(f"Duration: {duration_ns / 1e9:.3g}s")
    print(f"Start: {datetime.fromtimestamp(start_time_ns / 1e9).strftime('%B %d, %Y %H:%M:%S.%f')[:-3]}")
    print(f"End: {datetime.fromtimestamp((start_time_ns + duration_ns) / 1e9).strftime('%B %d, %Y %H:%M:%S.%f')[:-3]}")
    print(f"Messages: {bag_info['message_count']}")
    print("\nTopics:")
    topic_counts = {t["topic_metadata"]["name"]: t["message_count"] for t in bag_info["topics_with_message_count"]}
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {topic}: {count}")


if __name__ == "__main__":
    tyro.cli(extract_info)
