<?php
// ==============================================================================
// High-Performance Reverse Proxy & Auto-Healing Daemon for Python Flask
// Subdomain: https://qr.nexalogictechno.com
// ==============================================================================

$app_dir       = __DIR__;
$socket_path   = $app_dir . '/gunicorn.sock';
$backend_host  = '127.0.0.1';
$backend_port  = 58432;
$backend_url   = "http://{$backend_host}:{$backend_port}";
$boot_log      = $app_dir . '/gunicorn_boot.log';
$error_log     = $app_dir . '/gunicorn_error.log';
$access_log    = $app_dir . '/gunicorn_access.log';
$lock_file     = $app_dir . '/.gunicorn_boot.lock';
$venv_dir      = $app_dir . '/venv';

// Detect virtualenv python interpreter
$venv_python = null;
if (file_exists($venv_dir . '/bin/python3')) {
    $venv_python = $venv_dir . '/bin/python3';
} elseif (file_exists($venv_dir . '/bin/python')) {
    $venv_python = $venv_dir . '/bin/python';
}

// -----------------------------------------------------------------------------
// 1. Actions Dispatcher (?action=restart, ?action=pull, ?action=install)
// -----------------------------------------------------------------------------
$action = $_GET['action'] ?? null;
if ($action) {
    header('Content-Type: text/html; charset=utf-8');
    echo "<!DOCTYPE html><html><head><title>System Action: {$action}</title>";
    echo "<style>body{background:#0b0f19;color:#e2e8f0;font-family:system-ui,-apple-system,sans-serif;padding:30px;line-height:1.6;}pre{background:#1e293b;padding:16px;border-radius:10px;border:1px solid #334155;color:#38bdf8;overflow-x:auto;}a{color:#818cf8;text-decoration:none;font-weight:600;}.btn{display:inline-block;padding:10px 20px;background:#4f46e5;color:#fff;border-radius:8px;margin-top:15px;}</style></head><body>";
    echo "<h2>⚙️ Executing Action: " . htmlspecialchars($action) . "</h2>";

    if ($action === 'restart') {
        @exec("pkill -9 -f 'gunicorn' 2>&1");
        @exec("pkill -9 -f '{$backend_port}' 2>&1");
        if (file_exists($socket_path)) @unlink($socket_path);
        if (file_exists($lock_file)) @unlink($lock_file);
        echo "<pre>Killed previous Gunicorn processes and cleaned socket locks.</pre>";
        start_backend($app_dir, $socket_path, $backend_host, $backend_port, $boot_log, $error_log, $access_log, $lock_file, $venv_python);
        echo "<pre>Backend start initiated. Waiting for socket/port...</pre>";
        for ($i = 0; $i < 15; $i++) {
            usleep(300000);
            if (is_backend_alive($socket_path, $backend_host, $backend_port)) {
                echo "<p style='color:#10b981;'><strong>✅ Backend is now ALIVE and ready!</strong></p>";
                break;
            }
        }
    } elseif ($action === 'pull') {
        @exec("cd {$app_dir} && git pull origin main 2>&1", $out, $ret);
        echo "<h3>Git Pull Result (Exit Code: {$ret}):</h3>";
        echo "<pre>" . htmlspecialchars(implode("\n", (array)$out)) . "</pre>";
        @exec("pkill -9 -f 'gunicorn' 2>&1");
        if (file_exists($socket_path)) @unlink($socket_path);
        if (file_exists($lock_file)) @unlink($lock_file);
        start_backend($app_dir, $socket_path, $backend_host, $backend_port, $boot_log, $error_log, $access_log, $lock_file, $venv_python);
        echo "<p style='color:#10b981;'><strong>✅ Live repository pulled and backend restart triggered!</strong></p>";
    } elseif ($action === 'install') {
        set_time_limit(300);
        echo "<pre>Creating/verifying virtual environment and installing dependencies...</pre>";
        @exec("cd {$app_dir} && python3 -m venv venv 2>&1 && ./venv/bin/pip install --upgrade pip 2>&1 && ./venv/bin/pip install -r requirements.txt gunicorn 2>&1", $out, $ret);
        echo "<pre>" . htmlspecialchars(implode("\n", (array)$out)) . "</pre>";
        if ($ret === 0) {
            echo "<p style='color:#10b981;'><strong>✅ Dependencies installed successfully!</strong></p>";
        } else {
            echo "<p style='color:#ef4444;'><strong>⚠️ Setup exited with code {$ret}</strong></p>";
        }
    }
    echo "<br><a class='btn' href='" . htmlspecialchars(strtok($_SERVER['REQUEST_URI'], '?')) . "'>⬅️ Return to Website</a>";
    echo "</body></html>";
    exit;
}

