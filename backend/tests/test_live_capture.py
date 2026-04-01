import os
import tempfile
from PIL import Image
from minimap_capture import save_minimap_to_disk


def test_save_minimap_to_disk():
    img = Image.new("RGB", (226, 226), color=(100, 50, 50))
    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_minimap_to_disk(img, tmpdir, "death", 945.0)
        assert os.path.exists(path)
        assert path.endswith(".png")
        assert "death_0945" in path
        with Image.open(path) as saved:
            size = saved.size
        assert size == (226, 226)


def test_save_minimap_creates_output_dir():
    """output_dir deve ser criado se não existir."""
    img = Image.new("RGB", (64, 64), color=(0, 128, 0))
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = os.path.join(tmpdir, "subdir", "nested")
        assert not os.path.exists(new_dir)
        path = save_minimap_to_disk(img, new_dir, "kill", 100.0)
        assert os.path.exists(new_dir)
        assert os.path.exists(path)


def test_save_minimap_collision_guard():
    """Dois saves no mesmo timestamp devem gerar arquivos distintos."""
    img1 = Image.new("RGB", (64, 64), color=(255, 0, 0))
    img2 = Image.new("RGB", (64, 64), color=(0, 0, 255))
    with tempfile.TemporaryDirectory() as tmpdir:
        path1 = save_minimap_to_disk(img1, tmpdir, "death", 945.0)
        path2 = save_minimap_to_disk(img2, tmpdir, "death", 945.0)
        assert path1 != path2
        assert os.path.exists(path1)
        assert os.path.exists(path2)
        assert "death_0945.png" in path1
        assert "death_0945_1.png" in path2


def test_save_minimap_collision_guard_triple():
    """Três saves no mesmo timestamp devem gerar três arquivos distintos."""
    img = Image.new("RGB", (32, 32), color=(10, 20, 30))
    with tempfile.TemporaryDirectory() as tmpdir:
        path1 = save_minimap_to_disk(img, tmpdir, "death", 945.0)
        path2 = save_minimap_to_disk(img, tmpdir, "death", 945.0)
        path3 = save_minimap_to_disk(img, tmpdir, "death", 945.0)
        assert len({path1, path2, path3}) == 3
        assert all(os.path.exists(p) for p in [path1, path2, path3])
        assert "death_0945_2.png" in path3


def test_save_minimap_game_time_zero():
    """game_time_sec=0.0 deve produzir filename com 0000."""
    img = Image.new("RGB", (64, 64), color=(50, 50, 50))
    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_minimap_to_disk(img, tmpdir, "start", 0.0)
        assert os.path.exists(path)
        assert "start_0000.png" in path


def test_detect_new_match_id():
    before = ["BR1_100", "BR1_101", "BR1_102"]
    after = ["BR1_103", "BR1_100", "BR1_101", "BR1_102"]
    new_id = next((mid for mid in after if mid not in before), None)
    assert new_id == "BR1_103"


def test_no_new_match_id():
    before = ["BR1_100", "BR1_101"]
    after = ["BR1_100", "BR1_101"]
    new_id = next((mid for mid in after if mid not in before), None)
    assert new_id is None
