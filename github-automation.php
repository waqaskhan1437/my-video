<?php
require_once 'config.php';
require_once 'includes/GitHubActionsAPI.php';

$githubApi = new GitHubActionsAPI($pdo);
$settings = $githubApi->getSettings(true);

include 'includes/header.php';
?>

<div class="flex items-center justify-between mb-6">
    <div>
        <h2 class="text-xl font-semibold">GitHub Automation Manager</h2>
        <p class="text-sm text-gray-400 mt-1">Run workflows, monitor errors, and manage runner strategy from one page.</p>
    </div>
    <button id="refreshStatusBtn" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm">Refresh Status</button>
</div>

<div id="githubNotice" class="hidden mb-6 p-4 rounded-lg border border-yellow-500/30 bg-yellow-500/10 text-yellow-300 text-sm"></div>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
    <div class="card rounded-lg p-4">
        <div class="text-xs text-gray-400 uppercase tracking-wide">Workflows</div>
        <div id="statWorkflowCount" class="text-3xl font-bold mt-2">-</div>
    </div>
    <div class="card rounded-lg p-4">
        <div class="text-xs text-gray-400 uppercase tracking-wide">Running / Queued</div>
        <div id="statRunningCount" class="text-3xl font-bold mt-2 text-blue-400">-</div>
    </div>
    <div class="card rounded-lg p-4">
        <div class="text-xs text-gray-400 uppercase tracking-wide">Self-hosted Online</div>
        <div id="statRunnerCount" class="text-3xl font-bold mt-2 text-green-400">-</div>
        <div id="statFailed24h" class="text-xs text-red-400 mt-2">Failed (24h): -</div>
    </div>
</div>