// -----------------------------------------------------------------------------
// 2. Diagnostics Endpoint (?__diag=1 or /__diag)
// -----------------------------------------------------------------------------
if (isset($_GET['__diag']) || (isset($_SERVER['REQUEST_URI']) && strpos($_SERVER['REQUEST_URI'], '/__diag') === 0)) {
    header('Content-Type: application/json; charset=utf-8');
    $disabled = explode(',', (string)ini_get('disable_functions'));
    $disabled = array_map('trim', $disabled);

    $diag = [
        'timestamp' => date('c'),
        'php_version' => PHP_VERSION,
        'app_dir' => $app_dir,
        'user' => function_exists('get_current_user') ? get_current_user() : 'unknown',
        'exec_allowed' => function_exists('exec') && !in_array('exec', $disabled),
        'fsockopen_allowed' => function_exists('fsockopen') && !in_array('fsockopen', $disabled),
        'curl_allowed' => function_exists('curl_init'),
        'disabled_functions' => $disabled,
        'env_exists' => file_exists($app_dir . '/.env'),
        'venv_dir_exists' => is_dir($venv_dir),
        'venv_python_exists' => !empty($venv_python) && file_exists($venv_python),
        'socket_exists' => file_exists($socket_path),
        'backend_alive' => is_backend_alive($socket_path, $backend_host, $backend_port),
        'boot_log_tail' => file_exists($boot_log) ? substr(file_get_contents($boot_log), -1500) : null,
        'error_log_tail' => file_exists($error_log) ? substr(file_get_contents($error_log), -1500) : null,
    ];

    if ($diag['exec_allowed']) {
        @exec("python3 --version 2>&1", $py_ver);
        @exec("which python3 2>&1", $which_py);
        @exec("ps aux | grep -E 'gunicorn|python' | grep -v grep 2>&1", $ps_out);
        $diag['system_python_version'] = implode("\n", (array)$py_ver);
        $diag['which_python3'] = implode("\n", (array)$which_py);
        $diag['running_processes'] = $ps_out;
        
        if ($diag['venv_python_exists']) {
            @exec("cd {$app_dir} && {$venv_python} -c \"import app; print('App import SUCCESS')\" 2>&1", $app_import_test, $import_code);
            $diag['app_import_test'] = [
                'exit_code' => $import_code,
                'output' => implode("\n", (array)$app_import_test)
            ];
        }
    }

    echo json_encode($diag, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit;
}

// -----------------------------------------------------------------------------
// 3. Health Check
// -----------------------------------------------------------------------------
function is_backend_alive($socket_path, $host, $port) {
    // Check Unix domain socket first
    if (file_exists($socket_path)) {
        $fp = @fsockopen("unix://{$socket_path}", -1, $errno, $errstr, 0.3);
        if ($fp) {
            fclose($fp);
            return true;
        }
    }
    // Check TCP port
    $fp = @fsockopen($host, $port, $errno, $errstr, 0.3);
    if ($fp) {
        fclose($fp);
        return true;
    }
    return false;
}

// -----------------------------------------------------------------------------
// 4. Daemon Auto-Starter
// -----------------------------------------------------------------------------
function start_backend($app_dir, $socket_path, $host, $port, $boot_log, $error_log, $access_log, $lock_file, $venv_python) {
    if (!function_exists('exec')) {
        return;
    }

    // Prevent multiple requests from triggering concurrent spawns
    if (file_exists($lock_file) && (time() - filemtime($lock_file) < 20)) {
        return;
    }
    @touch($lock_file);

    // If socket exists but backend is not responding, remove stale socket
    if (file_exists($socket_path)) {
        @unlink($socket_path);
    }

    // Determine runner
    $gunicorn_cmd = null;
    $venv_bin = $app_dir . '/venv/bin';

    if ($venv_python && file_exists($venv_python)) {
        $gunicorn_cmd = "{$venv_python} -m gunicorn";
    } elseif (file_exists($venv_bin . '/gunicorn')) {
        $gunicorn_cmd = "{$venv_bin}/gunicorn";
    } else {
        // Trigger auto-creation in background if venv is missing
        $setup_cmd = "nohup bash -c \"cd {$app_dir} && python3 -m venv venv && ./venv/bin/pip install --upgrade pip && ./venv/bin/pip install -r requirements.txt gunicorn\" >> {$boot_log} 2>&1 < /dev/null &";
        @exec($setup_cmd);
        $gunicorn_cmd = "gunicorn";
    }

    $env_export = "export PYTHONPATH=\"{$app_dir}:\$PYTHONPATH\" && export PATH=\"{$venv_bin}:/usr/local/bin:/usr/bin:/bin:\$PATH\"";
    
    // Bind to both Unix domain socket and TCP port for maximum resilience
    $bind_args = "--bind unix:{$socket_path} --bind {$host}:{$port}";
    
    $full_cmd = "cd {$app_dir} && {$env_export} && nohup {$gunicorn_cmd} {$bind_args} --workers 2 --timeout 120 --error-logfile {$error_log} --access-logfile {$access_log} --capture-output app:app >> {$boot_log} 2>&1 < /dev/null &";

    @exec($full_cmd);
}

// -----------------------------------------------------------------------------
// 5. Ensure Backend is Running
// -----------------------------------------------------------------------------
if (!is_backend_alive($socket_path, $backend_host, $backend_port)) {
    start_backend($app_dir, $socket_path, $backend_host, $backend_port, $boot_log, $error_log, $access_log, $lock_file, $venv_python);
    
    // Patient polling: wait up to 8 seconds (20 iterations * 400ms)
    for ($i = 0; $i < 20; $i++) {
        usleep(400000);
        if (is_backend_alive($socket_path, $backend_host, $backend_port)) {
            if (file_exists($lock_file)) @unlink($lock_file);
            break;
        }
    }
}

// -----------------------------------------------------------------------------
// 6. Reverse Proxy with cURL
// -----------------------------------------------------------------------------
$request_uri = $_SERVER['REQUEST_URI'];
$use_socket = file_exists($socket_path);

$ch = curl_init();

if ($use_socket) {
    curl_setopt($ch, CURLOPT_UNIX_SOCKET_PATH, $socket_path);
    curl_setopt($ch, CURLOPT_URL, "http://localhost" . $request_uri);
} else {
    curl_setopt($ch, CURLOPT_URL, $backend_url . $request_uri);
}

curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $_SERVER['REQUEST_METHOD']);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HEADER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, false);
curl_setopt($ch, CURLOPT_TIMEOUT, 60);

