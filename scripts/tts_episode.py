import json
from pathlib import Path
import yaml
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PUBLIC = ROOT / "public"
EP_DIR = PUBLIC / "episodes"
SCRIPT = DATA / "episode_script.json"


def main():
    EP_DIR.mkdir(parents=True, exist_ok=True)

    if not SCRIPT.exists():
        print("no script. exit.")
        return

    cfg = yaml.safe_load(open(ROOT / "config.yaml", "r", encoding="utf-8"))
    ep = json.loads(SCRIPT.read_text(encoding="utf-8"))

    out_mp3 = EP_DIR / f"{ep['slug']}.mp3"
    out_txt = EP_DIR / f"{ep['slug']}.txt"
    out_txt.write_text(ep["script"], encoding="utf-8")

    cmd = [
        "edge-tts",
        "--voice", cfg["tts"]["voice"],
        "--rate", cfg["tts"]["rate"],
        "--volume", cfg["tts"]["volume"],
        "--file", str(out_txt),
        "--write-media", str(out_mp3),
    ]
    print(">", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("mp3 generated:", out_mp3)


if __name__ == "__main__":
    main()
