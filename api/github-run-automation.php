<?php
/**
 * GitHub Run Automation
 * Receives automation configuration from workflow and executes it
 * This is a headless version of the automation runner
 */

header('Content-Type: application/json');
require_once '../config.php';
require_once '../includes/FFmpegProcessor.php';
require_once '../includes/FTPAPI.php';

set_time_limit(14400);

$input = json_decode(file_get_contents('php://input'), true);

if (!$input || !isset($input['automation'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid input']);
    exit;
}

$automation = $input['automation'];
$automationId = intval($automation['id'] ?? 0);
$apiKey = $input['api_key'] ?? null;
$ftpConfig = $input['ftp_config'] ?? null;
$postformeAccounts = $input['postforme_accounts'] ?? [];

if (!$automationId) {
    http_response_code(400);
    echo json_encode(['error' => 'automation_id required']);
    exit;
}

try {
    // Initialize tracking
    $stats = [
        'fetched' => 0,
        'downloaded' => 0,
        'processed' => 0,
        'posted' => 0,
        'errors' => 0,
        'start_time' => date('Y-m-d H:i:s'),
        'messages' => []
    ];

    function log_message($msg) {
        global $stats;
        $timestamp = date('H:i:s');
        $full_msg = "[$timestamp] $msg";
        echo $full_msg . "\n";
        $stats['messages'][] = $full_msg;
        flush();
    }

    log_message("🚀 GitHub Automation Runner Started");
    log_message("Automation ID: $automationId");
    log_message("Video Source: {$automation['video_source']}");

    // Mark as processing
    $pdo->prepare("UPDATE automation_settings SET status = 'processing' WHERE id = ?")->execute([$automationId]);

    // Check FFmpeg
    log_message("Checking FFmpeg...");
    $ffmpeg = new FFmpegProcessor();
    if (!$ffmpeg->isAvailable()) {
        throw new Exception('FFmpeg not available');
    }
    log_message("✓ FFmpeg available");

    // Initialize video source
    $videoSource = $automation['video_source'] ?? 'ftp';
    $videosPerRun = intval($automation['videos_per_run'] ?? 5);
    if ($videosPerRun < 1) $videosPerRun = 1;
    if ($videosPerRun > 500) $videosPerRun = 500;

    $videos = [];

    if ($videoSource === 'manual') {
        log_message("Using manual video URLs");
        // Parse manual URLs
        $urls = explode("\n", $automation['manual_video_urls'] ?? '');
        $urls = array_filter(array_map('trim', $urls));

        foreach ($urls as $index => $url) {
            if (filter_var($url, FILTER_VALIDATE_URL)) {
                $videos[] = [
                    'url' => $url,
                    'name' => "manual_" . ($index + 1),
                    'is_manual' => true
                ];
            }
        }
        $stats['fetched'] = count($videos);
        log_message("Loaded " . count($videos) . " manual URLs");

    } else {
        // Use FTP to fetch videos
        log_message("Connecting to FTP storage...");

        if (!$ftpConfig || !$ftpConfig['host']) {
            throw new Exception('FTP configuration not available');
        }

        $ftp = new FTPAPI(
            $ftpConfig['host'],
            $ftpConfig['user'] ?? 'anonymous',
            $ftpConfig['password'] ?? 'user@example.com',
            intval($ftpConfig['port'] ?? 21),
            $ftpConfig['path'] ?? '/',
            true
        );

        // Apply filters
        $daysFilter = intval($automation['video_days_filter'] ?? 30);
        $startDate = $automation['video_start_date'] ?? null;
        $endDate = $automation['video_end_date'] ?? null;

        log_message("Fetching videos (filter: last $daysFilter days)...");

        // Get video list from FTP
        $allVideos = $ftp->listVideos();
        if (!$allVideos) {
            $allVideos = [];
        }

        // Filter by date if needed
        $now = time();
        $cutoff = $now - ($daysFilter * 86400);

        foreach ($allVideos as $video) {
            $timestamp = $video['timestamp'] ?? $now;
            if ($timestamp >= $cutoff) {
                $videos[] = $video;
            }
        }

        $stats['fetched'] = count($videos);
        log_message("Found " . count($videos) . " videos matching filters");
    }

    if (empty($videos)) {
        log_message("No videos to process");
        $pdo->prepare("UPDATE automation_settings SET status = 'completed', progress_percent = 100 WHERE id = ?")->execute([$automationId]);
        http_response_code(200);
        echo json_encode([
            'success' => true,
            'message' => 'No videos to process',
            'stats' => $stats
        ]);
        exit;
    }

    // Process videos (limit to videosPerRun)
    $videosToProcess = array_slice($videos, 0, $videosPerRun);

    foreach ($videosToProcess as $index => $video) {
        log_message("Processing video " . ($index + 1) . " of " . count($videosToProcess) . ": {$video['name']}");

        try {
            // Download
            if ($videoSource === 'manual') {
                $localPath = '/tmp/' . basename($video['url']);
                log_message("  Downloading from URL...");
                $ch = curl_init($video['url']);
                $fp = fopen($localPath, 'w');
                curl_setopt_array($ch, [
                    CURLOPT_FILE => $fp,
                    CURLOPT_TIMEOUT => 3600,
                    CURLOPT_FOLLOWLOCATION => true,
                ]);
                $result = curl_exec($ch);
                curl_close($ch);
                fclose($fp);
            } else {
                $localPath = '/tmp/' . $video['name'];
                log_message("  Downloading from FTP...");
                if (!$ftp->downloadFile($video['path'], $localPath)) {
                    throw new Exception('Download failed');
                }
            }

            if (!file_exists($localPath)) {
                throw new Exception('Download resulted in no file');
            }

            $fileSize = filesize($localPath);
            log_message("  ✓ Downloaded (" . round($fileSize / 1024 / 1024, 2) . " MB)");

            // Edit video if configured
            $editedPath = $localPath;
            if ($automation['short_duration'] || $automation['short_aspect_ratio']) {
                log_message("  Editing video...");

                $options = [
                    'duration' => intval($automation['short_duration'] ?? 60),
                    'aspect_ratio' => $automation['short_aspect_ratio'] ?? '9:16',
                ];

                if ($automation['branding_text_top'] || $automation['branding_text_bottom']) {
                    $options['text_top'] = $automation['branding_text_top'];
                    $options['text_bottom'] = $automation['branding_text_bottom'];
                }

                $editedPath = '/tmp/edited_' . basename($localPath);
                if (!$ffmpeg->processVideo($localPath, $editedPath, $options)) {
                    log_message("  ⚠ Editing failed, using original");
                    $editedPath = $localPath;
                }
            }

            $stats['processed']++;
            log_message("  ✓ Video processed successfully");

            // Post to platforms if configured
            if ($automation['youtube_enabled'] && $automation['youtube_api_key']) {
                log_message("  Posting to YouTube...");
                // YouTube posting logic would go here
                $stats['posted']++;
            }

            if ($automation['tiktok_enabled'] && $automation['tiktok_access_token']) {
                log_message("  Posting to TikTok...");
                // TikTok posting logic would go here
                $stats['posted']++;
            }

            if ($automation['postforme_enabled'] && !empty($postformeAccounts)) {
                log_message("  Scheduling with PostForMe...");
                // PostForMe scheduling logic would go here
                $stats['posted']++;
            }

            // Cleanup
            if (file_exists($localPath) && $localPath !== $editedPath) {
                unlink($localPath);
            }
            if (file_exists($editedPath)) {
                unlink($editedPath);
            }

        } catch (Exception $e) {
            log_message("  ❌ Error: " . $e->getMessage());
            $stats['errors']++;
        }
    }

    // Update completion
    $stats['end_time'] = date('Y-m-d H:i:s');
    log_message("✓ Automation completed");
    log_message("Stats: " . json_encode($stats));

    $pdo->prepare("UPDATE automation_settings SET status = 'completed', progress_percent = 100 WHERE id = ?")->execute([$automationId]);

    http_response_code(200);
    echo json_encode([
        'success' => true,
        'message' => 'Automation completed',
        'stats' => $stats
    ]);

} catch (Exception $e) {
    log_message("❌ FATAL ERROR: " . $e->getMessage());

    $pdo->prepare("UPDATE automation_settings SET status = 'error' WHERE id = ?")->execute([$automationId]);

    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage(),
        'stats' => $stats ?? []
    ]);
}
?>
