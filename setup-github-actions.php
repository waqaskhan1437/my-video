<?php
/**
 * GitHub Actions Setup Helper
 * Initializes required GitHub settings in database
 */

require_once 'config.php';

echo "======================================\n";
echo "GitHub Actions Configuration Setup\n";
echo "======================================\n\n";

try {
    // Check if settings already exist
    $existingSettings = $pdo->query("
        SELECT setting_key
        FROM settings
        WHERE setting_key IN (
            'github_actions_enabled',
            'github_api_token',
            'github_repo_owner',
            'github_repo_name',
            'github_repo_branch'
        )
    ")->fetchAll(PDO::FETCH_COLUMN);

    echo "Current GitHub Settings:\n";
    if (empty($existingSettings)) {
        echo "  ⚠ No GitHub settings found\n\n";
    } else {
        echo "  ✓ Found: " . implode(", ", $existingSettings) . "\n\n";
    }

    // Insert default settings if not exist
    $settings = [
        'github_actions_enabled' => '0',
        'github_api_token' => '',
        'github_repo_owner' => 'waqaskhan1437',
        'github_repo_name' => 'my-video',
        'github_repo_branch' => 'main',
    ];

    echo "Initializing GitHub settings...\n";
    foreach ($settings as $key => $value) {
        $stmt = $pdo->prepare("
            INSERT IGNORE INTO settings (setting_key, setting_value)
            VALUES (?, ?)
        ");
        $stmt->execute([$key, $value]);
        echo "  ✓ $key\n";
    }

    echo "\n✅ GitHub settings initialized!\n\n";
    echo "Next Steps:\n";
    echo "1. Go to: http://localhost/video-workflow-edit-enabled/settings.php\n";
    echo "2. Scroll to 'GitHub Actions' section\n";
    echo "3. Enable GitHub Actions (checkbox)\n";
    echo "4. Paste your GitHub API Token\n";
    echo "5. Verify owner/repo/branch are correct\n";
    echo "6. Save settings\n";
    echo "7. Then try running an automation with GitHub enabled\n\n";

    echo "To get GitHub API Token:\n";
    echo "1. Go to: https://github.com/settings/tokens\n";
    echo "2. Click 'Generate new token (classic)'\n";
    echo "3. Give it a name: 'Video Automation'\n";
    echo "4. Select scopes: repo, workflow\n";
    echo "5. Click 'Generate token'\n";
    echo "6. Copy the token and paste in settings\n";

} catch (PDOException $e) {
    echo "❌ Database Error: " . $e->getMessage() . "\n";
    exit(1);
}
?>
