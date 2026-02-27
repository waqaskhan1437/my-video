<?php
declare(strict_types=1);

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/GitHubActionsAPI.php';

header('Content-Type: application/json');

function gh_json(array $payload, int $statusCode = 200): void
{
    http_response_code($statusCode);
    echo json_encode($payload);
    exit;
}

function gh_clean_string($value): string
{
    return trim((string)$value);
}

function gh_parse_inputs_json(string $raw): array
{
    $raw = trim($raw);
    if ($raw === '') {
        return [];
    }
    $decoded = json_decode($raw, true);
    if (!is_array($decoded)) {
        throw new RuntimeException('inputs_json must be valid JSON object');
    }
    return $decoded;
}

try {
    $service = new GitHubActionsAPI($pdo);
    $method = strtoupper((string)($_SERVER['REQUEST_METHOD'] ?? 'GET'));
    $action = gh_clean_string($_GET['action'] ?? $_POST['action'] ?? '');

    if ($method === 'POST' && $action === 'save_settings') {
        $enabled = isset($_POST['enabled']) ? '1' : '0';

        $update = [
            'enabled' => $enabled,
            'repo_owner' => gh_clean_string($_POST['repo_owner'] ?? ''),
            'repo_name' => gh_clean_string($_POST['repo_name'] ?? ''),
            'repo_branch' => gh_clean_string($_POST['repo_branch'] ?? 'main'),
            'runner_preference' => gh_clean_string($_POST['runner_preference'] ?? 'github-hosted'),
            'self_hosted_label' => gh_clean_string($_POST['self_hosted_label'] ?? 'self-hosted'),
            'workflow_archive' => gh_clean_string($_POST['workflow_archive'] ?? 'pipeline.yml'),
            'workflow_social' => gh_clean_string($_POST['workflow_social'] ?? 'social-publish.yml'),
            'workflow_postforme' => gh_clean_string($_POST['workflow_postforme'] ?? 'archive-postforme.yml'),
            'workflow_whisper' => gh_clean_string($_POST['workflow_whisper'] ?? 'whisper-cpu.yml'),
        ];

        $apiToken = gh_clean_string($_POST['api_token'] ?? '');
        $clearToken = isset($_POST['clear_token']) && (string)$_POST['clear_token'] === '1';
        if ($clearToken) {
            $update['api_token'] = '';
        } elseif ($apiToken !== '') {
            $update['api_token'] = $apiToken;
        }

        $service->saveSettings($update);
        gh_json(['ok' => true, 'message' => 'GitHub settings saved']);
    }

    if ($method === 'POST' && $action === 'dispatch') {
        $settings = $service->getSettings(false);
        if ($settings['enabled'] !== '1') {
            gh_json(['ok' => false, 'error' => 'GitHub automation is disabled. Enable it first.'], 400);
        }

        $workflow = gh_clean_string($_POST['workflow'] ?? '');
        $workflowType = gh_clean_string($_POST['workflow_type'] ?? '');

        if ($workflow === '' && $workflowType !== '') {
            $map = [
                'archive' => $settings['workflow_archive'] ?? '',
                'social' => $settings['workflow_social'] ?? '',
                'postforme' => $settings['workflow_postforme'] ?? '',
                'whisper' => $settings['workflow_whisper'] ?? '',
            ];
            $workflow = $map[$workflowType] ?? '';
        }

        if ($workflow === '') {
            gh_json(['ok' => false, 'error' => 'Workflow file/id is required'], 400);
        }

        $ref = gh_clean_string($_POST['ref'] ?? ($settings['repo_branch'] ?? 'main'));
        $inputsJsonRaw = (string)($_POST['inputs_json'] ?? '{}');
        $inputs = gh_parse_inputs_json($inputsJsonRaw);

        // Helper defaults for whisper runner preference
        if ($workflowType === 'whisper') {
            if (!isset($inputs['runner_preference'])) {
                $inputs['runner_preference'] = $settings['runner_preference'] ?? 'github-hosted';
            }
            if (!isset($inputs['self_hosted_label'])) {
                $inputs['self_hosted_label'] = $settings['self_hosted_label'] ?? 'self-hosted';
            }
        }

        $dispatch = $service->dispatchWorkflow($workflow, $ref, $inputs);
        if (!$dispatch['success']) {
            gh_json([
                'ok' => false,
                'error' => $dispatch['error'] ?: ('Dispatch failed with status ' . $dispatch['status']),
                'status_code' => $dispatch['status'],
            ], 400);
        }

        $actionsUrl = sprintf(
            'https://github.com/%s/%s/actions',
            rawurlencode((string)$settings['repo_owner']),
            rawurlencode((string)$settings['repo_name'])
        );

        gh_json([
            'ok' => true,
            'message' => 'Workflow dispatch requested successfully',
            'workflow' => $workflow,
            'ref' => $ref,
            'actions_url' => $actionsUrl,
        ]);
    }

    if ($method === 'GET' && ($action === 'status' || $action === 'runs')) {
        $settingsMasked = $service->getSettings(true);
        $settingsRaw = $service->getSettings(false);
        $configured = $service->isConfigured();

        if (!$configured) {
            gh_json([
                'ok' => true,
                'configured' => false,
                'settings' => $settingsMasked,
                'message' => 'Configure repo owner, repo name and API token first.',
                'workflows' => [],
                'runs' => [],
                'runners' => [],
                'summary' => [
                    'workflow_count' => 0,
                    'running_count' => 0,
                    'failed_count_24h' => 0,
                    'online_self_hosted' => 0,
                ],
            ]);
        }

        $workflowFilter = gh_clean_string($_GET['workflow'] ?? '');
        $workflowsResult = $service->listWorkflows();
        $runsResult = $service->listRuns($workflowFilter, 25);
        $runnersResult = $service->listRunners();

        $workflows = [];
        if ($workflowsResult['success'] && is_array($workflowsResult['data'])) {
            $workflows = $workflowsResult['data']['workflows'] ?? [];
            if (!is_array($workflows)) {
                $workflows = [];
            }
        }

        $runs = [];
        if ($runsResult['success'] && is_array($runsResult['data'])) {
            $runs = $runsResult['data']['workflow_runs'] ?? [];
            if (!is_array($runs)) {
                $runs = [];
            }
        }

        $runners = [];
        $runnerError = '';
        if ($runnersResult['success'] && is_array($runnersResult['data'])) {
            $runners = $runnersResult['data']['runners'] ?? [];
            if (!is_array($runners)) {
                $runners = [];
            }
        } else {
            $runnerError = (string)($runnersResult['error'] ?? '');
        }

        $runningCount = 0;
        $failed24h = 0;
        $cutoff = time() - (24 * 3600);

        foreach ($runs as $run) {
            if (!is_array($run)) {
                continue;
            }
            $status = strtolower((string)($run['status'] ?? ''));
            $conclusion = strtolower((string)($run['conclusion'] ?? ''));
            if (in_array($status, ['queued', 'in_progress', 'waiting'], true)) {
                $runningCount++;
            }

            $updatedAt = strtotime((string)($run['updated_at'] ?? ''));
            if ($updatedAt >= $cutoff && $conclusion === 'failure') {
                $failed24h++;
            }
        }

        $onlineSelfHosted = 0;
        foreach ($runners as $runner) {
            if (!is_array($runner)) {
                continue;
            }
            $runnerType = strtolower((string)($runner['runner_type'] ?? ''));
            $status = strtolower((string)($runner['status'] ?? ''));
            if ($runnerType === 'self-hosted' && $status === 'online') {
                $onlineSelfHosted++;
            }
        }

        $failedRuns = [];
        foreach ($runs as $run) {
            if (!is_array($run)) {
                continue;
            }
            $conclusion = strtolower((string)($run['conclusion'] ?? ''));
            if ($conclusion === 'failure' || $conclusion === 'cancelled' || $conclusion === 'timed_out') {
                $failedRuns[] = $run;
            }
        }

        gh_json([
            'ok' => true,
            'configured' => true,
            'settings' => $settingsMasked,
            'workflows' => $workflows,
            'runs' => $runs,
            'runners' => $runners,
            'runner_error' => $runnerError,
            'failed_runs' => array_slice($failedRuns, 0, 10),
            'summary' => [
                'workflow_count' => count($workflows),
                'running_count' => $runningCount,
                'failed_count_24h' => $failed24h,
                'online_self_hosted' => $onlineSelfHosted,
                'repo' => ($settingsRaw['repo_owner'] ?? '') . '/' . ($settingsRaw['repo_name'] ?? ''),
            ],
        ]);
    }

    gh_json(['ok' => false, 'error' => 'Unsupported action or method'], 405);
} catch (Throwable $e) {
    gh_json([
        'ok' => false,
        'error' => $e->getMessage(),
    ], 500);
}