<div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
    <div class="card rounded-lg">
        <div class="p-4 border-b border-gray-800">
            <h3 class="font-semibold">GitHub Connection</h3>
        </div>
        <div class="p-4 space-y-4">
            <form id="githubSettingsForm" class="space-y-4">
                <div class="flex items-center gap-2 p-3 rounded bg-gray-800/60">
                    <input id="enabled" name="enabled" type="checkbox" class="w-4 h-4" <?= ($settings['enabled'] ?? '0') === '1' ? 'checked' : '' ?>>
                    <label for="enabled" class="text-sm">Enable GitHub-based automation control</label>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Repo Owner</label>
                        <input name="repo_owner" id="repo_owner" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg" placeholder="waqaskhan1437" value="<?= htmlspecialchars($settings['repo_owner'] ?? '') ?>">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Repo Name</label>
                        <input name="repo_name" id="repo_name" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg" placeholder="my-video" value="<?= htmlspecialchars($settings['repo_name'] ?? '') ?>">
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Branch</label>
                        <input name="repo_branch" id="repo_branch" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg" placeholder="main" value="<?= htmlspecialchars($settings['repo_branch'] ?? 'main') ?>">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">GitHub Token (classic/fine-grained)</label>
                        <input name="api_token" id="api_token" type="password" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg" placeholder="<?= htmlspecialchars(($settings['api_token_masked'] ?? '') !== '' ? 'Saved: ' . $settings['api_token_masked'] : 'ghp_xxx...') ?>">
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Runner Preference</label>
                        <select name="runner_preference" id="runner_preference" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg">
                            <option value="github-hosted">GitHub Hosted</option>
                            <option value="self-hosted">Self Hosted</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Self-hosted Label</label>
                        <input name="self_hosted_label" id="self_hosted_label" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg" placeholder="self-hosted" value="<?= htmlspecialchars($settings['self_hosted_label'] ?? 'self-hosted') ?>">
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Archive Workflow</label>
                        <input name="workflow_archive" id="workflow_archive" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg" value="<?= htmlspecialchars($settings['workflow_archive'] ?? 'pipeline.yml') ?>">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Social Workflow</label>
                        <input name="workflow_social" id="workflow_social" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg" value="<?= htmlspecialchars($settings['workflow_social'] ?? 'social-publish.yml') ?>">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">PostForMe Workflow</label>
                        <input name="workflow_postforme" id="workflow_postforme" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg" value="<?= htmlspecialchars($settings['workflow_postforme'] ?? 'archive-postforme.yml') ?>">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Whisper Workflow</label>
                        <input name="workflow_whisper" id="workflow_whisper" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg" value="<?= htmlspecialchars($settings['workflow_whisper'] ?? 'whisper-cpu.yml') ?>">
                    </div>
                </div>

                <div class="flex items-center justify-between gap-3">
                    <label class="inline-flex items-center gap-2 text-xs text-gray-400">
                        <input type="checkbox" id="clear_token" name="clear_token" value="1">
                        Clear saved token
                    </label>
                    <button type="submit" class="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm">Save Settings</button>
                </div>
            </form>
        </div>
    </div>

    <div class="card rounded-lg">
        <div class="p-4 border-b border-gray-800">
            <h3 class="font-semibold">Quick Dispatch</h3>
        </div>
        <div class="p-4 space-y-4">
            <div class="p-3 rounded bg-gray-800/60 border border-gray-700">
                <div class="flex items-center justify-between mb-2">
                    <div class="font-medium text-sm">Google Photos to Archive</div>
                    <button class="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs" data-dispatch-type="archive">Run</button>
                </div>
                <textarea id="inputs_archive" class="w-full h-16 px-3 py-2 bg-black/30 border border-gray-700 rounded text-xs font-mono" placeholder='{"mode":"process_session","session_id":""}'>{}</textarea>
            </div>

            <div class="p-3 rounded bg-gray-800/60 border border-gray-700">
                <div class="flex items-center justify-between mb-2">
                    <div class="font-medium text-sm">Archive to YouTube</div>
                    <button class="px-3 py-1 bg-pink-600 hover:bg-pink-700 rounded text-xs" data-dispatch-type="social">Run</button>
                </div>
                <textarea id="inputs_social" class="w-full h-16 px-3 py-2 bg-black/30 border border-gray-700 rounded text-xs font-mono" placeholder='{"max_items":"1","privacy_status":"public"}'>{}</textarea>
            </div>

            <div class="p-3 rounded bg-gray-800/60 border border-gray-700">
                <div class="flex items-center justify-between mb-2">
                    <div class="font-medium text-sm">Archive to PostForMe</div>
                    <button class="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 rounded text-xs" data-dispatch-type="postforme">Run</button>
                </div>
                <textarea id="inputs_postforme" class="w-full h-16 px-3 py-2 bg-black/30 border border-gray-700 rounded text-xs font-mono" placeholder='{"run_mode":"run","automation_id":"daily_archive_accounts_a"}'>{}</textarea>
            </div>

            <div class="p-3 rounded bg-gray-800/60 border border-gray-700">
                <div class="flex items-center justify-between mb-2">
                    <div class="font-medium text-sm">Whisper CPU Job (Self-hosted)</div>
                    <button class="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 rounded text-xs text-black font-semibold" data-dispatch-type="whisper">Run</button>
                </div>
                <textarea id="inputs_whisper" class="w-full h-16 px-3 py-2 bg-black/30 border border-gray-700 rounded text-xs font-mono" placeholder='{"whisper_model":"base","language":"auto","runner_preference":"self-hosted"}'>{}</textarea>
            </div>

            <div class="p-3 rounded bg-gray-800/60 border border-gray-700">
                <label class="block text-xs text-gray-400 mb-1">Custom Workflow</label>
                <div class="flex gap-2">
                    <select id="customWorkflowSelect" class="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm">
                        <option value="">Select workflow...</option>
                    </select>
                    <button id="runCustomBtn" class="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded text-xs">Run</button>
                </div>
                <textarea id="inputs_custom" class="w-full h-16 px-3 py-2 mt-2 bg-black/30 border border-gray-700 rounded text-xs font-mono" placeholder='{"key":"value"}'>{}</textarea>
            </div>
        </div>
    </div>
</div>

