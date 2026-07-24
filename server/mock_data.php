<?php
/**
 * 生成测试用的mock数据
 * 运行: php mock_data.php
 */

$dbPath = __DIR__ . '/data/app.db';
if (!is_dir(__DIR__ . '/data')) {
    mkdir(__DIR__ . '/data', 0755, true);
}

$db = new SQLite3($dbPath);
$db->exec('PRAGMA journal_mode=WAL');

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
");

$now = time();

// 模拟用户
$mock_users = [
    ['name' => '张三',   'ip' => '192.168.1.100'],
    ['name' => '李四',   'ip' => '192.168.1.101'],
    ['name' => '王五',   'ip' => '192.168.1.102'],
    ['name' => '赵六',   'ip' => '192.168.1.103'],
    ['name' => '测试小明', 'ip' => '192.168.1.200'],
    ['name' => '测试小红', 'ip' => '192.168.1.201'],
];

echo "=== 嘉行找人 - Mock数据生成 ===\n\n";

foreach ($mock_users as $u) {
    $stmt = $db->prepare("INSERT OR REPLACE INTO users (name, ip, last_seen) VALUES (:name, :ip, :now)");
    $stmt->bindValue(':name', $u['name']);
    $stmt->bindValue(':ip', $u['ip']);
    $stmt->bindValue(':now', $now, SQLITE3_INTEGER);
    $stmt->execute();
    echo "  ✓ 添加用户: {$u['name']} ({$u['ip']})\n";
}

// 给当前用户(127.0.0.1)添加一些收藏
$my_ip = '127.0.0.1';
$fav_ips = ['192.168.1.100', '192.168.1.101'];
foreach ($fav_ips as $fip) {
    $stmt = $db->prepare("INSERT OR IGNORE INTO favorites (user_ip, favorite_ip) VALUES (:u, :f)");
    $stmt->bindValue(':u', $my_ip);
    $stmt->bindValue(':f', $fip);
    $stmt->execute();
}

// 添加一条找人请求(模拟张三在找你)
$stmt = $db->prepare("INSERT INTO find_requests (from_ip, to_ip, status, created_at) VALUES ('192.168.1.100', :to_ip, 'pending', :now)");
$stmt->bindValue(':to_ip', $my_ip);
$stmt->bindValue(':now', $now, SQLITE3_INTEGER);
$stmt->execute();

echo "\n  ✓ 已添加收藏: 张三、李四\n";
echo "  ✓ 已添加待处理的找人请求: 张三 → 你\n";
echo "\n数据库: $dbPath\n";
echo "完成！启动服务器后打开客户端即可看到mock数据。\n";
