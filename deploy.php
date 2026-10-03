<?php
// ==============================================================================
// Nexalogic Automated Web Deployment & Health Controller
// Access via: https://qr.nexalogictechno.com/deploy.php?token=nexalogic2026
// ==============================================================================

define('DEPLOY_TOKEN', 'nexalogic2026');

$app_dir     = __DIR__;
$socket_path = $app_dir . '/gunicorn.sock';
$host        = '127.0.0.1';
$port        = 58432;
$boot_log    = $app_dir . '/gunicorn_boot.log';
$error_log   = $app_dir . '/gunicorn_error.log';
$access_log  = $app_dir . '/gunicorn_access.log';
$lock_file   = $app_dir . '/.gunicorn_boot.lock';

// Support both GET token, POST payload, and Webhook
$req_token = $_GET['token'] ?? $_POST['token'] ?? null;
$is_webhook = (isset($_SERVER['HTTP_X_GITHUB_EVENT']) || (isset($_SERVER['CONTENT_TYPE']) && strpos($_SERVER['CONTENT_TYPE'], 'application/json') !== false));

if ($is_webhook && !$req_token) {
    // If webhook query string has token
    if (isset($_GET['token']) && $_GET['token'] === DEPLOY_TOKEN) {
        $req_token = DEPLOY_TOKEN;
    }
}

if ($req_token !== DEPLOY_TOKEN) {
    header('HTTP/1.1 403 Forbidden');
    header('Content-Type: text/html; charset=utf-8');
    echo "<!DOCTYPE html><html><head><title>403 Forbidden</title><style>body{background:#0b0f19;color:#f8fafc;font-family:sans-serif;padding:40px;text-align:center;}</style></head><body>";
    echo "<h1>🔒 Authorization Required</h1><p>Please provide the deployment token to proceed.</p>";
    echo "<form method='GET'><input type='password' name='token' placeholder='Deployment Token' style='padding:10px 14px;border-radius:8px;border:1px solid #334155;background:#1e293b;color:#fff;'> <button type='submit' style='padding:10px 20px;border-radius:8px;background:#4f46e5;color:#fff;border:none;cursor:pointer;font-weight:600;'>Deploy</button></form>";
    echo "</body></html>";
    exit;
}

// Uncap timeout for pip install & git pull
@set_time_limit(300);
@ignore_user_abort(true);