// Detect multipart/form-data
$content_type = $_SERVER['CONTENT_TYPE'] ?? $_SERVER['HTTP_CONTENT_TYPE'] ?? '';
$is_multipart = (stripos($content_type, 'multipart/form-data') !== false) || !empty($_FILES);

$req_headers = [];
$incoming_headers = function_exists('getallheaders') ? getallheaders() : [];

$cookie_found = false;
$host_header = $_SERVER['HTTP_HOST'] ?? 'qr.nexalogictechno.com';

foreach ($incoming_headers as $name => $value) {
    $lower = strtolower($name);
    if ($lower === 'host') {
        $req_headers[] = "Host: {$host_header}";
        $req_headers[] = "X-Forwarded-Host: {$host_header}";
        $req_headers[] = "X-Forwarded-Proto: https";
        $req_headers[] = "X-Forwarded-For: " . ($_SERVER['REMOTE_ADDR'] ?? '');
    } elseif ($lower === 'cookie') {
        $req_headers[] = "Cookie: {$value}";
        $cookie_found = true;
    } elseif ($lower === 'content-type' && $is_multipart) {
        continue; // Let cURL set multipart boundary
    } elseif ($lower !== 'content-length') {
        $req_headers[] = "{$name}: {$value}";
    }
}

if (!$cookie_found && !empty($_SERVER['HTTP_COOKIE'])) {
    $req_headers[] = "Cookie: " . $_SERVER['HTTP_COOKIE'];
}

