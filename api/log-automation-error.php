<?php
/**
 * Log Automation Error
 * Called by workflows to log errors and progress in real-time
 */

header('Content-Type: application/json');
require_once '../config.php';

$input = json_decode(file_get_contents('php://input'), true);

$automationId = intval($input['automation_id'] ?? 0);
$error = $input['error'] ?? '';
$step = $input['step'] ?? 'unknown';
$severity = $input['severity'] ?? 'error'; // error, warning, info
$progressPercent = intval($input['progress_percent'] ?? 0);
$message = $input['message'] ?? '';

if (!$automationId) {
    http_response_code(400);
    echo json_encode(['error' => 'automation_id required']);
    exit;
}

try {
    // Log error to database
    $errorMessage = "[$step] [$severity] " . ($error ?: $message);

    // Create log entry
    $stmt = $pdo->prepare("
        INSERT INTO automation_logs (automation_id, status, message, created_at)
        VALUES (?, ?, ?, NOW())
    ");
    $stmt->execute([$automationId, $severity, $errorMessage]);

    // Update automation record with latest error
    if ($severity === 'error') {
        $stmt = $pdo->prepare("
            UPDATE automation_settings
            SET last_error = ?,
                status = 'error'
            WHERE id = ?
        ");
        $stmt->execute([$errorMessage, $automationId]);
    }

    // Update progress if provided
    if ($progressPercent > 0) {
        $progressData = json_encode([
            'step' => $step,
            'severity' => $severity,
            'message' => $message ?: $error,
            'time' => date('H:i:s')
        ]);

        $stmt = $pdo->prepare("
            UPDATE automation_settings
            SET progress_percent = ?,
                progress_data = ?
            WHERE id = ?
        ");
        $stmt->execute([$progressPercent, $progressData, $automationId]);
    }

    http_response_code(200);
    echo json_encode([
        'success' => true,
        'message' => 'Error logged',
        'log_id' => $pdo->lastInsertId()
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
?>
