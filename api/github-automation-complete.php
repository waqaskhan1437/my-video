<?php
/**
 * GitHub Automation Completion Notification
 * Called by workflow when done to log results
 */

header('Content-Type: application/json');
require_once '../config.php';

$input = json_decode(file_get_contents('php://input'), true);

$automationId = intval($input['automation_id'] ?? 0);
$githubRunId = $input['github_run_id'] ?? null;
$conclusion = $input['workflow_conclusion'] ?? 'unknown';
$completedAt = $input['completed_at'] ?? date('Y-m-d H:i:s');

if (!$automationId) {
    http_response_code(400);
    echo json_encode(['error' => 'automation_id required']);
    exit;
}

try {
    // Log workflow execution
    $logData = json_encode([
        'github_run_id' => $githubRunId,
        'conclusion' => $conclusion,
        'completed_at' => $completedAt,
        'workflow_url' => $githubRunId ? "https://github.com/waqaskhan1437/my-video/actions/runs/$githubRunId" : null
    ]);

    $pdo->prepare("UPDATE automation_settings SET last_run_at = NOW(), github_last_run_id = ? WHERE id = ?")
        ->execute([$githubRunId, $automationId]);

    http_response_code(200);
    echo json_encode([
        'success' => true,
        'message' => 'Completion recorded',
        'automation_id' => $automationId,
        'github_run_id' => $githubRunId
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
?>
