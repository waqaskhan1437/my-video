<?php
/**
 * Start Background Automation
 * Launches process that runs independently of browser
 * Queue system: Only one automation runs at a time to prevent CPU overload
 */

// Suppress HTML errors - return JSON errors only
error_reporting(0);
ini_set('display_errors', 0);

header('Content-Type: application/json');

try {
    require_once __DIR__ . '/../config.php';
} catch (Exception $e) {
    echo json_encode(['success' => false, 'error' => 'Config error: ' . $e->getMessage()]);
    exit;
}

if (!isset($pdo)) {
    echo json_encode(['success' => false, 'error' => 'Database connection failed']);
    exit;
}

$automationId = $_GET['id'] ?? $_POST['id'] ?? null;

if (!$automationId) {
    echo json_encode(['success' => false, 'error' => 'No automation ID']);
    exit;
}

// Check if already running
$stmt = $pdo->prepare("SELECT status FROM automation_settings WHERE id = ?");
$stmt->execute([$automationId]);
$automation = $stmt->fetch();

if (!$automation) {
    echo json_encode(['success' => false, 'error' => 'Automation not found']);
    exit;
}

if ($automation['status'] === 'processing') {
    echo json_encode(['success' => false, 'error' => 'Already running']);
    exit;
}

if ($automation['status'] === 'queued') {
    echo json_encode(['success' => false, 'error' => 'Already in queue']);
    exit;
}

// Check if another automation is already processing
$stmt = $pdo->query("SELECT id, name FROM automation_settings WHERE status = 'processing' LIMIT 1");
$runningAutomation = $stmt->fetch();

if ($runningAutomation) {
    // Add to queue instead of starting immediately
    $stmt = $pdo->prepare("UPDATE automation_settings SET status = 'queued', progress_percent = 0 WHERE id = ?");
    $stmt->execute([$automationId]);
    
    echo json_encode([
        'success' => true,
        'queued' => true,
        'message' => "Added to queue. Waiting for '{$runningAutomation['name']}' to complete.",
        'automationId' => $automationId
    ]);
    exit;
}

// Reset progress
try {
    $stmt = $pdo->prepare("UPDATE automation_settings SET status = 'processing', progress_percent = 0, progress_data = NULL WHERE id = ?");
    $stmt->execute([$automationId]);
} catch (Exception $e) {
    // Fallback if new columns don't exist yet
    $stmt = $pdo->prepare("UPDATE automation_settings SET status = 'processing' WHERE id = ?");
    $stmt->execute([$automationId]);
}

// Start background process
$scriptPath = realpath(__DIR__ . '/../run-background.php');
$logsDir = realpath(__DIR__ . '/../logs') ?: __DIR__ . '/../logs';
if (!is_dir($logsDir)) mkdir($logsDir, 0777, true);

if (PHP_OS_FAMILY === 'Windows') {
    // Windows XAMPP: Use PHP_BINARY which is the current PHP executable
    $phpPath = PHP_BINARY;
    
    // Fallback to common paths if needed
    if (!$phpPath || !file_exists($phpPath)) {
        $possiblePaths = [
            'C:\\xampp\\php\\php.exe',
            'C:\\xampp64\\php\\php.exe', 
            'D:\\xampp\\php\\php.exe'
        ];
        foreach ($possiblePaths as $path) {
            if (file_exists($path)) {
                $phpPath = $path;
                break;
            }
        }
    }
    
    // Simple start /B command - runs in background
    $logFile = $logsDir . '\\process-output.log';
    $cmd = 'start /B "" "' . $phpPath . '" "' . $scriptPath . '" ' . $automationId . ' > "' . $logFile . '" 2>&1';
    
    // Log the command for debugging
    file_put_contents($logsDir . '/start-cmd.log', date('Y-m-d H:i:s') . " - Command: $cmd\n", FILE_APPEND);
    
    pclose(popen($cmd, 'r'));
} else {
    // Linux: Use nohup and &
    $phpPath = PHP_BINARY ?: '/usr/bin/php';
    $cmd = "nohup {$phpPath} \"{$scriptPath}\" {$automationId} > /dev/null 2>&1 &";
    exec($cmd);
}

echo json_encode([
    'success' => true,
    'message' => 'Automation started in background',
    'automationId' => $automationId
]);
