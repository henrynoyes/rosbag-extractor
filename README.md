# rosbag-extractor

> [!NOTE]
> This is implemented in pure Python and does not require a ROS environment

## Installation

Install with [uv](https://docs.astral.sh/uv/),
```bash
git clone git@github.com:henrynoyes/rosbag-extractor.git
cd rosbag-extractor
uv sync
```

## Usage

### CLI

```bash
uv run extract_video.py -c video.yaml data/mybag
```
or,
```bash
source .venv/bin/activate
python3 extract_video.py -c video.yaml data/mybag
```

### Notebook

```python
from extract_video import VideoExtractor
from info import extract_info
```

```python
extract_info('data/mybag')
```

```python
video_extractor = VideoExtractor()
video_extractor.extract(bag_path='data/mybag', config='video.yaml')
```

### Scripts

- `info.py` - clone of `ros2 bag info`
- `extract_video.py` - extracts MP4 from image stream

> [!TIP]
> Add a `--help` to view command line options

## Future Features

- [ ] Add script for batch extraction on directory of bags
- [ ] Add option for ROS distro
- [ ] Rework CLI using [tyro](https://github.com/brentyi/tyro)
