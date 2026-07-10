@echo off
REM AIToolssolo auto-publish wrapper — run by Windows Scheduled Task (Mon/Wed/Fri).
REM Hits LOCAL Ollama, generates one post, commits + pushes to GitHub (Cloudflare deploys).
setlocal
set REPO=C:\Users\prin-win\aitoolssolo
set LOG=%REPO%\scripts\publish.log
set OLLAMA_HOST=http://localhost:11434
set OLLAMA_MODEL=qwen3:14b

echo [%date% %time%] --- auto-publish start --- >> %LOG%
cd /d %REPO% || (echo cd failed >> %LOG% & exit /b 1)

git config user.name "AI Tools Solo Bot"
git config user.email "bot@aitoolssolo.com"

py -3 scripts/generate_post.py >> %LOG% 2>&1
if errorlevel 1 (echo [%date% %time%] generation failed >> %LOG% & exit /b 1)

git add content/posts scripts/topics_done.txt
git diff --staged --quiet
if not errorlevel 1 (
  echo [%date% %time%] nothing staged, skip commit >> %LOG%
  goto :done
)
git commit -m "Auto-publish: new post %date:~6,4%-%date:~3,2%-%date:~0,2%" >> %LOG% 2>&1
git push >> %LOG% 2>&1
if errorlevel 1 (echo [%date% %time%] push failed >> %LOG% & exit /b 1)

:done
echo [%date% %time%] --- auto-publish done --- >> %LOG%
endlocal
