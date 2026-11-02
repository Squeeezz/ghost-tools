from PIL import Image
from ghost_tools.footprint import scan_directory


def test_corrupt_image_and_limit(tmp_path):
    (tmp_path / 'a.jpg').write_bytes(b'not an image')
    Image.new('RGB', (4, 4)).save(tmp_path / 'b.png')
    reports = scan_directory(tmp_path, limit=1)
    assert len(reports) == 1
    assert reports[0].warnings[0].startswith('Skipped:')
    assert len(scan_directory(tmp_path, limit=2)) == 2
