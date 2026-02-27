<?php
/**
 * Get Live Automation Status
 * Returns real-time progress and errors from automation execution
 */

header('Content-Type: application/json');
require_once '../config.php';

$automationId = intval($_GET['automation_id'] ?? 0);
$runId = $_GET['run_id'] ?? null;

if (!$automationId) {
    http_response_code(400);
    echo json_encode(['error' => 'automation_id required']);
    exit;
}

try {
    // Get automation record
    $stmt = $pdo->prepare("SELECT * FROM automation_settings WHERE id = ?");
    $stmt->execute([$automationId]);
    $automation = $stmt->fetch(PDO::FETCH_ASSOC);

    if (!$automation) {
        http_response_code(404);
        echo json_encode(['error' => 'Automation not found']);
        exit;
    }

    // Get current status and progress
    $status = $automation['status'] ?? 'idle';
    $progressPercent = intval($automation['progress_percent'] ?? 0);
    $progressData = $automation['progress_data'] ?? null;
    $lastProgressTime = $automation['last_progress_time'] ?? null;
    $lastRunAt = $automation['last_run_at'] ?? null;
    $lastError = $automation['last_error'] ?? null;

    // Parse progress data if available
    $progressDetails = [];
    if ($progressData) {
        $parsed = json_decode($progressData, true);
        if (is_array($parsed)) {
            $progressDetails = $parsed;
        }
    }

    // If GitHub enabled, fetch from GitHub Actions too
    $githubInfo = null;
    if ($automation['github_runner_enabled'] && $automation['github_last_run_id']) {
        $githubInfo = [
            'run_id' => $automation['github_last_run_id'],
            'url' => 'https://github.com/waqaskhan1437/my-video/actions/runs/' . $automation['github_last_run_id']
        ];
    }

    // Build response
    $response = [
        'automation_id' => $automationId,
        'automation_name' => $automation['name'],
        'status' => $status,
        'progress_percent' => $progressPercent,
        'progress_details' => $progressDetails,
        'last_progress_time' => $lastProgressTime,
        'last_run_at' => $lastRunAt,
        'last_error' => $lastError,
        'github_info' => $githubInfo,
        'github_enabled' => !empty($automation['github_runner_enabled']),
        'is_processing' => ($status === 'processing'),
        'timestamp' => date('Y-m-d H:i:s')
    ];

    http_response_code(200);
    echo json_encode($response, JSON_PRETTY_PRINT);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
?>
