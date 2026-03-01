import json
from pathlib import Path
import yaml
import feedparser

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "raw_items.json"


def main():
    cfg = yaml.safe_load(open(ROOT / "config.yaml", "r", encoding="utf-8"))
    items = []
    for s in cfg["sources"]:
        d = feedparser.parse(s["rss"])
        for e in d.entries[:30]:
            link = getattr(e, "link", "")
            title = getattr(e, "title", "").strip()
            summary = getattr(e, "summary", "").strip()
            published = getattr(e, "published", "") or getattr(e, "updated", "")
            if not link or not title:
                continue
            items.append({
                "source": s["name"],
                "title": title,
                "link": link,
                "summary": summary,
                "published": published,
            })

    DATA.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"raw items: {len(items)}")
    print("saved:", OUT)


if __name__ == "__main__":
    main()
