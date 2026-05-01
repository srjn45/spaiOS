"""Unit tests for MediaAgent — filters, image info, resize."""

import pytest
from PIL import Image

from spaiOS.agents.media_agent import MediaAgent


@pytest.fixture
def agent():
    return MediaAgent()


@pytest.fixture
def rgb_image(tmp_path):
    """100×80 solid-blue JPEG."""
    p = tmp_path / "sample.jpg"
    Image.new("RGB", (100, 80), color=(30, 60, 180)).save(str(p), format="JPEG")
    return p


@pytest.fixture
def rgba_image(tmp_path):
    """50×50 RGBA PNG (for mode-conversion coverage)."""
    p = tmp_path / "sample.png"
    Image.new("RGBA", (50, 50), color=(255, 0, 0, 128)).save(str(p), format="PNG")
    return p


# --- apply_filter: output file creation ---


@pytest.mark.parametrize("style", ["black_white", "high_contrast", "vintage", "90s_film"])
def test_apply_filter_creates_output_file(agent, rgb_image, style):
    out = agent.apply_filter(str(rgb_image), style)
    from pathlib import Path
    assert Path(out).exists()


@pytest.mark.parametrize("style", ["black_white", "high_contrast", "vintage", "90s_film"])
def test_apply_filter_output_is_valid_jpeg(agent, rgb_image, style):
    out = agent.apply_filter(str(rgb_image), style)
    img = Image.open(out)
    assert img.mode == "RGB"
    assert img.size == (100, 80)


@pytest.mark.parametrize("style", ["black_white", "high_contrast", "vintage", "90s_film"])
def test_apply_filter_output_path_contains_style(agent, rgb_image, style):
    out = agent.apply_filter(str(rgb_image), style)
    assert style in out


def test_apply_filter_different_styles_produce_different_files(agent, rgb_image):
    out_bw = agent.apply_filter(str(rgb_image), "black_white")
    out_hc = agent.apply_filter(str(rgb_image), "high_contrast")
    assert out_bw != out_hc


def test_apply_filter_rgba_input_converted_to_rgb(agent, rgba_image):
    out = agent.apply_filter(str(rgba_image), "black_white")
    img = Image.open(out)
    assert img.mode == "RGB"


# --- apply_filter: error cases ---


def test_apply_filter_raises_for_unknown_style(agent, rgb_image):
    with pytest.raises(ValueError, match="Unknown style"):
        agent.apply_filter(str(rgb_image), "cinematic")


def test_apply_filter_raises_for_missing_file(agent, tmp_path):
    with pytest.raises(FileNotFoundError):
        agent.apply_filter(str(tmp_path / "ghost.jpg"), "vintage")


# --- get_image_info ---


def test_get_image_info_returns_dimensions(agent, rgb_image):
    info = agent.get_image_info(str(rgb_image))
    assert info["width"] == 100
    assert info["height"] == 80


def test_get_image_info_returns_expected_keys(agent, rgb_image):
    info = agent.get_image_info(str(rgb_image))
    for key in ("width", "height", "mode", "format", "size_bytes"):
        assert key in info


def test_get_image_info_size_bytes_positive(agent, rgb_image):
    info = agent.get_image_info(str(rgb_image))
    assert info["size_bytes"] > 0


def test_get_image_info_raises_for_missing_file(agent, tmp_path):
    with pytest.raises(FileNotFoundError):
        agent.get_image_info(str(tmp_path / "ghost.jpg"))


# --- resize_image ---


def test_resize_image_produces_correct_dimensions(agent, rgb_image):
    out = agent.resize_image(str(rgb_image), 40, 30)
    img = Image.open(out)
    assert img.size == (40, 30)


def test_resize_image_creates_output_file(agent, rgb_image):
    out = agent.resize_image(str(rgb_image), 20, 20)
    from pathlib import Path
    assert Path(out).exists()


def test_resize_image_output_path_contains_dimensions(agent, rgb_image):
    out = agent.resize_image(str(rgb_image), 64, 48)
    assert "64x48" in out


def test_resize_image_raises_for_missing_file(agent, tmp_path):
    with pytest.raises(FileNotFoundError):
        agent.resize_image(str(tmp_path / "ghost.jpg"), 10, 10)