curl_setopt($ch, CURLOPT_HTTPHEADER, $req_headers);

function flatten_array_for_curl($data, $prefix = '') {
    $result = [];
    foreach ($data as $key => $value) {
        $full_key = $prefix === '' ? (string)$key : "{$prefix}[{$key}]";
        if (is_array($value)) {
            $result = array_merge($result, flatten_array_for_curl($value, $full_key));
        } else {
            $result[$full_key] = (string)$value;
        }
    }
    return $result;
}

function process_files_for_curl($files, $prefix = '') {
    $result = [];
    foreach ($files as $name => $file) {
        $key = $prefix === '' ? $name : "{$prefix}[{$name}]";
        if (isset($file['tmp_name']) && is_array($file['tmp_name'])) {
            $sub_files = [];
            foreach ($file['tmp_name'] as $sub_k => $sub_v) {
                $sub_files[$sub_k] = [
                    'name' => $file['name'][$sub_k],
                    'type' => $file['type'][$sub_k],
                    'tmp_name' => $file['tmp_name'][$sub_k],
                    'error' => $file['error'][$sub_k],
                    'size' => $file['size'][$sub_k],
                ];
            }
            $result = array_merge($result, process_files_for_curl($sub_files, $key));
        } elseif (isset($file['error'])) {
            if ($file['error'] === UPLOAD_ERR_OK && !empty($file['tmp_name']) && file_exists($file['tmp_name'])) {
                $mime = !empty($file['type']) ? $file['type'] : (function_exists('mime_content_type') ? @mime_content_type($file['tmp_name']) : 'application/octet-stream');
                $result[$key] = new CURLFile($file['tmp_name'], $mime, $file['name']);
            }
        }
    }
    return $result;
}

if (in_array($_SERVER['REQUEST_METHOD'], ['POST', 'PUT', 'PATCH', 'DELETE'])) {
    if ($is_multipart) {
        $post_fields = flatten_array_for_curl($_POST);
        $file_fields = process_files_for_curl($_FILES);
        $all_fields = array_merge($post_fields, $file_fields);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $all_fields);
    } else {
        $input_body = file_get_contents('php://input');
        curl_setopt($ch, CURLOPT_POSTFIELDS, $input_body);
    }
}

$response = curl_exec($ch);