<div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
    <div class="xl:col-span-2 card rounded-lg">
        <div class="p-4 border-b border-gray-800 flex items-center justify-between">
            <h3 class="font-semibold">Recent Workflow Runs</h3>
            <a id="openActionsLink" href="#" target="_blank" class="text-xs text-indigo-400 hover:underline">Open GitHub Actions</a>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
                <thead class="bg-gray-800/50 text-gray-400">
                    <tr>
                        <th class="text-left px-4 py-3">Workflow</th>
                        <th class="text-left px-4 py-3">Status</th>
                        <th class="text-left px-4 py-3">Event</th>
                        <th class="text-left px-4 py-3">Branch</th>
                        <th class="text-left px-4 py-3">Updated</th>
                        <th class="text-left px-4 py-3">Link</th>
                    </tr>
                </thead>
                <tbody id="runsTableBody">
                    <tr><td colspan="6" class="px-4 py-6 text-gray-500 text-center">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <div class="space-y-6">
        <div class="card rounded-lg">
            <div class="p-4 border-b border-gray-800">
                <h3 class="font-semibold">Failed / Cancelled</h3>
            </div>
            <div id="failedRunsBox" class="p-4 text-sm text-gray-400 space-y-3">
                <div>Loading...</div>
            </div>
        </div>

        <div class="card rounded-lg">
            <div class="p-4 border-b border-gray-800">
                <h3 class="font-semibold">Runner Health</h3>
            </div>
            <div id="runnerBox" class="p-4 text-sm text-gray-400 space-y-2">
                <div>Loading...</div>
            </div>
        </div>

        <div class="card rounded-lg">
            <div class="p-4 border-b border-gray-800">
                <h3 class="font-semibold">Self-hosted Whisper Note</h3>
            </div>
            <div class="p-4 text-xs text-gray-400 space-y-2">
                <div>Use a dedicated label for CPU transcription runner, for example: <code class="bg-gray-800 px-1 rounded">whisper-cpu</code>.</div>
                <div>Dispatch payload can include:</div>
                <pre class="bg-black/40 p-2 rounded overflow-x-auto">{
  "runner_preference": "self-hosted",
  "self_hosted_label": "whisper-cpu",
  "whisper_model": "base",
  "language": "auto"
}</pre>
            </div>
        </div>
    </div>
</div>

<script>
const githubApiUrl = 'api/github-actions.php';

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function statusBadge(status, conclusion) {
    const normalizedStatus = String(status || '').toLowerCase();
    const normalizedConclusion = String(conclusion || '').toLowerCase();
    if (['queued', 'in_progress', 'waiting'].includes(normalizedStatus)) {
        return '<span class="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-300">' + escapeHtml(normalizedStatus) + '</span>';
    }
    if (normalizedConclusion === 'success') {
        return '<span class="px-2 py-1 rounded text-xs bg-green-500/20 text-green-300">success</span>';
    }
    if (normalizedConclusion === 'failure' || normalizedConclusion === 'timed_out') {
        return '<span class="px-2 py-1 rounded text-xs bg-red-500/20 text-red-300">' + escapeHtml(normalizedConclusion || 'failed') + '</span>';
    }
    if (normalizedConclusion === 'cancelled') {
        return '<span class="px-2 py-1 rounded text-xs bg-yellow-500/20 text-yellow-300">cancelled</span>';
    }
    return '<span class="px-2 py-1 rounded text-xs bg-gray-600/40 text-gray-300">' + escapeHtml(normalizedStatus || normalizedConclusion || 'unknown') + '</span>';
}

function parseJsonOrThrow(rawText) {
    const text = String(rawText || '').trim();
    if (!text) return {};
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return parsed;
    }
    throw new Error('JSON must be an object');
}

