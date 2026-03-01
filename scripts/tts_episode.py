"""
대화형 스크립트(AI: / 제이스:)를 줄 단위로 구분해
voice_ai / voice_jace로 TTS 후, 250ms 무음 삽입해 ffmpeg로 병합.
출력: episodes/{slug}.mp3, episodes/{slug}.txt (프로젝트 루트 기준)
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EP_DIR = ROOT / "episodes"
SCRIPT_JSON = DATA / "episode_script.json"

SILENCE_DURATION_SEC = 0.25
SILENCE_SAMPLE_RATE = 24000


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg"):
        return
    print("ffmpeg를 찾을 수 없습니다.")
    print("macOS: brew install ffmpeg")
    raise RuntimeError("ffmpeg is required. Install with: brew install ffmpeg")


def parse_lines(script: str) -> list[tuple[str, str]]:
    """(speaker, text) 리스트. speaker는 'jace' 또는 'ai'. 빈 줄·미인식 줄 스킵."""
    result = []
    for line in script.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("제이스:"):
            result.append(("jace", s[len("제이스:") :].strip()))
        elif s.startswith("AI:"):
            result.append(("ai", s[len("AI:") :].strip()))
    return result


def tts_one(
    text: str,
    voice: str,
    rate: str,
    volume: str | None,
    txt_path: Path,
    mp3_path: Path,
) -> None:
    """한 줄 텍스트를 tmp txt로 쓰고 edge-tts --file로 mp3 생성."""
    if not text:
        return
    txt_path.write_text(text, encoding="utf-8")
    cmd = [
        "edge-tts",
        "--voice", voice,
        "--rate", rate,
        "--file", str(txt_path),
        "--write-media", str(mp3_path),
    ]
    if volume:
        cmd.extend(["--volume", volume])
    subprocess.run(cmd, check=True)


def make_silence_mp3(out_path: Path, duration_sec: float = SILENCE_DURATION_SEC) -> None:
    """duration_sec 길이의 무음 mp3 생성 (concat 시 샘플레이트 맞춤)."""
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r={SILENCE_SAMPLE_RATE}:cl=stereo",
            "-t", str(duration_sec),
            "-acodec", "libmp3lame",
            "-ar", str(SILENCE_SAMPLE_RATE),
            "-ac", "1",
            str(out_path),
        ],
        check=True,
        capture_output=True,
    )


def concat_with_silence(part_mp3s: list[Path], silence_mp3: Path, out_path: Path, tmpdir: Path) -> None:
    """part_mp3s 사이에 silence를 끼워 넣어 순서대로 병합. part0, silence, part1, silence, ..."""
    lines = []
    for i, p in enumerate(part_mp3s):
        lines.append(f"file '{p.resolve()}'")
        if i < len(part_mp3s) - 1:
            lines.append(f"file '{silence_mp3.resolve()}'")
    list_file = tmpdir / "concat_list.txt"
    list_file.write_text("\n".join(lines), encoding="utf-8")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",
                str(out_path),
            ],
            check=True,
            capture_output=True,
        )
    finally:
        list_file.unlink(missing_ok=True)


def main():
    require_ffmpeg()
    print("[1/6] ffmpeg 확인 완료")

    EP_DIR.mkdir(parents=True, exist_ok=True)

    if not SCRIPT_JSON.exists():
        print("no script. exit.")
        return

    cfg = yaml.safe_load(open(ROOT / "config.yaml", "r", encoding="utf-8"))
    tts = cfg.get("tts", {})
    voice_jace = tts.get("voice_jace", "ko-KR-SunHiNeural")
    voice_ai = tts.get("voice_ai", "ko-KR-InJoonNeural")
    rate = tts.get("rate", "+0%")
    volume = tts.get("volume")

    ep = json.loads(SCRIPT_JSON.read_text(encoding="utf-8"))
    slug = ep["slug"]
    script = ep.get("script", "")

    out_mp3 = EP_DIR / f"{slug}.mp3"
    out_txt = EP_DIR / f"{slug}.txt"
    out_txt.write_text(script, encoding="utf-8")
    print(f"[2/6] 대본 저장: {out_txt}")

    segments = parse_lines(script)
    if not segments:
        print("no 제이스:/AI: lines. exit.")
        return
    print(f"[3/6] 대화 {len(segments)}줄 파싱 완료")

    tmpdir = Path(tempfile.mkdtemp(prefix="tts_episode_"))
    part_mp3s = []
    try:
        make_silence_mp3(tmpdir / "silence.mp3")
        print("[4/6] 250ms 무음 생성 완료")

        for i, (speaker, text) in enumerate(segments):
            if not text:
                continue
            voice = voice_jace if speaker == "jace" else voice_ai
            txt_path = tmpdir / f"line_{i:04d}.txt"
            mp3_path = tmpdir / f"part_{i:04d}.mp3"
            tts_one(text, voice, rate, volume, txt_path, mp3_path)
            part_mp3s.append(mp3_path)
            print(f"  [{speaker}] {text[:50]}{'…' if len(text) > 50 else ''}")

        concat_with_silence(part_mp3s, tmpdir / "silence.mp3", out_mp3, tmpdir)
        print(f"[5/6] 병합 완료: {out_mp3}")
    finally:
        for f in tmpdir.iterdir():
            f.unlink(missing_ok=True)
        tmpdir.rmdir()
    print("[6/6] 임시 파일 삭제 완료")
    print("done. mp3:", out_mp3)


if __name__ == "__main__":
    main()
