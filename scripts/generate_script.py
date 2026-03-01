import json
import datetime
from pathlib import Path
import yaml
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw_items.json"
SCRIPT_OUT = DATA / "episode_script.json"
SEEN = DATA / "seen.json"


def pick_top(items, seen, k=3, max_scan=80):
    picked = []
    for it in items[:max_scan]:
        if it["link"] in seen:
            continue
        picked.append(it)
        if len(picked) >= k:
            break
    return picked


def ollama_generate(model, prompt):
    url = "http://localhost:11434/api/generate"
    r = requests.post(
        url, json={"model": model, "prompt": prompt, "stream": False}, timeout=600
    )
    r.raise_for_status()
    return r.json()["response"]


def main():
    cfg = yaml.safe_load(open(ROOT / "config.yaml", "r", encoding="utf-8"))
    items = json.loads(RAW.read_text(encoding="utf-8"))
    seen = json.loads(SEEN.read_text(encoding="utf-8")) if SEEN.exists() else {}

    top_k = cfg["schedule"]["top_news"]
    picks = pick_top(items, seen, k=top_k)

    if not picks:
        print("No new items. exit.")
        return

    news_block = "\n".join([
        f"- [{p['source']}] {p['title']} ({p['link']})\n  요약: {p['summary'][:400]}"
        for p in picks
    ])

    prompt = f"""
너는 'AI 트렌드 팟캐스트' 진행자다. 한국어로 말하듯 자연스럽게.
목표: 오늘의 AI 트렌드 3개를 요약하고, 마케팅/비즈니스 관점 인사이트와 실행 아이디어를 제시한다.

형식(필수):
1) 오프닝(10~15초)
2) 뉴스 1~3 (각: 45~70초)
   - 한 문장 요약
   - 왜 중요한가
   - 마케팅/비즈니스 인사이트 1개
3) 오늘의 실행 아이디어(30초)
4) 클로징(10초)
5) 참고 링크(마지막에 목록)

주의:
- 과장 금지. 수치/사실 확언은 피하고 '발표에 따르면' 톤 사용
- 길이: 전체 4~6분 분량

오늘의 뉴스:
{news_block}
""".strip()

    script = ollama_generate(cfg["ollama"]["model"], prompt).strip()

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    slug = today.replace("-", "")
    title = f"AI 트렌드 브리핑 - {today}"

    episode = {
        "date": today,
        "slug": slug,
        "title": title,
        "script": script,
        "sources": picks,
    }

    DATA.mkdir(parents=True, exist_ok=True)
    SCRIPT_OUT.write_text(
        json.dumps(episode, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("script generated:", SCRIPT_OUT)

    for p in picks:
        seen[p["link"]] = today
    SEEN.write_text(
        json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("seen updated:", SEEN)


if __name__ == "__main__":
    main()
