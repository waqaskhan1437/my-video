<?php
/**
 * GitHub Actions API helper for Video Workflow Manager.
 */

class GitHubActionsAPI
{
    private $pdo;
    private $apiBase = 'https://api.github.com';

    private $settingDefaults = [
        'enabled' => '0',
        'repo_owner' => '',
        'repo_name' => '',
        'repo_branch' => 'main',
        'api_token' => '',
        'runner_preference' => 'github-hosted',
        'self_hosted_label' => 'self-hosted',
        'workflow_archive' => 'pipeline.yml',
        'workflow_social' => 'social-publish.yml',
        'workflow_postforme' => 'archive-postforme.yml',
        'workflow_whisper' => 'whisper-cpu.yml',
    ];

    public function __construct($pdo)
    {
        $this->pdo = $pdo;
    }

    private function settingKeyMap()
    {
        return [
            'enabled' => 'github_actions_enabled',
            'repo_owner' => 'github_repo_owner',
            'repo_name' => 'github_repo_name',
            'repo_branch' => 'github_repo_branch',
            'api_token' => 'github_api_token',
            'runner_preference' => 'github_runner_preference',
            'self_hosted_label' => 'github_self_hosted_label',
            'workflow_archive' => 'github_workflow_archive',
            'workflow_social' => 'github_workflow_social',
            'workflow_postforme' => 'github_workflow_postforme',
            'workflow_whisper' => 'github_workflow_whisper',
        ];
    }

    private function upsertSetting($settingKey, $settingValue)
    {
        $stmt = $this->pdo->prepare(
            "INSERT INTO settings (setting_key, setting_value) VALUES (?, ?)
             ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)"
        );
        $stmt->execute([$settingKey, (string)$settingValue]);
    }

    public function getSettings($maskToken = true)
    {
        $keyMap = $this->settingKeyMap();
        $settings = $this->settingDefaults;

        $dbKeys = array_values($keyMap);
        $placeholders = implode(',', array_fill(0, count($dbKeys), '?'));
        $stmt = $this->pdo->prepare("SELECT setting_key, setting_value FROM settings WHERE setting_key IN ($placeholders)");
        $stmt->execute($dbKeys);
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

        $reverseMap = array_flip($keyMap);
        foreach ($rows as $row) {
            $dbKey = (string)$row['setting_key'];
            if (!isset($reverseMap[$dbKey])) {
                continue;
            }
            $settings[$reverseMap[$dbKey]] = (string)$row['setting_value'];
        }

        if ($maskToken) {
            $settings['api_token_masked'] = $this->maskToken($settings['api_token']);
            unset($settings['api_token']);
        }

        $settings['enabled'] = ($settings['enabled'] === '1' || strtolower((string)$settings['enabled']) === 'true') ? '1' : '0';
        return $settings;
    }

    public function saveSettings($input)
    {
        $keyMap = $this->settingKeyMap();

        foreach ($keyMap as $field => $dbKey) {
            if (!array_key_exists($field, $input)) {
                continue;
            }

            $value = (string)$input[$field];
            if ($field === 'enabled') {
                $value = ($value === '1' || strtolower($value) === 'true' || strtolower($value) === 'on') ? '1' : '0';
            }

            $this->upsertSetting($dbKey, trim($value));
        }
    }

    private function maskToken($token)
    {
        $token = trim((string)$token);
        if ($token === '') {
            return '';
        }
        if (strlen($token) <= 10) {
            return str_repeat('*', strlen($token));
        }
        return substr($token, 0, 4) . str_repeat('*', max(4, strlen($token) - 8)) . substr($token, -4);
    }

    public function isConfigured()
    {
        $settings = $this->getSettings(false);
        return !empty($settings['repo_owner']) && !empty($settings['repo_name']) && !empty($settings['api_token']);
    }

    private function request($method, $path, $query = [], $body = null)
    {
        $settings = $this->getSettings(false);
        $token = trim((string)($settings['api_token'] ?? ''));

        if ($token === '') {
            return [
                'success' => false,
                'status' => 0,
                'error' => 'GitHub token is missing',
                'data' => null,
            ];
        }

        $url = $this->apiBase . $path;
        if (!empty($query)) {
            $url .= '?' . http_build_query($query);
        }

        $headers = [
            'Accept: application/vnd.github+json',
            'Authorization: Bearer ' . $token,
            'X-GitHub-Api-Version: 2022-11-28',
            'User-Agent: VideoWorkflowManager',
            'Content-Type: application/json',
        ];

        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 60,
            CURLOPT_HTTPHEADER => $headers,
        ]);

        $upper = strtoupper((string)$method);
        if ($upper === 'POST') {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $body ? json_encode($body) : '{}');
        } elseif ($upper !== 'GET') {
            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $upper);
            if ($body !== null) {
                curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body));
            }
        }

        $response = curl_exec($ch);
        $error = curl_error($ch);
        $status = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($error) {
            return [
                'success' => false,
                'status' => 0,
                'error' => 'cURL error: ' . $error,
                'data' => null,
            ];
        }

        $decoded = null;
        if (is_string($response) && $response !== '') {
            $decoded = json_decode($response, true);
            if ($decoded === null && json_last_error() !== JSON_ERROR_NONE) {
                $decoded = ['raw' => $response];
            }
        }

        $ok = ($status >= 200 && $status < 300);
        $message = '';
        if (!$ok) {
            if (is_array($decoded) && isset($decoded['message'])) {
                $message = (string)$decoded['message'];
            } else {
                $message = 'GitHub API request failed';
            }
        }

        return [
            'success' => $ok,
            'status' => $status,
            'error' => $message,
            'data' => $decoded,
        ];
    }

    private function repoPath()
    {
        $settings = $this->getSettings(false);
        $owner = rawurlencode((string)$settings['repo_owner']);
        $repo = rawurlencode((string)$settings['repo_name']);
        return "/repos/{$owner}/{$repo}";
    }

    public function listWorkflows()
    {
        return $this->request('GET', $this->repoPath() . '/actions/workflows', ['per_page' => 100]);
    }

    public function listRuns($workflow = '', $perPage = 30)
    {
        $path = $this->repoPath() . '/actions/runs';
        if (trim((string)$workflow) !== '') {
            $path = $this->repoPath() . '/actions/workflows/' . rawurlencode((string)$workflow) . '/runs';
        }
        return $this->request('GET', $path, ['per_page' => max(1, (int)$perPage)]);
    }

    public function listRunners()
    {
        return $this->request('GET', $this->repoPath() . '/actions/runners', ['per_page' => 100]);
    }

    public function dispatchWorkflow($workflowFileOrId, $ref, $inputs = [])
    {
        $workflowFileOrId = trim((string)$workflowFileOrId);
        if ($workflowFileOrId === '') {
            return [
                'success' => false,
                'status' => 0,
                'error' => 'Workflow identifier is required',
                'data' => null,
            ];
        }

        $payload = [
            'ref' => trim((string)$ref) ?: 'main',
            'inputs' => is_array($inputs) ? $inputs : [],
        ];

        return $this->request(
            'POST',
            $this->repoPath() . '/actions/workflows/' . rawurlencode($workflowFileOrId) . '/dispatches',
            [],
            $payload
        );
    }
}

