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


def extract_dialogue_only(raw: str) -> str:
    """"AI:" 또는 "제이스:"로 시작하는 줄만 추려서 합친 대화 텍스트 반환."""
    lines = []
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("AI:") or s.startswith("제이스:"):
            lines.append(s)
    return "\n".join(lines) if lines else raw.strip()


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
2인 대화형 팟캐스트 스크립트를 작성한다.
Host A = "제이스" (마케터/기획자 시선), Host B = "AI" (정리 담당 + 질문 던지는 역할).

출력 형식(엄격):
- 각 줄은 반드시 "AI:" 또는 "제이스:" 로 시작한다.
- 한 줄 = 한 문장(짧게). 한 문장 20단어 넘기지 말 것.
- 문장 끝에 마침표/물음표/느낌표 중 하나로 끝낸다.
- 줄바꿈을 자주 사용한다.
- 다른 설명·제목·괄호는 넣지 말고, 대화만 출력한다.

톤:
- 실무자 대화 톤.
- 가벼운 유머 10~15% (과한 개그 금지, 가벼운 농담/밈 느낌 정도).
- 제이스는 "마케터/기획자 시선"으로 해석한다.
- AI는 "정리 담당" + 질문 던지는 역할.

구성(4~6분 분량):

1) 오프닝(20초)
   - AI: 오늘 한 줄 요약
   - 제이스: 짧은 리액션(가벼운 유머 1개 포함)
   - AI: 오늘 다룰 뉴스 2~3개 예고

2) 뉴스 1~3(각 60~90초)
   - AI: 무슨 일인지 3~4문장
   - 제이스: "그래서 우리한테 뭐가 좋은데요?" 같은 질문 1문장
   - AI: 왜 중요한지 2~3문장
   - 제이스: 마케팅/비즈니스 인사이트 2~3문장 + 가벼운 농담 1문장

3) 오늘의 실험(30초)
   - 제이스: 오늘 해볼 실험 1개를 매우 구체적으로 제안(도구/단계 포함)

4) 클로징(10초)
   - AI: 요약 1문장
   - 제이스: 구독/다음 예고 1문장(가벼운 유머 1개)

반드시 마지막에 참고 링크를 대화형으로 포함:
AI: 참고 링크는 설명란에 정리해둘게요.

금지:
- 딱딱한 보고서 문체
- 긴 문장(한 문장 20단어 넘기지 말 것)
- 숫자/스펙 나열
- 과장/확언 ("무조건", "반드시" 금지)
- 영어 남발

오늘의 뉴스:
{news_block}
""".strip()

    script = ollama_generate(cfg["ollama"]["model"], prompt).strip()
    script = extract_dialogue_only(script)

    # Edge TTS는 줄바꿈에 반응. 문장 끝에만 줄바꿈 추가 (대화형 형식 유지)
    script = script.replace("입니다.", "입니다.\n").replace("요.", "요.\n")

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
