<?php
/**
 * Add GitHub Columns to automation_settings table
 * Run this once to add the required columns for GitHub Actions integration
 */

require_once 'config.php';

echo "========================================\n";
echo "Adding GitHub Columns to Database\n";
echo "========================================\n\n";

try {
    // Check if columns already exist
    $result = $pdo->query("SHOW COLUMNS FROM automation_settings LIKE 'github_%'");
    $existingColumns = $result->fetchAll();

    if (count($existingColumns) >= 2) {
        echo "✅ Columns already exist!\n\n";
        foreach ($existingColumns as $col) {
            echo "   ✓ " . $col['Field'] . " (" . $col['Type'] . ")\n";
        }
        echo "\nNo changes needed.\n";
        exit(0);
    }

    // Add columns
    echo "Adding columns...\n\n";

    $sql = "ALTER TABLE automation_settings
            ADD COLUMN IF NOT EXISTS github_runner_enabled TINYINT(1) DEFAULT 0,
            ADD COLUMN IF NOT EXISTS github_workflow VARCHAR(50) NULL";

    $pdo->exec($sql);
    echo "✅ Columns added successfully!\n\n";

    // Verify
    $result = $pdo->query("SHOW COLUMNS FROM automation_settings WHERE Field IN ('github_runner_enabled', 'github_workflow')");
    $rows = $result->fetchAll();

    echo "Verification:\n";
    foreach ($rows as $row) {
        echo "   ✓ " . $row['Field'] . " (" . $row['Type'] . ")\n";
    }

    echo "\n========================================\n";
    echo "✅ Database Ready for GitHub Actions!\n";
    echo "========================================\n";
    echo "\nYou can now:\n";
    echo "1. Create automations with GitHub runner option\n";
    echo "2. Select GitHub Actions workflows\n";
    echo "3. Run automations on GitHub servers instead of local PC\n";

} catch (PDOException $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
    exit(1);
} catch (Exception $e) {
    echo "❌ Unexpected Error: " . $e->getMessage() . "\n";
    exit(1);
}

?>
