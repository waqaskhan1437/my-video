<?php
/**
 * Debug GitHub Settings
 */
require_once 'config.php';

echo "<pre style='background:#1a1a1a;color:#00ff00;padding:15px;font-family:monospace;border-radius:5px;'>";
echo "╔═══════════════════════════════════════════╗\n";
echo "║     DEBUG: GitHub Settings Check         ║\n";
echo "╚═══════════════════════════════════════════╝\n\n";

// Check all GitHub settings
$settings = [
    'github_actions_enabled',
    'github_api_token',
    'github_repo_owner',
    'github_repo_name',
    'github_repo_branch'
];

echo "📋 Settings in Database:\n";
echo str_repeat("─", 50) . "\n";

foreach ($settings as $key) {
    $stmt = $pdo->prepare("SELECT setting_value FROM settings WHERE setting_key = ?");
    $stmt->execute([$key]);
    $value = $stmt->fetchColumn();

    $status = '';
    if ($key === 'github_actions_enabled') {
        $status = ($value === '1') ? ' ✅ ENABLED' : ' ❌ DISABLED';
    } elseif ($key === 'github_api_token') {
        if (!$value) {
            $status = ' ❌ EMPTY - NEEDS TOKEN';
        } elseif (strlen($value) < 10) {
            $status = ' ⚠ TOO SHORT - INVALID';
        } else {
            $status = ' ✅ TOKEN SET (' . strlen($value) . ' chars)';
        }
    } else {
        $status = ($value) ? ' ✅' : ' ❌ MISSING';
    }

    echo "\n$key\n";
    echo "  Value: " . ($value ?: '(empty)') . "\n";
    echo "  Status:$status\n";
}

echo "\n" . str_repeat("─", 50) . "\n";

// Check what run-sync.php will see
echo "\n🔍 What run-sync.php checks:\n";
echo str_repeat("─", 50) . "\n";

$githubEnabled = $pdo->query("SELECT setting_value FROM settings WHERE setting_key = 'github_actions_enabled'")->fetchColumn();
$githubToken = $pdo->query("SELECT setting_value FROM settings WHERE setting_key = 'github_api_token'")->fetchColumn();
$githubOwner = $pdo->query("SELECT setting_value FROM settings WHERE setting_key = 'github_repo_owner'")->fetchColumn();
$githubRepo = $pdo->query("SELECT setting_value FROM settings WHERE setting_key = 'github_repo_name'")->fetchColumn();

echo "\nCondition: if (\$githubEnabled === '1' && \$githubToken && \$githubOwner && \$githubRepo)\n\n";

echo "  githubEnabled === '1'    : " . ($githubEnabled === '1' ? '✅ TRUE' : '❌ FALSE (' . var_export($githubEnabled, true) . ')') . "\n";
echo "  githubToken (has value)  : " . (!empty($githubToken) ? '✅ TRUE' : '❌ FALSE (empty)') . "\n";
echo "  githubOwner (has value)  : " . (!empty($githubOwner) ? '✅ TRUE (' . $githubOwner . ')' : '❌ FALSE (empty)') . "\n";
echo "  githubRepo (has value)   : " . (!empty($githubRepo) ? '✅ TRUE (' . $githubRepo . ')' : '❌ FALSE (empty)') . "\n";

echo "\n" . str_repeat("─", 50) . "\n";

if ($githubEnabled === '1' && $githubToken && $githubOwner && $githubRepo) {
    echo "\n✅ ALL CONDITIONS MET - Will dispatch to GitHub\n";
} else {
    echo "\n❌ CONDITIONS NOT MET - Will show error:\n";
    echo "   'GitHub Actions not configured...'\n";

    echo "\n🔧 What's missing:\n";
    if ($githubEnabled !== '1') echo "   • GitHub Actions not enabled (enable checkbox in settings)\n";
    if (!$githubToken) echo "   • GitHub API Token is EMPTY (add token in settings)\n";
    if (!$githubOwner) echo "   • Repo Owner not set\n";
    if (!$githubRepo) echo "   • Repo Name not set\n";
}

echo "\n</pre>";
?>
