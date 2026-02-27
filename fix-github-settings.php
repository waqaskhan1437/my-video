<?php
/**
 * Quick Fix: Set GitHub Settings
 * Aapke GitHub repository details ko automatically set kar denga
 */

require_once 'config.php';

echo "<style>
body { font-family: monospace; background: #1a1a1a; color: #00ff00; padding: 20px; }
pre { background: #0a0a0a; padding: 15px; border-radius: 5px; border: 1px solid #00ff00; }
.success { color: #00ff00; }
.error { color: #ff0000; }
.warning { color: #ffff00; }
</style>";

echo "<pre>";
echo "╔════════════════════════════════════════╗\n";
echo "║  GitHub Settings Auto-Fix             ║\n";
echo "╚════════════════════════════════════════╝\n\n";

try {
    // Fixed values
    $updates = [
        'github_repo_owner' => 'waqaskhan1437',
        'github_repo_name' => 'my-video',
    ];

    echo "Setting values:\n";
    echo "─" . str_repeat("─", 36) . "─\n";

    foreach ($updates as $key => $value) {
        $stmt = $pdo->prepare("
            UPDATE settings
            SET setting_value = ?
            WHERE setting_key = ?
        ");
        $stmt->execute([$value, $key]);

        $rows = $stmt->rowCount();
        if ($rows > 0) {
            echo "<span class='success'>✅</span> $key = $value\n";
        } else {
            echo "<span class='warning'>⚠</span> $key (insert, not update)\n";
            $stmt = $pdo->prepare("
                INSERT INTO settings (setting_key, setting_value)
                VALUES (?, ?)
            ");
            $stmt->execute([$key, $value]);
            echo "   <span class='success'>✅ Inserted</span>\n";
        }
    }

    echo "\n" . str_repeat("─", 38) . "\n";
    echo "\n<span class='success'>✅ Settings Fixed!</span>\n\n";

    // Verify
    echo "Verification:\n";
    echo "─" . str_repeat("─", 36) . "─\n";

    $settings = $pdo->query("
        SELECT setting_key, setting_value
        FROM settings
        WHERE setting_key IN ('github_repo_owner', 'github_repo_name', 'github_actions_enabled', 'github_api_token')
        ORDER BY setting_key
    ")->fetchAll(PDO::FETCH_ASSOC);

    foreach ($settings as $row) {
        $val = $row['setting_value'];
        if ($val === '1') $val = '✅ ENABLED';
        elseif ($val === '0') $val = '❌ DISABLED';
        elseif (strlen($val) > 30) $val = substr($val, 0, 30) . '...';

        echo "  " . $row['setting_key'] . ": " . $val . "\n";
    }

    echo "\n" . str_repeat("─", 38) . "\n";
    echo "\n🎯 Next Step:\n";
    echo "   1. Go to Dashboard\n";
    echo "   2. Edit an Automation\n";
    echo "   3. Check 'GitHub Actions Runner'\n";
    echo "   4. Save\n";
    echo "   5. Click 'Run Automation'\n";
    echo "   6. Should now dispatch to GitHub! ✅\n\n";

    echo "<span class='success'>🎉 Ready to test!</span>\n";

} catch (Exception $e) {
    echo "<span class='error'>❌ Error: " . $e->getMessage() . "</span>\n";
}

echo "</pre>";
?>
