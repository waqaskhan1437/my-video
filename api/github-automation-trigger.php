<?php
/**
 * GitHub Automation Trigger Endpoint
 * Called by GitHub Actions workflows to trigger local automation
 */

declare(strict_types=1);

require_once __DIR__ . '/../config.php';

header('Content-Type: application/json');
header('X-GitHub-Workflow: true');

// Error handler
function gh_error(string $message, int $statusCode = 400): void {
    http_response_code($statusCode);
    echo json_encode([
        'ok' => false,
        'error' => $message,
        'timestamp' => date('Y-m-d H:i:s'),
    ]);
    exit;
}

// Success handler
function gh_success(array $data = []): void {
    http_response_code(200);
    echo json_encode(array_merge([
        'ok' => true,
        'timestamp' => date('Y-m-d H:i:s'),
    ], $data));
    exit;
}

try {
    // Verify API key from Authorization header
    $authHeader = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    if (empty($authHeader)) {
        gh_error('Authorization header missing', 401);
    }

    $apiKey = str_replace('Bearer ', '', $authHeader);
    $expectedKey = getenv('AUTOMATION_API_KEY') ?: $_ENV['AUTOMATION_API_KEY'] ?? '';

    // Fallback: check in settings table
    if (empty($expectedKey)) {
        try {
            $stmt = $pdo->prepare("SELECT setting_value FROM settings WHERE setting_key = ?");
            $stmt->execute(['automation_api_key']);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            $expectedKey = $row['setting_value'] ?? '';
        } catch (Exception $e) {
            // Settings table might not exist, continue with empty check
        }
    }

    if (empty($apiKey) || ($expectedKey && $apiKey !== $expectedKey)) {
        gh_error('Unauthorized: Invalid API key', 401);
    }

    // Get request method
    $method = strtoupper($_SERVER['REQUEST_METHOD'] ?? 'GET');

    if ($method !== 'POST') {
        gh_error('Only POST method is allowed', 405);
    }

    // Parse JSON payload
    $rawPayload = file_get_contents('php://input');
    $payload = json_decode($rawPayload, true);

    if (!is_array($payload)) {
        gh_error('Invalid JSON payload', 400);
    }

    $action = trim((string)($payload['action'] ?? ''));
    $githubRunId = (int)($payload['github_run_id'] ?? 0);

    if (empty($action)) {
        gh_error('Action is required', 400);
    }

    // Log the trigger
    $logDir = __DIR__ . '/../logs';
    if (!is_dir($logDir)) {
        mkdir($logDir, 0755, true);
    }

    $logFile = $logDir . '/github_triggers_' . date('Y-m-d') . '.log';
    $logEntry = sprintf(
        "[%s] Action: %s | Run ID: %d | IP: %s\n",
        date('Y-m-d H:i:s'),
        $action,
        $githubRunId,
        $_SERVER['REMOTE_ADDR'] ?? 'unknown'
    );
    file_put_contents($logFile, $logEntry, FILE_APPEND);

    // Handle different actions
    switch ($action) {
        case 'archive':
            handleArchiveAction($payload);
            break;

        case 'social':
            handleSocialAction($payload);
            break;

        case 'postforme':
            handlePostForMeAction($payload);
            break;

        case 'whisper':
            handleWhisperAction($payload);
            break;

        default:
            gh_error("Unknown action: {$action}", 400);
    }

} catch (Throwable $e) {
    error_log("GitHub Automation Trigger Error: " . $e->getMessage());
    gh_error("Internal server error: " . $e->getMessage(), 500);
}

/**
 * Handle Archive automation action
 */
function handleArchiveAction(array $payload): void {
    $mode = trim((string)($payload['mode'] ?? 'process_session'));
    $sessionId = trim((string)($payload['session_id'] ?? ''));

    // Log action
    error_log("Archive trigger: mode=$mode, session_id=$sessionId");

    // Call your existing automation.php or your automation class
    // Example:
    // include __DIR__ . '/../automation.php';
    // runArchiveAutomation($mode, $sessionId);

    gh_success([
        'action' => 'archive',
        'mode' => $mode,
        'session_id' => $sessionId,
        'message' => 'Archive automation triggered successfully',
        'github_run_id' => (int)($payload['github_run_id'] ?? 0),
    ]);
}

/**
 * Handle Social (YouTube) publishing action
 */
function handleSocialAction(array $payload): void {
    $maxItems = trim((string)($payload['max_items'] ?? '1'));
    $privacyStatus = trim((string)($payload['privacy_status'] ?? 'public'));
    $playlistId = trim((string)($payload['playlist_id'] ?? ''));

    // Log action
    error_log("Social trigger: max_items=$maxItems, privacy=$privacyStatus");

    // Call your existing social publishing code
    // Example:
    // include __DIR__ . '/../run-background.php';
    // publishToSocial($maxItems, $privacyStatus, $playlistId);

    gh_success([
        'action' => 'social',
        'max_items' => $maxItems,
        'privacy_status' => $privacyStatus,
        'playlist_id' => $playlistId ?: null,
        'message' => 'Social publishing automation triggered successfully',
        'github_run_id' => (int)($payload['github_run_id'] ?? 0),
    ]);
}

/**
 * Handle PostForMe automation action
 */
function handlePostForMeAction(array $payload): void {
    $runMode = trim((string)($payload['run_mode'] ?? 'run'));
    $automationId = trim((string)($payload['automation_id'] ?? ''));
    $accountFilter = trim((string)($payload['account_filter'] ?? ''));

    // Log action
    error_log("PostForMe trigger: mode=$runMode, automation_id=$automationId");

    // Call your existing PostForMe automation
    // Example:
    // include __DIR__ . '/../automation.php';
    // runPostForMeAutomation($automationId, $runMode, $accountFilter);

    gh_success([
        'action' => 'postforme',
        'run_mode' => $runMode,
        'automation_id' => $automationId,
        'account_filter' => $accountFilter ?: null,
        'message' => 'PostForMe automation triggered successfully',
        'github_run_id' => (int)($payload['github_run_id'] ?? 0),
    ]);
}

/**
 * Handle Whisper transcription action
 */
function handleWhisperAction(array $payload): void {
    $model = trim((string)($payload['whisper_model'] ?? 'base'));
    $language = trim((string)($payload['language'] ?? 'auto'));
    $runnerType = trim((string)($payload['runner_type'] ?? 'Linux'));

    // Log action
    error_log("Whisper trigger: model=$model, language=$language, runner=$runnerType");

    // Check if this should run on self-hosted runner
    $runnerPreference = trim((string)($payload['runner_preference'] ?? 'self-hosted'));

    if ($runnerPreference === 'self-hosted' && $runnerType !== 'Linux') {
        // Runner is not the self-hosted one, but was requested
        error_log("Warning: Self-hosted runner requested but got: $runnerType");
    }

    // Call your existing Whisper transcription
    // Example:
    // include __DIR__ . '/../automation.php';
    // runWhisperTranscription($model, $language);

    gh_success([
        'action' => 'whisper',
        'model' => $model,
        'language' => $language,
        'runner_type' => $runnerType,
        'message' => 'Whisper transcription automation triggered successfully',
        'github_run_id' => (int)($payload['github_run_id'] ?? 0),
    ]);
}

// End of file
?>
