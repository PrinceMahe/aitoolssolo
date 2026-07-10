#!/bin/bash

REPO="$HOME/aitoolssolo"
LOG="$REPO/scripts/publish.log"

echo "=== $(date) ===" >> "$LOG"

cd "$REPO"

# Keep pi-local remote for reliable syncing when GitHub DNS fails on prin-pc
git remote get-url pi-local >/dev/null 2>&1 || git remote add pi-local "prin-pi:$REPO"

# --- PULL (non-fatal) ---
if git pull origin main >> "$LOG" 2>&1; then
  echo "Pulled directly from GitHub." >> "$LOG"
elif git fetch pi-local >> "$LOG" 2>&1 && git reset --hard pi-local/main >> "$LOG" 2>&1; then
  echo "Synced from prin-pi (GitHub DNS failed)." >> "$LOG"
else
  echo "WARNING: Could not sync. Proceeding with local state." >> "$LOG"
fi

# --- GENERATE ---
python3 scripts/generate_post.py >> "$LOG" 2>&1

# --- FIND NEW POST (untracked md in posts/) ---
NEW_POST=$(git ls-files --others --exclude-standard -- content/posts/ | grep '\.md$' | head -1)

if [ -z "$NEW_POST" ]; then
  echo "No new post generated." >> "$LOG"
  exit 0
fi
echo "Generated: $NEW_POST" >> "$LOG"

# --- COMMIT ---
git add content/posts/ scripts/topics_done.txt

if git diff --staged --quiet; then
  echo "Nothing to commit (post may already exist)." >> "$LOG"
  exit 0
fi

git commit -m "Auto-publish: new post $(date +%Y-%m-%d)"

# --- PUSH (direct first, prin-pi fallback) ---
if git push origin main >> "$LOG" 2>&1; then
  echo "Published directly. Done." >> "$LOG"
  exit 0
fi

echo "Direct push failed. Trying prin-pi relay..." >> "$LOG"

# Un-commit so prin-pi does the commit — prevents local/remote divergence
git reset HEAD~1

POST_BASENAME=$(basename "$NEW_POST")
if scp "$REPO/$NEW_POST" "prin-pi:$REPO/content/posts/$POST_BASENAME" >> "$LOG" 2>&1 && \
   scp "$REPO/scripts/topics_done.txt" "prin-pi:$REPO/scripts/topics_done.txt" >> "$LOG" 2>&1 && \
   ssh prin-pi "cd '$REPO' && git add 'content/posts/$POST_BASENAME' scripts/topics_done.txt && git commit -m 'Auto-publish: new post \$(date +%Y-%m-%d)' && git push origin main" >> "$LOG" 2>&1; then
  echo "Published via prin-pi." >> "$LOG"
  git fetch pi-local >> "$LOG" 2>&1 && git reset --hard pi-local/main >> "$LOG" 2>&1 || true
  echo "Local repo resynced from prin-pi." >> "$LOG"
else
  echo "ERROR: Both push paths failed. Post saved locally at: $REPO/$NEW_POST" >> "$LOG"
  exit 1
fi