// -----------------------------------------------------------------------------
// 7. Error & Healing Screen (502 Bad Gateway)
// -----------------------------------------------------------------------------
if ($response === false) {
    http_response_code(502);
    header('Content-Type: text/html; charset=utf-8');
    
    $curl_err = curl_error($ch);
    curl_close($ch);
    
    $boot_err = file_exists($boot_log) ? htmlspecialchars(substr(file_get_contents($boot_log), -1200)) : 'No boot output found.';
    $err_err = file_exists($error_log) ? htmlspecialchars(substr(file_get_contents($error_log), -1200)) : 'No error log found.';
    $clean_uri = htmlspecialchars(strtok($_SERVER['REQUEST_URI'], '?'));

    echo <<<HTML
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="4">
  <title>502 — Initializing Service | Nexalogic</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: rgba(30, 41, 59, 0.7);
      --border: rgba(255, 255, 255, 0.1);
      --primary: #4f46e5;
      --accent: #06b6d4;
      --text: #f8fafc;
      --muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      backdrop-filter: blur(16px);
      border-radius: 20px;
      padding: 40px;
      max-width: 680px;
      width: 100%;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
      text-align: center;
    }
    .spinner-box {
      margin-bottom: 24px;
    }
    .spinner {
      display: inline-block;
      width: 48px;
      height: 48px;
      border: 4px solid rgba(99, 102, 241, 0.2);
      border-top-color: #6366f1;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    h1 {
      font-family: 'Outfit', sans-serif;
      font-size: 1.85rem;
      font-weight: 700;
      margin-bottom: 12px;
      background: linear-gradient(135deg, #a5b4fc, #38bdf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    p {
      color: var(--muted);
      font-size: 0.98rem;
      margin-bottom: 24px;
      line-height: 1.6;
    }
    .btn-group {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      justify-content: center;
      margin-bottom: 24px;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 20px;
      border-radius: 10px;
      font-weight: 600;
      font-size: 0.9rem;
      text-decoration: none;
      transition: all 0.2s;
    }
    .btn-primary { background: var(--primary); color: #fff; }
    .btn-primary:hover { background: #4338ca; }
    .btn-secondary { background: rgba(255, 255, 255, 0.08); color: #e2e8f0; border: 1px solid var(--border); }
    .btn-secondary:hover { background: rgba(255, 255, 255, 0.15); }
    details {
      text-align: left;
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 18px;
      margin-top: 14px;
    }
    summary {
      cursor: pointer;
      font-weight: 600;
      font-size: 0.88rem;
      color: #cbd5e1;
    }
    pre {
      margin-top: 12px;
      background: #020617;
      padding: 14px;
      border-radius: 8px;
      font-size: 0.8rem;
      color: #38bdf8;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="spinner-box">
      <div class="spinner"></div>
    </div>
    <h1>Backend Service Starting...</h1>
    <p>
      The Python Flask service daemon is booting up or recovering automatically.
      This page will refresh automatically in <strong>4 seconds</strong>.
    </p>

    <div class="btn-group">
      <a href="{$clean_uri}" class="btn btn-primary">🔄 Refresh Now</a>
      <a href="{$clean_uri}?action=restart" class="btn btn-secondary">⚡ Force Restart</a>
      <a href="{$clean_uri}?action=pull" class="btn btn-secondary">🚀 Sync Git</a>
      <a href="{$clean_uri}?action=install" class="btn btn-secondary">🛠️ Repair Env</a>
    </div>

    <details>
      <summary>🔍 Diagnostics & Error Logs (Click to expand)</summary>
      <p style="margin: 8px 0 4px; font-size: 0.82rem; color: #94a3b8;">cURL error: {$curl_err}</p>
      <pre><strong>Boot Log:</strong><br>{$boot_err}<br><br><strong>Error Log:</strong><br>{$err_err}</pre>
    </details>
  </div>
</body>
</html>
HTML;
    exit;
}

// -----------------------------------------------------------------------------
// 8. Output Response
// -----------------------------------------------------------------------------
$header_size = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
$http_code   = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

$response_headers = substr($response, 0, $header_size);
$response_body    = substr($response, $header_size);

http_response_code($http_code);

$raw_headers = preg_split("/\r\n|\n|\r/", $response_headers);
foreach ($raw_headers as $line) {
    $line = trim($line);
    if (!empty($line) && strpos($line, ':') !== false) {
        $lower_line = strtolower($line);
        if (strpos($lower_line, 'transfer-encoding:') === false && strpos($lower_line, 'content-length:') === false) {
            header($line, false);
        }
    }
}

echo $response_body;
