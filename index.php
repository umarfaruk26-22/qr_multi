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
    } elseif ($lower !== 'content-length') {
        $req_headers[] = "{$name}: {$value}";
    }
}

if (!$cookie_found && !empty($_SERVER['HTTP_COOKIE'])) {
    $req_headers[] = "Cookie: " . $_SERVER['HTTP_COOKIE'];
}

curl_setopt($ch, CURLOPT_HTTPHEADER, $req_headers);

if (in_array($_SERVER['REQUEST_METHOD'], ['POST', 'PUT', 'PATCH', 'DELETE'])) {
    $input_body = file_get_contents('php://input');
    curl_setopt($ch, CURLOPT_POSTFIELDS, $input_body);
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
