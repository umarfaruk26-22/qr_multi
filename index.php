<?php
// High-Performance Reverse Proxy with Auto-Restart Daemon for Python Flask
$backend_host = '127.0.0.1';
$backend_port = 58432;
$backend_url = "http://{$backend_host}:{$backend_port}";
$app_dir = __DIR__;
$boot_log = $app_dir . '/gunicorn_boot.log';
$error_log = $app_dir . '/gunicorn_error.log';

// Diagnostics endpoint: access with ?__diag=1 or /__diag
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
        'shell_exec_allowed' => function_exists('shell_exec') && !in_array('shell_exec', $disabled),
        'fsockopen_allowed' => function_exists('fsockopen') && !in_array('fsockopen', $disabled),
        'curl_allowed' => function_exists('curl_init'),
        'disabled_functions' => $disabled,
        'env_exists' => file_exists($app_dir . '/.env'),
        'venv_dir_exists' => is_dir($app_dir . '/venv'),
        'venv_python_exists' => file_exists($app_dir . '/venv/bin/python') || file_exists($app_dir . '/venv/bin/python3'),
        'venv_gunicorn_exists' => file_exists($app_dir . '/venv/bin/gunicorn'),
        'boot_log_exists' => file_exists($boot_log),
        'boot_log_content' => file_exists($boot_log) ? substr(file_get_contents($boot_log), -2000) : null,
        'error_log_exists' => file_exists($error_log),
        'error_log_content' => file_exists($error_log) ? substr(file_get_contents($error_log), -2000) : null,
    ];

    if ($diag['exec_allowed']) {
        @exec("python3 --version 2>&1", $py_ver);
        @exec("which python3 2>&1", $which_py);
        @exec("which gunicorn 2>&1", $which_gun);
        @exec("ps aux | grep -E 'gunicorn|python' | grep -v grep 2>&1", $ps_out);
        $diag['system_python_version'] = implode("\n", (array)$py_ver);
        $diag['which_python3'] = implode("\n", (array)$which_py);
        $diag['which_gunicorn'] = implode("\n", (array)$which_gun);
        $diag['running_processes'] = $ps_out;
        
        if ($diag['venv_python_exists']) {
            $venv_py = file_exists($app_dir . '/venv/bin/python3') ? $app_dir . '/venv/bin/python3' : $app_dir . '/venv/bin/python';
            @exec("cd {$app_dir} && {$venv_py} -c \"import app; print('App import SUCCESS')\" 2>&1", $app_import_test, $import_code);
            $diag['app_import_test'] = [
                'exit_code' => $import_code,
                'output' => implode("\n", (array)$app_import_test)
            ];
        }
    }

    echo json_encode($diag, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit;
}

function is_backend_alive($host, $port) {
    $fp = @fsockopen($host, $port, $errno, $errstr, 0.5);
    if ($fp) {
        fclose($fp);
        return true;
    }
    return false;
}

function start_backend($app_dir, $host, $port, $boot_log, $error_log) {
    // 1. Detect best python & gunicorn runners
    $venv_bin = $app_dir . '/venv/bin';
    $gunicorn_cmd = null;

    if (file_exists($venv_bin . '/gunicorn') && is_executable($venv_bin . '/gunicorn')) {
        $gunicorn_cmd = "{$venv_bin}/gunicorn";
    } elseif (file_exists($venv_bin . '/python3')) {
        $gunicorn_cmd = "{$venv_bin}/python3 -m gunicorn";
    } elseif (file_exists($venv_bin . '/python')) {
        $gunicorn_cmd = "{$venv_bin}/python -m gunicorn";
    } else {
        // Virtual environment does not exist, try auto-creating or use system python
        if (function_exists('exec')) {
            @exec("cd {$app_dir} && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt gunicorn >> {$boot_log} 2>&1");
            if (file_exists($venv_bin . '/gunicorn')) {
                $gunicorn_cmd = "{$venv_bin}/gunicorn";
            } elseif (file_exists($venv_bin . '/python3')) {
                $gunicorn_cmd = "{$venv_bin}/python3 -m gunicorn";
            }
        }
        if (!$gunicorn_cmd) {
            $gunicorn_cmd = "gunicorn";
        }
    }

    $env_export = "export PYTHONPATH=\"{$app_dir}:\$PYTHONPATH\" && export PATH=\"{$venv_bin}:/usr/local/bin:/usr/bin:/bin:\$PATH\"";
    $full_cmd = "cd {$app_dir} && {$env_export} && nohup {$gunicorn_cmd} --workers 2 --bind {$host}:{$port} --timeout 120 --error-logfile {$error_log} --access-logfile - --capture-output app:app >> {$boot_log} 2>&1 &";

    if (function_exists('exec')) {
        @exec($full_cmd);
    }
}