if ($is_webhook) {
    header('Content-Type: application/json; charset=utf-8');
} else {
    header('Content-Type: text/html; charset=utf-8');
    echo "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><title>🚀 Deploying to Live Server</title>";
    echo "<style>
      body { background: #0b0f19; color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; padding: 32px; max-width: 900px; margin: 0 auto; line-height: 1.6; }
      h1 { color: #818cf8; margin-bottom: 20px; }
      .step { background: #1e293b; border-left: 4px solid #6366f1; padding: 16px 20px; border-radius: 8px; margin-bottom: 18px; }
      .step-title { font-weight: 700; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
      pre { background: #020617; padding: 14px; border-radius: 6px; overflow-x: auto; color: #38bdf8; font-size: 0.88rem; margin: 0; }
      .badge-ok { color: #10b981; font-weight: 600; }
      .badge-err { color: #ef4444; font-weight: 600; }
      .btn { display: inline-block; padding: 12px 24px; background: #10b981; color: #fff; text-decoration: none; border-radius: 8px; font-weight: 700; margin-top: 15px; }
    </style></head><body>";
    echo "<h1>🚀 Automated Live Server Deployment</h1>";
    @ob_flush();
    @flush();
}

$results = [];

// Step 1: Git Pull
$step1 = [];
@exec("cd {$app_dir} && git fetch origin main 2>&1 && git reset --hard origin/main 2>&1", $step1, $ret1);
$results['git_pull'] = ['code' => $ret1, 'output' => implode("\n", (array)$step1)];

if (!$is_webhook) {
    echo "<div class='step'><div class='step-title'>📥 1. Git Pull (origin/main) " . ($ret1 === 0 ? "<span class='badge-ok'>✅ Success</span>" : "<span class='badge-err'>⚠️ Exit {$ret1}</span>") . "</div><pre>" . htmlspecialchars($results['git_pull']['output']) . "</pre></div>";
    @ob_flush(); @flush();
}

// Step 2: Virtual Environment Setup & Dependencies
$venv_bin = $app_dir . '/venv/bin';
$venv_py = file_exists($venv_bin . '/python3') ? $venv_bin . '/python3' : $venv_bin . '/python';

if (!file_exists($venv_py)) {
    @exec("cd {$app_dir} && python3 -m venv venv 2>&1", $out_v, $ret_v);
    $venv_py = file_exists($venv_bin . '/python3') ? $venv_bin . '/python3' : $venv_bin . '/python';
}

$step2 = [];
@exec("cd {$app_dir} && {$venv_bin}/pip install --upgrade pip 2>&1 && {$venv_bin}/pip install -r requirements.txt gunicorn 2>&1", $step2, $ret2);
$results['pip_install'] = ['code' => $ret2, 'output' => implode("\n", (array)$step2)];

if (!$is_webhook) {
    echo "<div class='step'><div class='step-title'>📦 2. Python Virtualenv & Pip Install " . ($ret2 === 0 ? "<span class='badge-ok'>✅ Success</span>" : "<span class='badge-err'>⚠️ Exit {$ret2}</span>") . "</div><pre>" . htmlspecialchars(substr($results['pip_install']['output'], -1500)) . "</pre></div>";
    @ob_flush(); @flush();
}

// Step 3: Restart Backend Daemon
@exec("pkill -9 -f 'gunicorn' 2>&1");
@exec("pkill -9 -f '{$port}' 2>&1");
if (file_exists($socket_path)) @unlink($socket_path);
if (file_exists($lock_file)) @unlink($lock_file);

$env_export = "export PYTHONPATH=\"{$app_dir}:\$PYTHONPATH\" && export PATH=\"{$venv_bin}:/usr/local/bin:/usr/bin:/bin:\$PATH\"";
$runner = file_exists($venv_py) ? "{$venv_py} -m gunicorn" : "{$venv_bin}/gunicorn";
$full_cmd = "cd {$app_dir} && {$env_export} && nohup {$runner} --workers 2 --bind unix:{$socket_path} --bind {$host}:{$port} --timeout 120 --error-logfile {$error_log} --access-logfile {$access_log} --capture-output app:app > {$boot_log} 2>&1 < /dev/null &";
@exec($full_cmd);

// Wait up to 5 seconds to verify health
$alive = false;
for ($i = 0; $i < 15; $i++) {
    usleep(300000);
    $fp = file_exists($socket_path) ? @fsockopen("unix://{$socket_path}", -1, $e1, $e2, 0.3) : false;
    if (!$fp) {
        $fp = @fsockopen($host, $port, $e1, $e2, 0.3);
    }
    if ($fp) {
        fclose($fp);
        $alive = true;
        break;
    }
}
$results['backend_alive'] = $alive;

if (!$is_webhook) {
    echo "<div class='step'><div class='step-title'>🔄 3. Gunicorn Daemon Restart " . ($alive ? "<span class='badge-ok'>✅ Backend ALIVE</span>" : "<span class='badge-err'>⚠️ Starting up...</span>") . "</div>";
    echo "<p>" . ($alive ? "Gunicorn is running on Unix socket and port {$port}." : "Backend initiated in background.") . "</p>";
    if (file_exists($boot_log)) {
        echo "<pre><strong>Boot Log:</strong>\n" . htmlspecialchars(substr(file_get_contents($boot_log), -800)) . "</pre>";
    }
    echo "</div>";
    echo "<a href='/' class='btn'>🎉 View Live Website</a>";
    echo "</body></html>";
} else {
    echo json_encode([
        'status' => $alive ? 'success' : 'starting',
        'timestamp' => date('c'),
        'results' => $results
    ], JSON_PRETTY_PRINT);
}
