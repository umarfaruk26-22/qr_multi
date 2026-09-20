<?php
// High-Performance Reverse Proxy with Auto-Restart Daemon for Python Flask
$backend_host = '127.0.0.1';
$backend_port = 58432;
$backend_url = "http://{$backend_host}:{$backend_port}";
$app_dir = __DIR__;

function is_backend_alive($host, $port) {
    $fp = @fsockopen($host, $port, $errno, $errstr, 0.4);
    if ($fp) {
        fclose($fp);
        return true;
    }
    return false;
}

if (!is_backend_alive($backend_host, $backend_port)) {
    $cmd = "cd {$app_dir} && ./venv/bin/gunicorn --workers 2 --bind {$backend_host}:{$backend_port} app:app --daemon";
    exec($cmd);
    for ($i = 0; $i < 6; $i++) {
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
    echo "<h1>502 Bad Gateway</h1><p>Starting backend service... Please refresh.</p>";
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