async function loadGithubStatus() {
    const notice = document.getElementById('githubNotice');
    notice.classList.add('hidden');

    const response = await fetch(githubApiUrl + '?action=status', { cache: 'no-store' });
    const data = await response.json();
    if (!data || !data.ok) {
        throw new Error((data && data.error) ? data.error : 'Unable to load GitHub status');
    }

    document.getElementById('statWorkflowCount').textContent = String((data.summary && data.summary.workflow_count) || 0);
    document.getElementById('statRunningCount').textContent = String((data.summary && data.summary.running_count) || 0);
    document.getElementById('statRunnerCount').textContent = String((data.summary && data.summary.online_self_hosted) || 0);
    document.getElementById('statFailed24h').textContent = 'Failed (24h): ' + String((data.summary && data.summary.failed_count_24h) || 0);

    const repoText = (data.summary && data.summary.repo) ? data.summary.repo : '';
    const actionsLink = document.getElementById('openActionsLink');
    actionsLink.href = repoText ? ('https://github.com/' + repoText + '/actions') : '#';

    if (!data.configured) {
        notice.textContent = data.message || 'GitHub settings are not configured.';
        notice.classList.remove('hidden');
    }

    const workflowSelect = document.getElementById('customWorkflowSelect');
    const workflows = Array.isArray(data.workflows) ? data.workflows : [];
    workflowSelect.innerHTML = '<option value="">Select workflow...</option>' + workflows.map(function (wf) {
        return '<option value="' + escapeHtml(wf.path || wf.id || '') + '">' + escapeHtml(wf.name || wf.path || '') + '</option>';
    }).join('');

    const runs = Array.isArray(data.runs) ? data.runs : [];
    const runsBody = document.getElementById('runsTableBody');
    if (!runs.length) {
        runsBody.innerHTML = '<tr><td colspan="6" class="px-4 py-6 text-gray-500 text-center">No runs found.</td></tr>';
    } else {
        runsBody.innerHTML = runs.map(function (run) {
            return '<tr class="border-t border-gray-800">' +
                '<td class="px-4 py-3">' + escapeHtml(run.name || '-') + '</td>' +
                '<td class="px-4 py-3">' + statusBadge(run.status, run.conclusion) + '</td>' +
                '<td class="px-4 py-3">' + escapeHtml(run.event || '-') + '</td>' +
                '<td class="px-4 py-3">' + escapeHtml(run.head_branch || '-') + '</td>' +
                '<td class="px-4 py-3">' + escapeHtml(run.updated_at || '-') + '</td>' +
                '<td class="px-4 py-3"><a href="' + escapeHtml(run.html_url || '#') + '" target="_blank" class="text-indigo-400 hover:underline">View</a></td>' +
                '</tr>';
        }).join('');
    }

    const failedRuns = Array.isArray(data.failed_runs) ? data.failed_runs : [];
    const failedBox = document.getElementById('failedRunsBox');
    if (!failedRuns.length) {
        failedBox.innerHTML = '<div class="text-gray-500">No failed/cancelled runs in latest history.</div>';
    } else {
        failedBox.innerHTML = failedRuns.slice(0, 8).map(function (run) {
            const status = (run.conclusion || run.status || 'unknown');
            return '<div class="p-2 rounded bg-gray-800/60 border border-gray-700">' +
                '<div class="font-medium text-gray-200">' + escapeHtml(run.name || '-') + '</div>' +
                '<div class="text-xs text-gray-400 mt-1">Status: ' + escapeHtml(String(status)) + '</div>' +
                '<div class="text-xs text-gray-500 mt-1">' + escapeHtml(run.updated_at || '') + '</div>' +
                '<a target="_blank" class="text-xs text-indigo-400 hover:underline" href="' + escapeHtml(run.html_url || '#') + '">Open run</a>' +
                '</div>';
        }).join('');
    }

    const runners = Array.isArray(data.runners) ? data.runners : [];
    const runnerBox = document.getElementById('runnerBox');
    if (!runners.length) {
        const runnerError = data.runner_error ? ('<div class="text-red-400 text-xs">' + escapeHtml(data.runner_error) + '</div>') : '';
        runnerBox.innerHTML = '<div class="text-gray-500">No runner data available.</div>' + runnerError;
    } else {
        runnerBox.innerHTML = runners.map(function (runner) {
            const statusColor = String(runner.status || '').toLowerCase() === 'online' ? 'text-green-400' : 'text-red-400';
            const labels = Array.isArray(runner.labels) ? runner.labels.map(function (l) { return l.name; }).join(', ') : '';
            return '<div class="p-2 rounded bg-gray-800/60 border border-gray-700">' +
                '<div class="font-medium text-gray-200">' + escapeHtml(runner.name || '-') + '</div>' +
                '<div class="text-xs ' + statusColor + ' mt-1">' + escapeHtml(runner.status || 'unknown') + ' / ' + escapeHtml(runner.runner_type || 'unknown') + '</div>' +
                '<div class="text-xs text-gray-500 mt-1">Labels: ' + escapeHtml(labels || '-') + '</div>' +
                '</div>';
        }).join('');
    }
}

