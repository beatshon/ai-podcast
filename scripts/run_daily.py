"""
올인원 일일 파이프라인: fetch_feeds → generate_script → tts_episode → build_feed → (옵션) publish_git.
ROOT 기준 cwd 고정, 어디서 실행해도 동일하게 동작.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

REQUIRED = [
    "fetch_feeds.py",
    "generate_script.py",
    "tts_episode.py",
    "build_feed.py",
]
OPTIONAL = "publish_git.py"


def run_script(name: str) -> None:
    """스크립트 실행. 실패 시 CalledProcessError 발생. stdout/stderr는 터미널로."""
    path = SCRIPTS / name
    print(f"==> running: {name}")
    subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
        check=True,
    )


def main():
    for name in REQUIRED:
        run_script(name)

    path_opt = SCRIPTS / OPTIONAL
    if path_opt.exists():
        print(f"==> running: {OPTIONAL}")
        subprocess.run(
            [sys.executable, str(path_opt)],
            cwd=str(ROOT),
            check=True,
        )
    else:
        print("publish_git.py not found, skip")


if __name__ == "__main__":
    main()