if (!is_backend_alive($backend_host, $backend_port)) {
    start_backend($app_dir, $backend_host, $backend_port, $boot_log, $error_log);
    for ($i = 0; $i < 8; $i++) {
        usleep(400000);
        if (is_backend_alive($backend_host, $backend_port)) {
            break;
        }
    }
}

$request_uri = $_SERVER['REQUEST_URI'];
$target_url = $backend_url . $request_uri;

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $target_url);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $_SERVER['REQUEST_METHOD']);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HEADER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, false);
curl_setopt($ch, CURLOPT_TIMEOUT, 60);

// Check if request is multipart/form-data
$content_type = $_SERVER['CONTENT_TYPE'] ?? $_SERVER['HTTP_CONTENT_TYPE'] ?? '';
$is_multipart = (stripos($content_type, 'multipart/form-data') !== false) || !empty($_FILES);

$req_headers = [];
$incoming_headers = function_exists('getallheaders') ? getallheaders() : [];

$cookie_found = false;
foreach ($incoming_headers as $name => $value) {
    $lower = strtolower($name);
    if ($lower === 'host') {
        $req_headers[] = "Host: " . ($_SERVER['HTTP_HOST'] ?? 'qr.nexalogictechno.com');
        $req_headers[] = "X-Forwarded-Host: " . ($_SERVER['HTTP_HOST'] ?? 'qr.nexalogictechno.com');
        $req_headers[] = "X-Forwarded-Proto: https";
        $req_headers[] = "X-Forwarded-For: " . ($_SERVER['REMOTE_ADDR'] ?? '');
    } elseif ($lower === 'cookie') {
        $req_headers[] = "Cookie: {$value}";
        $cookie_found = true;
    } elseif ($lower === 'content-type' && $is_multipart) {
        // Skip client content-type header for multipart so cURL generates its own multipart boundary header
        continue;
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

if ($response === false) {
    http_response_code(502);
    header('Content-Type: text/html; charset=utf-8');
    $curl_err = curl_error($ch);
    $boot_err = file_exists($boot_log) ? htmlspecialchars(substr(file_get_contents($boot_log), -1500)) : 'No boot log found.';
    $err_err = file_exists($error_log) ? htmlspecialchars(substr(file_get_contents($error_log), -1500)) : 'No error log found.';
    
    echo "<!DOCTYPE html><html><head><title>502 Bad Gateway</title><style>body{font-family:sans-serif;padding:30px;line-height:1.6;background:#0f172a;color:#f8fafc;}pre{background:#1e293b;padding:15px;border-radius:8px;overflow-x:auto;color:#38bdf8;}h1{color:#ef4444;}</style></head><body>";
    echo "<h1>502 Bad Gateway</h1><p>Starting backend service or backend is unavailable. Please refresh.</p>";
    echo "<p><small>cURL error: " . htmlspecialchars($curl_err) . "</small></p>";
    if (!empty($boot_err) && $boot_err !== 'No boot log found.') {
        echo "<h3>Startup Output:</h3><pre>{$boot_err}</pre>";
    }
    if (!empty($err_err) && $err_err !== 'No error log found.') {
        echo "<h3>Error Log:</h3><pre>{$err_err}</pre>";
    }
    echo "</body></html>";
    curl_close($ch);
    exit;
}

$header_size = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

$response_headers = substr($response, 0, $header_size);
$response_body = substr($response, $header_size);

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
