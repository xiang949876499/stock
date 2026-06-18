from pathlib import Path


def test_dockerfile_installs_enabled_integration_extras():
    dockerfile = Path(__file__).resolve().parents[2] / "Dockerfile"
    contents = dockerfile.read_text(encoding="utf-8")

    install_line = next(
        line.strip()
        for line in contents.splitlines()
        if 'pip install ".[' in line
    )

    for extra in ("backtrader", "easytrader", "qbot", "ai-quant"):
        assert extra in install_line
