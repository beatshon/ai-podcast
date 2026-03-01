"""
Podcast RSS(feed.xml) 자동 생성.
- data/episode_script.json + episodes/{slug}.mp3 존재 시에만 진행
- data/episodes.json 누적 관리, 프로젝트 루트 feed.xml 생성 (feedgen + iTunes extension)
"""
import json
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone

import yaml
from feedgen.feed import FeedGenerator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EP_DIR = ROOT / "episodes"
FEED_PATH = ROOT / "feed.xml"
EPISODES_JSON = DATA / "episodes.json"
SCRIPT_JSON = DATA / "episode_script.json"
UTC = timezone.utc
LOG = logging.getLogger(__name__)


def load_config():
    """config.yaml 로드."""
    cfg_path = ROOT / "config.yaml"
    if not cfg_path.exists():
        LOG.error("config.yaml 없음: %s", cfg_path)
        raise FileNotFoundError(f"config.yaml not found: {cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not cfg or "podcast" not in cfg:
        LOG.error("config.yaml에 podcast 섹션이 없습니다.")
        raise ValueError("config.yaml must have 'podcast' section")
    return cfg


def load_episode_script():
    """data/episode_script.json에서 slug, title, date, script 로드."""
    if not SCRIPT_JSON.exists():
        LOG.error("episode_script.json 없음: %s", SCRIPT_JSON)
        raise FileNotFoundError(f"episode_script.json not found: {SCRIPT_JSON}")
    try:
        raw = SCRIPT_JSON.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError) as e:
        LOG.error("episode_script.json 로드 실패: %s", e)
        raise
    slug = data.get("slug")
    title = data.get("title", "")
    date_str = data.get("date", "")
    script = data.get("script", "")
    if not slug:
        LOG.error("episode_script.json에 slug가 없습니다.")
        raise ValueError("episode_script.json must have 'slug'")
    if not date_str:
        LOG.error("episode_script.json에 date가 없습니다.")
        raise ValueError("episode_script.json must have 'date'")
    return {"slug": slug, "title": title, "date": date_str, "script": script}


def ensure_mp3_exists(slug: str) -> bool:
    """episodes/{slug}.mp3 존재 여부. 없으면 로그 후 False."""
    mp3_path = EP_DIR / f"{slug}.mp3"
    if not mp3_path.exists():
        LOG.warning("mp3 not found: %s (기존 episodes만 URL 갱신)", mp3_path)
        return False
    return True


def refresh_episode_urls(cfg: dict, episodes: list) -> None:
    """episodes 리스트의 mp3/text URL을 현재 config site_url 기준으로 갱신."""
    site = (cfg.get("podcast") or {}).get("site_url") or ""
    site = site.rstrip("/")
    for ep in episodes:
        slug = ep.get("slug")
        if not slug:
            continue
        ep["mp3"] = f"{site}/episodes/{slug}.mp3"
        ep["text"] = f"{site}/episodes/{slug}.txt"


def ensure_txt_exists(slug: str, script: str) -> Path:
    """episodes/{slug}.txt 없으면 script로 생성."""
    txt_path = EP_DIR / f"{slug}.txt"
    if not txt_path.exists() and script:
        try:
            EP_DIR.mkdir(parents=True, exist_ok=True)
            txt_path.write_text(script, encoding="utf-8")
            LOG.info("대본 생성: %s", txt_path)
        except OSError as e:
            LOG.error("대본 파일 생성 실패: %s", e)
            raise
    return txt_path


def load_episodes_list() -> list:
    """data/episodes.json 로드. 없으면 빈 리스트. 중복 slug 제거."""
    if not EPISODES_JSON.exists():
        return []
    try:
        raw = EPISODES_JSON.read_text(encoding="utf-8")
        arr = json.loads(raw)
    except (json.JSONDecodeError, OSError) as e:
        LOG.error("episodes.json 로드 실패: %s", e)
        raise
    if not isinstance(arr, list):
        return []
    seen = set()
    out = []
    for ep in arr:
        s = ep.get("slug")
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(ep)
    return out


