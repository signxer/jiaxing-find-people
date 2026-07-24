<?php
/**
 * People Finder - 单文件API后端
 * PHP + SQLite，所有请求通过 action 参数分发
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// 数据库初始化
$dbPath = __DIR__ . '/data/app.db';
if (!is_dir(__DIR__ . '/data')) {
    mkdir(__DIR__ . '/data', 0755, true);
}

$db = new SQLite3($dbPath);
$db->busyTimeout(5000);
$db->exec('PRAGMA journal_mode=WAL');
$db->exec('PRAGMA busy_timeout=5000');

// 建表
$db->exec("
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ip TEXT UNIQUE NOT NULL,
        last_seen INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS find_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_ip TEXT NOT NULL,
        to_ip TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS favorites (
        user_ip TEXT NOT NULL,
        favorite_ip TEXT NOT NULL,
        PRIMARY KEY (user_ip, favorite_ip)
    );
    CREATE INDEX IF NOT EXISTS idx_find_to ON find_requests(to_ip, status);
    CREATE INDEX IF NOT EXISTS idx_find_from ON find_requests(from_ip, status);
");

// 自动清理过期数据(每次请求时顺带执行)
$now = time();
$expire = $now - 600; // 10分钟过期
$db->exec("DELETE FROM users WHERE last_seen < $expire");
$db->exec("DELETE FROM find_requests WHERE created_at < $expire AND status != 'pending'");
$db->exec("DELETE FROM find_requests WHERE created_at < " . ($now - 300)); // 5分钟未响应的请求也清理

// 获取请求参数
$action = $_GET['action'] ?? $_POST['action'] ?? '';
$input = json_decode(file_get_contents('php://input'), true) ?: $_POST;

function json_out($data) {
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

function get_ip() {
    // 优先从输入获取，其次从REMOTE_ADDR
    global $input;
    return $input['ip'] ?? $_SERVER['REMOTE_ADDR'] ?? '';
}

function is_online($last_seen) {
    return (time() - $last_seen) < 300; // 5分钟内视为在线
}

// 路由分发
switch ($action) {

    // 注册/更新用户
    case 'register':
        $name = trim($input['name'] ?? '');
        $ip = get_ip();
        if (!$name || !$ip) {
            json_out(['error' => '名字和IP不能为空']);
        }
        $stmt = $db->prepare("INSERT INTO users (name, ip, last_seen) VALUES (:name, :ip, :now)
                              ON CONFLICT(ip) DO UPDATE SET name=:name, last_seen=:now");
        $stmt->bindValue(':name', $name);
        $stmt->bindValue(':ip', $ip);
        $stmt->bindValue(':now', $now, SQLITE3_INTEGER);
        $stmt->execute();
        json_out(['ok' => true, 'name' => $name, 'ip' => $ip]);
        break;

    // 心跳
    case 'heartbeat':
        $ip = get_ip();
        if (!$ip) json_out(['error' => 'IP不能为空']);
        $db->exec("UPDATE users SET last_seen=$now WHERE ip='" . SQLite3::escapeString($ip) . "'");
        json_out(['ok' => true]);
        break;

    // 获取用户列表
    case 'users':
        $results = $db->query("SELECT name, ip, last_seen FROM users ORDER BY name");
        $users = [];
        while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
            $users[] = [
                'name' => $row['name'],
                'ip' => $row['ip'],
                'online' => is_online($row['last_seen'])
            ];
        }
        json_out($users);
        break;

    // 发送找人请求
    case 'find':
        $from_ip = $input['from_ip'] ?? get_ip();
        $to_ip = $input['to_ip'] ?? '';
        if (!$from_ip || !$to_ip) {
            json_out(['error' => '参数不完整']);
        }
        // 检查目标用户是否存在
        $stmt = $db->prepare("SELECT name FROM users WHERE ip=:ip");
        $stmt->bindValue(':ip', $to_ip);
        $target = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
        if (!$target) {
            json_out(['error' => '用户不存在']);
        }
        // 检查是否已有pending请求
        $stmt = $db->prepare("SELECT id FROM find_requests WHERE from_ip=:from AND to_ip=:to AND status='pending'");
        $stmt->bindValue(':from', $from_ip);
        $stmt->bindValue(':to', $to_ip);
        $existing = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
        if ($existing) {
            json_out(['error' => '已有待处理的请求']);
        }
        $stmt = $db->prepare("INSERT INTO find_requests (from_ip, to_ip, status, created_at) VALUES (:from, :to, 'pending', :now)");
        $stmt->bindValue(':from', $from_ip);
        $stmt->bindValue(':to', $to_ip);
        $stmt->bindValue(':now', $now, SQLITE3_INTEGER);
        $stmt->execute();
        json_out(['ok' => true, 'request_id' => $db->lastInsertRowID()]);
        break;

    // 检查是否有人找我
    case 'check':
        $ip = get_ip();
        if (!$ip) json_out(['error' => 'IP不能为空']);
        $stmt = $db->prepare("
            SELECT fr.id as request_id, u.name as from_name, fr.from_ip
            FROM find_requests fr
            JOIN users u ON u.ip = fr.from_ip
            WHERE fr.to_ip=:ip AND fr.status='pending'
            ORDER BY fr.created_at DESC LIMIT 1
        ");
        $stmt->bindValue(':ip', $ip);
        $result = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
        json_out($result ?: null);
        break;

    // 回应找人请求
    case 'respond':
        $request_id = intval($input['request_id'] ?? 0);
        $accepted = !empty($input['accepted']);
        if (!$request_id) {
            json_out(['error' => '请求ID不能为空']);
        }
        $status = $accepted ? 'accepted' : 'rejected';
        $db->exec("UPDATE find_requests SET status='$status' WHERE id=$request_id");
        json_out(['ok' => true]);
        break;

    // 检查自己发出的请求结果
    case 'result':
        $ip = get_ip();
        if (!$ip) json_out(['error' => 'IP不能为空']);
        $stmt = $db->prepare("
            SELECT fr.status, u.name as to_name
            FROM find_requests fr
            JOIN users u ON u.ip = fr.to_ip
            WHERE fr.from_ip=:ip AND fr.status IN ('accepted', 'rejected')
            ORDER BY fr.created_at DESC LIMIT 1
        ");
        $stmt->bindValue(':ip', $ip);
        $result = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
        if ($result) {
            // 删除已处理的请求，避免重复通知
            $db->exec("DELETE FROM find_requests WHERE from_ip='" . SQLite3::escapeString($ip) . "' AND status IN ('accepted', 'rejected')");
            json_out($result);
        } else {
            json_out(null);
        }
        break;

    // 同步接口(合并心跳+检查+结果)
    case 'sync':
        $ip = get_ip();
        if (!$ip) json_out(['error' => 'IP不能为空']);
        $escaped_ip = SQLite3::escapeString($ip);

        // 更新心跳
        $db->exec("UPDATE users SET last_seen=$now WHERE ip='$escaped_ip'");

        // 检查是否有人找我
        $stmt = $db->prepare("
            SELECT fr.id as request_id, u.name as from_name, fr.from_ip
            FROM find_requests fr
            JOIN users u ON u.ip = fr.from_ip
            WHERE fr.to_ip=:ip AND fr.status='pending'
            ORDER BY fr.created_at DESC LIMIT 1
        ");
        $stmt->bindValue(':ip', $ip);
        $incoming = $stmt->execute()->fetchArray(SQLITE3_ASSOC);

        // 检查自己请求的结果
        $stmt = $db->prepare("
            SELECT fr.id, fr.status, u.name as to_name
            FROM find_requests fr
            JOIN users u ON u.ip = fr.to_ip
            WHERE fr.from_ip=:ip AND fr.status IN ('accepted', 'rejected')
            ORDER BY fr.created_at DESC LIMIT 1
        ");
        $stmt->bindValue(':ip', $ip);
        $my_result = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
        if ($my_result) {
            $db->exec("DELETE FROM find_requests WHERE from_ip='$escaped_ip' AND status IN ('accepted', 'rejected')");
        }

        json_out([
            'ok' => true,
            'incoming' => $incoming ?: null,
            'my_result' => $my_result ?: null
        ]);
        break;

    // 切换收藏
    case 'favorite':
        $user_ip = $input['user_ip'] ?? get_ip();
        $favorite_ip = $input['favorite_ip'] ?? '';
        if (!$user_ip || !$favorite_ip) {
            json_out(['error' => '参数不完整']);
        }
        // 检查是否已收藏
        $stmt = $db->prepare("SELECT 1 FROM favorites WHERE user_ip=:u AND favorite_ip=:f");
        $stmt->bindValue(':u', $user_ip);
        $stmt->bindValue(':f', $favorite_ip);
        $exists = $stmt->execute()->fetchArray(SQLITE3_NUM);

        if ($exists) {
            $stmt = $db->prepare("DELETE FROM favorites WHERE user_ip=:u AND favorite_ip=:f");
            $stmt->bindValue(':u', $user_ip);
            $stmt->bindValue(':f', $favorite_ip);
            $stmt->execute();
            json_out(['ok' => true, 'action' => 'removed']);
        } else {
            $stmt = $db->prepare("INSERT INTO favorites (user_ip, favorite_ip) VALUES (:u, :f)");
            $stmt->bindValue(':u', $user_ip);
            $stmt->bindValue(':f', $favorite_ip);
            $stmt->execute();
            json_out(['ok' => true, 'action' => 'added']);
        }
        break;

    // 获取收藏列表
    case 'favorites':
        $ip = get_ip();
        if (!$ip) json_out(['error' => 'IP不能为空']);
        $stmt = $db->prepare("
            SELECT u.name, u.ip, u.last_seen
            FROM favorites f
            JOIN users u ON u.ip = f.favorite_ip
            WHERE f.user_ip=:ip
            ORDER BY u.name
        ");
        $stmt->bindValue(':ip', $ip);
        $results = $stmt->execute();
        $favorites = [];
        while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
            $favorites[] = [
                'name' => $row['name'],
                'ip' => $row['ip'],
                'online' => is_online($row['last_seen'])
            ];
        }
        json_out($favorites);
        break;

    default:
        json_out(['error' => '未知操作: ' . $action]);
}
