import pytest
import os
#from pathlib import Path

# Fixtures pointing to test files
@pytest.fixture(scope="module")
def base_dir():
    return os.path.dirname(os.path.abspath(__file__))

@pytest.fixture(scope="module")
def video_as_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(base_dir,"..","demos","video_as_dir"))

@pytest.fixture(scope="module")
def background():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(base_dir,"..","demos","background.png"))

@pytest.fixture(scope="module")
def video_as_mp4():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(base_dir,"..","demos","video.mp4"))

@pytest.fixture(scope="module")
def slideshow_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(base_dir,"..","demos","slideshow"))

@pytest.fixture(scope="module")
def test_tmp_prefix():
    return "pytest-tmp"



# delete any temporary files
#for f in Path(".").rglob("pytest-tmp-*"):
#    os.remove(f)
