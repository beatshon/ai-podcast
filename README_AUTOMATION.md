# AI Podcast 자동화 (crontab)

macOS에서 매일 `run_daily.py`를 자동 실행하는 방법.

**실행 통일**: 프로젝트에서는 `python` 대신 **`python3`** 또는 **`.venv/bin/python3`**를 사용하세요. (환경에 `python`이 없을 수 있음)

---

## 1. crontab 등록 (macOS)

```bash
crontab -e
```

에디터가 열리면 다음 한 줄 추가 후 저장:

```cron
0 6 * * * /path/to/ai-podcast/.venv/bin/python3 /path/to/ai-podcast/scripts/run_daily.py >> /path/to/ai-podcast/logs/cron.log 2>&1
```

- `0 6 * * *` = 매일 오전 6시 0분
- `/path/to/ai-podcast`는 실제 프로젝트 경로로 바꾸세요.
- `python` 명령이 없는 환경에서는 `.venv/bin/python` 또는 `.venv/bin/python3`를 사용하세요.

등록 확인:

```bash
crontab -l
```

---

## 2. venv Python 경로 확인

프로젝트에서 가상환경 Python 절대 경로:

```bash
cd /path/to/ai-podcast
source .venv/bin/activate
which python3
# 예: /Users/you/.../ai-podcast/.venv/bin/python3
```

또는 경로만 출력 (crontab용):

```bash
# macOS
python3 -c "import os; print(os.path.realpath('.venv/bin/python3'))"
# Linux에 realpath 있으면:
# realpath .venv/bin/python3
```

crontab에는 **절대 경로**를 써야 합니다. `python`이 없으면 `.venv/bin/python3`를 사용하세요.

---

## 3. 매일 오전 6시 실행 예시

프로젝트 경로가 `/Users/jace/Desktop/ai-podcast`일 때:

```cron
0 6 * * * /Users/jace/Desktop/ai-podcast/.venv/bin/python3 /Users/jace/Desktop/ai-podcast/scripts/run_daily.py >> /Users/jace/Desktop/ai-podcast/logs/cron.log 2>&1
```

로그 디렉터리 없으면 먼저 생성:

```bash
mkdir -p /Users/jace/Desktop/ai-podcast/logs
```

---

## 4. 로그 확인

- **crontab에서 리다이렉트한 로그**  
  `logs/cron.log`  
  ```bash
  tail -f logs/cron.log
  # 또는
  cat logs/cron.log
  ```

- **run_daily.py 출력**  
  각 스크립트의 print는 위 로그에 쌓입니다. 실패 시 `[FAIL]` 및 stderr도 같은 파일에 기록됩니다.

- **crontab 실행 여부**  
  macOS에서는 메일 알림이 꺼져 있으면 실패해도 알림이 없을 수 있으므로, 주기적으로 `logs/cron.log`를 확인하는 것이 좋습니다.

---

## 5. 수동 테스트

프로젝트 루트에서:

```bash
cd /path/to/ai-podcast
source .venv/bin/activate
python3 scripts/run_daily.py
```

또는 가상환경 없이 절대 경로로:

```bash
/path/to/ai-podcast/.venv/bin/python3 /path/to/ai-podcast/scripts/run_daily.py
```

정상이면 `==> running:` / `✅` 가 순서대로 출력됩니다.  
에러 시 해당 스크립트에서 중단됩니다.

---

## 6. 개별 스크립트 실행 (python3 기준)

가상환경 활성화 후:

```bash
source .venv/bin/activate
python3 scripts/fetch_feeds.py
python3 scripts/generate_script.py
python3 scripts/tts_episode.py
python3 scripts/build_feed.py
python3 scripts/run_daily.py   # 위 4개 + publish_git 순서 실행
```

가상환경 없이 실행할 때는 `.venv/bin/python3` 절대 경로를 사용하세요.
