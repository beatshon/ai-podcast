# AI Podcast 자동화 (crontab)

macOS에서 매일 `run_daily.py`를 자동 실행하는 방법.

---

## 1. crontab 등록 (macOS)

```bash
crontab -e
```

에디터가 열리면 다음 한 줄 추가 후 저장:

```cron
0 6 * * * /path/to/ai-podcast/.venv/bin/python /path/to/ai-podcast/scripts/run_daily.py >> /path/to/ai-podcast/logs/cron.log 2>&1
```

- `0 6 * * *` = 매일 오전 6시 0분
- `/path/to/ai-podcast`는 실제 프로젝트 경로로 바꾸세요.

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
which python
# 예: /Users/you/.../ai-podcast/.venv/bin/python
```

또는 경로만 출력:

```bash
realpath .venv/bin/python   # Linux
# macOS에 realpath 없으면:
python3 -c "import os; print(os.path.realpath('.venv/bin/python'))"
```

crontab에는 **절대 경로**를 써야 합니다 (예: `.../ai-podcast/.venv/bin/python`).

---

## 3. 매일 오전 6시 실행 예시

프로젝트 경로가 `/Users/jace/Desktop/ai-podcast`일 때:

```cron
0 6 * * * /Users/jace/Desktop/ai-podcast/.venv/bin/python /Users/jace/Desktop/ai-podcast/scripts/run_daily.py >> /Users/jace/Desktop/ai-podcast/logs/cron.log 2>&1
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
python scripts/run_daily.py
```

정상이면 `[RUN]` / `[OK]` / `--- run_daily done ---` 가 순서대로 출력됩니다.  
에러 시 해당 스크립트에서 중단되고 `[FAIL]` 및 에러 메시지가 출력됩니다.