def save_episodes_list(episodes: list) -> None:
    """data/episodes.json 저장."""
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        EPISODES_JSON.write_text(
            json.dumps(episodes, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as e:
        LOG.error("episodes.json 저장 실패: %s", e)
        raise


def register_episode_if_new(cfg: dict, episodes: list, ep_info: dict) -> list:
    """현재 에피소드가 목록에 없으면 맨 앞에 추가 후 반환."""
    slug = ep_info["slug"]
    if any(e.get("slug") == slug for e in episodes):
        return episodes
    site = (cfg["podcast"].get("site_url") or "").rstrip("/")
    mp3_url = f"{site}/episodes/{slug}.mp3"
    txt_url = f"{site}/episodes/{slug}.txt"
    new_ep = {
        "slug": slug,
        "title": ep_info["title"],
        "date": ep_info["date"],
        "mp3": mp3_url,
        "text": txt_url,
    }
    episodes.insert(0, new_ep)
    return episodes


def warn_if_example_site_url(cfg: dict) -> None:
    """podcast.site_url에 example.com이 있으면 경고 출력."""
    url = (cfg.get("podcast") or {}).get("site_url") or ""
    if "example.com" in url:
        print("⚠️ podcast.site_url이 아직 설정되지 않았습니다.", file=sys.stderr)


def build_feed_xml(cfg: dict, episodes: list) -> None:
    """config podcast 값으로 루트 feed.xml 생성. feedgen + podcast(itunes) extension."""
    podcast = cfg["podcast"]
    fg = FeedGenerator()
    fg.load_extension("podcast")

    fg.title(podcast.get("title", ""))
    fg.link(href=podcast.get("site_url", ""), rel="alternate")
    fg.description(podcast.get("description", ""))
    fg.language(podcast.get("language", "ko"))

    fg.podcast.itunes_author(podcast.get("author", ""))
    fg.podcast.itunes_summary(podcast.get("description", ""))
    if podcast.get("image_url"):
        fg.podcast.itunes_image(podcast["image_url"])

    for ep in episodes[:200]:
        fe = fg.add_entry()
        fe.id(ep.get("mp3", ""))
        fe.title(ep.get("title", ""))
        fe.link(href=ep.get("text", ""))
        fe.description(f"대본: {ep.get('text', '')}")

        date_str = ep.get("date", "")
        try:
            dt = datetime.fromisoformat(date_str).replace(tzinfo=UTC)
        except (ValueError, TypeError):
            dt = datetime.now(UTC)
        fe.pubDate(dt)
        fe.enclosure(ep.get("mp3", ""), 0, "audio/mpeg")

    try:
        xml_bytes = fg.rss_str(pretty=True)
        xml_str = xml_bytes.decode("utf-8") if isinstance(xml_bytes, bytes) else xml_bytes
        FEED_PATH.write_text(xml_str, encoding="utf-8")
    except Exception as e:
        LOG.error("feed.xml 생성 실패: %s", e)
        raise


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
    )
    try:
        cfg = load_config()
    except Exception as e:
        LOG.error("[단계: config 로드] %s", e)
        raise

    try:
        ep_info = load_episode_script()
    except Exception as e:
        LOG.error("[단계: episode_script.json 로드] %s", e)
        raise

    mp3_ok = ensure_mp3_exists(ep_info["slug"])

    if mp3_ok:
        try:
            ensure_txt_exists(ep_info["slug"], ep_info.get("script", ""))
        except Exception as e:
            LOG.error("[단계: 대본 .txt 생성] %s", e)
            raise

    try:
        episodes = load_episodes_list()
    except Exception as e:
        LOG.error("[단계: episodes.json 로드] %s", e)
        raise

    if mp3_ok:
        episodes = register_episode_if_new(cfg, episodes, ep_info)

    refresh_episode_urls(cfg, episodes)

    try:
        save_episodes_list(episodes)
    except Exception as e:
        LOG.error("[단계: episodes.json 저장] %s", e)
        raise

    warn_if_example_site_url(cfg)

    try:
        build_feed_xml(cfg, episodes)
    except Exception as e:
        LOG.error("[단계: feed.xml 생성] %s", e)
        raise

    print("✅ feed updated: feed.xml")
    print("✅ episodes updated: data/episodes.json")


if __name__ == "__main__":
    main()
