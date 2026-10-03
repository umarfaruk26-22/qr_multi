param(
    [string]$CommitMessage = "Update and sync changes"
)

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🚀 1. Staging and Committing to Git..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
git add .
$diff = git status --porcelain
if ($diff) {
    git commit -m $CommitMessage
} else {
    Write-Host "ℹ️  No new local changes to commit. Proceeding..." -ForegroundColor Yellow
}

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "📤 2. Pushing to GitHub (origin/main)..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
git push origin main

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "🌐 3. Deploying to Hostinger Live Server via SSH..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$SSH_HOST = "193.203.185.201"
$SSH_PORT = "65002"
$SSH_USER = "u121474497"

$REMOTE_CMD = @'
if [ -d ~/domains/nexalogictechno.com/public_html/qr ]; then
    cd ~/domains/nexalogictechno.com/public_html/qr
elif [ -d ~/domains/qr.nexalogictechno.com/public_html ]; then
    cd ~/domains/qr.nexalogictechno.com/public_html
elif [ -d ~/public_html/qr ]; then
    cd ~/public_html/qr
elif [ -d ~/public_html ]; then
    cd ~/public_html
else
    REPO_PATH=$(find ~ -maxdepth 4 -name .git -type d 2>/dev/null | head -n 1 | sed 's/\/.git//')
    if [ -n "$REPO_PATH" ]; then
        cd "$REPO_PATH"
    fi
fi

echo "📍 Current Server Directory: $(pwd)"
git pull origin main

if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing / updating dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "🔄 Restarting Gunicorn backend daemon..."
pkill -f "58432" 2>/dev/null || true
sleep 1

export PYTHONPATH="$(pwd):$PYTHONPATH"
export PATH="$(pwd)/venv/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

nohup ./venv/bin/gunicorn --workers 2 --bind 127.0.0.1:58432 --timeout 120 --error-logfile gunicorn_error.log --access-logfile gunicorn_access.log --capture-output app:app > gunicorn_boot.log 2>&1 &

sleep 2
if ps aux | grep -v grep | grep -q "58432"; then
    echo "✅ Gunicorn backend running on 127.0.0.1:58432"
else
    echo "⚠️ Backend not detected on 58432, checking boot log:"
    cat gunicorn_boot.log 2>/dev/null || true
fi

echo "✅ Live server updated successfully!"
'@

ssh -p $SSH_PORT -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" $REMOTE_CMD

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "🎉 Deployment Completed Successfully!" -ForegroundColor Green
Write-Host "🌐 Live URL: https://qr.nexalogictechno.com" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
