from pathlib import Path
import importlib.util

import pytest


def _load_module():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "build" / "build_portable.py"
    spec = importlib.util.spec_from_file_location("build_portable", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_create_release_package_copies_expected_files(monkeypatch, tmp_path):
    bp = _load_module()

    build_dir = tmp_path / "build"
    project_root = tmp_path / "project"
    release_dir = project_root / "release"
    dist_dir = build_dir / "dist"

    build_dir.mkdir(parents=True)
    project_root.mkdir(parents=True)
    release_dir.mkdir(parents=True)
    dist_dir.mkdir(parents=True)

    (dist_dir / "YouTubeDownloader.exe").write_text("bin", encoding="utf-8")
    (release_dir / "RELEASE_README.md").write_text("readme", encoding="utf-8")
    (project_root / "LICENSE").write_text("license", encoding="utf-8")

    monkeypatch.setattr(bp, "BUILD_DIR", str(build_dir))
    monkeypatch.setattr(bp, "PROJECT_ROOT", str(project_root))
    monkeypatch.setattr(bp, "RELEASE_DIR", str(release_dir))

    out = bp.create_release_package()

    assert out is not None
    out_path = Path(out)
    assert (out_path / "YouTubeDownloader.exe").exists()
    assert (out_path / "README.md").exists()
    assert (out_path / "LICENSE").exists()
    assert (out_path / "VERSION.txt").exists()