async function saveGithubSettings(event) {
    event.preventDefault();
    const form = document.getElementById('githubSettingsForm');
    const data = new FormData(form);
    data.append('action', 'save_settings');

    const response = await fetch(githubApiUrl, { method: 'POST', body: data });
    const payload = await response.json();
    if (!payload || !payload.ok) {
        throw new Error((payload && payload.error) ? payload.error : 'Failed to save settings');
    }
    showToast(payload.message || 'Saved', 'success');
    await loadGithubStatus();
}

async function dispatchByType(type) {
    const inputsBox = document.getElementById('inputs_' + type);
    const inputsJson = parseJsonOrThrow(inputsBox ? inputsBox.value : '{}');
    const ref = document.getElementById('repo_branch').value || 'main';

    const body = new FormData();
    body.append('action', 'dispatch');
    body.append('workflow_type', type);
    body.append('ref', ref);
    body.append('inputs_json', JSON.stringify(inputsJson));

    const response = await fetch(githubApiUrl, { method: 'POST', body: body });
    const payload = await response.json();
    if (!payload || !payload.ok) {
        throw new Error((payload && payload.error) ? payload.error : 'Dispatch failed');
    }

    showToast(payload.message || 'Dispatch requested', 'success');
    if (payload.actions_url) {
        document.getElementById('openActionsLink').href = payload.actions_url;
    }
    await loadGithubStatus();
}

async function dispatchCustomWorkflow(event) {
    event.preventDefault();
    const workflow = document.getElementById('customWorkflowSelect').value;
    if (!workflow) {
        throw new Error('Select a custom workflow first');
    }
    const ref = document.getElementById('repo_branch').value || 'main';
    const inputsJson = parseJsonOrThrow(document.getElementById('inputs_custom').value);

    const body = new FormData();
    body.append('action', 'dispatch');
    body.append('workflow', workflow);
    body.append('ref', ref);
    body.append('inputs_json', JSON.stringify(inputsJson));

    const response = await fetch(githubApiUrl, { method: 'POST', body: body });
    const payload = await response.json();
    if (!payload || !payload.ok) {
        throw new Error((payload && payload.error) ? payload.error : 'Custom dispatch failed');
    }
    showToast(payload.message || 'Custom dispatch requested', 'success');
    await loadGithubStatus();
}

document.getElementById('githubSettingsForm').addEventListener('submit', function (event) {
    saveGithubSettings(event).catch(function (error) {
        showToast(error.message || 'Save failed', 'error');
    });
});

document.getElementById('refreshStatusBtn').addEventListener('click', function () {
    loadGithubStatus().then(function () {
        showToast('GitHub status refreshed', 'success');
    }).catch(function (error) {
        showToast(error.message || 'Refresh failed', 'error');
    });
});

document.querySelectorAll('[data-dispatch-type]').forEach(function (button) {
    button.addEventListener('click', function (event) {
        event.preventDefault();
        const type = button.getAttribute('data-dispatch-type');
        dispatchByType(type).catch(function (error) {
            showToast(error.message || 'Dispatch failed', 'error');
        });
    });
});

document.getElementById('runCustomBtn').addEventListener('click', function (event) {
    dispatchCustomWorkflow(event).catch(function (error) {
        showToast(error.message || 'Dispatch failed', 'error');
    });
});

loadGithubStatus().catch(function (error) {
    showToast(error.message || 'Initial load failed', 'error');
});
setInterval(function () {
    loadGithubStatus().catch(function () {});
}, 30000);
</script>

<?php include 'includes/footer.php'; ?>

