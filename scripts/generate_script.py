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
너는 10년 경력의 라디오 진행자다.
청취자는 마케터와 비즈니스 실무자다.

목표:
AI 뉴스를 '읽는 느낌'이 아니라
실제 사람이 마이크 앞에서 말하는 것처럼 자연스럽게 말하듯 작성한다.

작성 규칙:
1. 문장은 짧게.
2. 한 문장은 15~20단어 이내.
3. 줄바꿈을 자주 사용한다.
4. 연결어를 적극 사용한다.
   (예: 그런데요, 여기서 중요한 건, 쉽게 말하면, 한마디로 정리하면)
5. 중간중간 청취자에게 말을 건다.
   (예: 여러분은 어떻게 보시나요?, 이 부분이 핵심입니다.)
6. 숫자 나열 금지.
7. 전문 용어는 설명 후 사용.
8. 딱딱한 문어체 금지.
9. 뉴스 요약보다 '왜 중요한지'를 강조.
10. 마지막에는 제이스 개인 코멘트 2~3문장 포함.

구성:
[오프닝 – 15초]
오늘의 AI 트렌드 한 줄 요약

[뉴스 1]
- 무슨 일인가
- 왜 중요한가
- 실무에서 어떻게 써먹을 수 있는가

[뉴스 2]
동일 구조

[마무리]
오늘 한 가지 실험해볼 아이디어 제안

추가 주의:
- 과장 금지. 수치/사실 확언은 피하고 '발표에 따르면' 톤 사용.
- 전체 4~6분 분량으로 작성.

오늘의 뉴스:
{news_block}
""".strip()

    script = ollama_generate(cfg["ollama"]["model"], prompt).strip()

    # Edge TTS는 쉼표·줄바꿈에 반응하므로 문장 끝에 줄바꿈 추가
    script = ".\n".join([s.strip() for s in script.split(". ") if s.strip()])
    if script and not script.endswith("."):
        script = script + "."

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
