<?php
/**
 * Get Automation Configuration for GitHub Runner
 * Returns full automation settings as JSON for GitHub workflow to process
 */

header('Content-Type: application/json');
require_once '../config.php';

$automationId = intval($_GET['automation_id'] ?? 0);

if (!$automationId) {
    http_response_code(400);
    echo json_encode(['error' => 'automation_id required']);
    exit;
}

try {
    // Get automation configuration
    $stmt = $pdo->prepare("SELECT * FROM automation_settings WHERE id = ?");
    $stmt->execute([$automationId]);
    $automation = $stmt->fetch(PDO::FETCH_ASSOC);

    if (!$automation) {
        http_response_code(404);
        echo json_encode(['error' => 'Automation not found']);
        exit;
    }

    // Get API key details if needed
    $apiKey = null;
    if ($automation['api_key_id']) {
        $stmt = $pdo->prepare("SELECT * FROM api_keys WHERE id = ?");
        $stmt->execute([$automation['api_key_id']]);
        $apiKey = $stmt->fetch(PDO::FETCH_ASSOC);
    }

    // Get FTP settings from global settings if not using API key
    $ftpConfig = null;
    if (!$apiKey) {
        $ftpConfig = [
            'host' => $pdo->query("SELECT setting_value FROM settings WHERE setting_key = 'ftp_host'")->fetchColumn(),
            'user' => $pdo->query("SELECT setting_value FROM settings WHERE setting_key = 'ftp_user'")->fetchColumn(),
            'password' => $pdo->query("SELECT setting_value FROM settings WHERE setting_key = 'ftp_password'")->fetchColumn(),
            'port' => $pdo->query("SELECT setting_value FROM settings WHERE setting_key = 'ftp_port'")->fetchColumn() ?: 21,
            'path' => $pdo->query("SELECT setting_value FROM settings WHERE setting_key = 'ftp_path'")->fetchColumn() ?: '/',
        ];
    }

    // Get PostForMe account details if enabled
    $postformeAccounts = [];
    if ($automation['postforme_enabled']) {
        $accountIds = json_decode($automation['postforme_account_ids'] ?? '[]', true);
        if (is_array($accountIds) && !empty($accountIds)) {
            $placeholders = implode(',', array_fill(0, count($accountIds), '?'));
            $stmt = $pdo->prepare("SELECT * FROM postforme_accounts WHERE id IN ($placeholders)");
            $stmt->execute($accountIds);
            $postformeAccounts = $stmt->fetchAll(PDO::FETCH_ASSOC);
        }
    }

    // Build response with all configuration
    $response = [
        'automation' => $automation,
        'api_key' => $apiKey,
        'ftp_config' => $ftpConfig,
        'postforme_accounts' => $postformeAccounts,
        'github_run_id' => $_GET['run_id'] ?? null,
    ];

    http_response_code(200);
    echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);

} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database error: ' . $e->getMessage()]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error: ' . $e->getMessage()]);
}
?>
