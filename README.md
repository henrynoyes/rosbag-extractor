# rosbag-extractor

Minimal tool to extract data from ROS2 bags using [rosbags](https://gitlab.com/ternaris/rosbags).

> [!NOTE]
> This is implemented in pure Python and does not require a ROS environment

## Installation

Install with [uv](https://docs.astral.sh/uv/),
```shell
git clone https://github.com/henrynoyes/rosbag-extractor.git
cd rosbag-extractor
uv sync
```

## Usage

### CLI

```shell
uv run rbe-info data/mybag
uv run rbe-video data/mybag --config-path configs/video.yaml
```
or,
```shell
source .venv/bin/activate
rbe-info data/mybag
rbe-video data/mybag --config-path configs/video.yaml
```

### Notebook

```python
from extract_video import VideoExtractor
from info import extract_info
```

```python
extract_info("data/mybag")
```

```python
video_extractor = VideoExtractor(config="configs/video.yaml")
video_extractor.extract(bag_path="data/mybag")
```

### Scripts

- `rbe-info` - clone of `ros2 bag info`
- `rbe-video` - extracts an MP4 video from a [sensor_msgs/Image](https://docs.ros2.org/foxy/api/sensor_msgs/msg/Image.html) topic

> [!TIP]
> Add a `--help` to view command line options, courtesy of [tyro](https://github.com/brentyi/tyro)

## Development

```shell
uv run --dev mypy . # type check with mypy
uvx pre-commit run ruff --all-files # manually lint/format with ruff
```

## Future Features

- [ ] Add script for batch extraction on directory of bags
- [ ] Add option for ROS distro
