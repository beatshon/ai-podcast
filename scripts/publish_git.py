"""
Git add → commit (--allow-empty) → push.
public/, data/episodes.json, data/seen.json, data/episode_script.json 만 스테이징.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PUBLIC = ROOT / "public"

ADD_PATHS = [
    str(PUBLIC),
    str(DATA / "episodes.json"),
    str(DATA / "seen.json"),
    str(DATA / "episode_script.json"),
]


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        check=check,
        capture_output=True,
        text=True,
    )


def main():
    if not (ROOT / ".git").exists():
        print("Not a git repo. Skip.", file=sys.stderr)
        return

    for path in ADD_PATHS:
        p = Path(path)
        if not p.exists():
            continue
        try:
            run(["git", "add", path])
            print("git add:", path)
        except subprocess.CalledProcessError as e:
            print(e.stderr or e.stdout or str(e), file=sys.stderr)
            sys.exit(e.returncode)

    try:
        run(["git", "commit", "-m", "Auto publish episode", "--allow-empty"])
        print("git commit: done")
    except subprocess.CalledProcessError as e:
        if e.returncode == 1 and "nothing to commit" in (e.stdout or "") + (e.stderr or ""):
            print("Nothing to commit (working tree clean)")
        else:
            print(e.stderr or e.stdout or str(e), file=sys.stderr)
            sys.exit(e.returncode)

    try:
        run(["git", "push"])
        print("git push: done")
    except subprocess.CalledProcessError as e:
        print(e.stderr or e.stdout or "git push failed", file=sys.stderr)
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
