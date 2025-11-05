// API base URL
const API_BASE = window.location.origin;

// State
let currentJobId = null;
let pollingInterval = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadClusterInfo();
    loadJobs();
    setupEventListeners();
});

// Event listeners
function setupEventListeners() {
    document.getElementById('refresh-cluster-btn').addEventListener('click', loadClusterInfo);
    document.getElementById('start-analysis-btn').addEventListener('click', startAnalysis);
    document.getElementById('refresh-jobs-btn').addEventListener('click', loadJobs);

    // Modal close
    document.querySelector('.close').addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('job-modal');
        if (e.target === modal) {
            closeModal();
        }
    });
}

// API calls
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Health check
async function checkHealth() {
    try {
        const data = await apiCall('/health');

        const proxmoxStatus = document.getElementById('proxmox-status');
        const claudeStatus = document.getElementById('claude-status');

        if (data.proxmox_connected) {
            proxmoxStatus.textContent = 'Connected';
            proxmoxStatus.className = 'status-indicator connected';
        } else {
            proxmoxStatus.textContent = 'Disconnected';
            proxmoxStatus.className = 'status-indicator error';
        }

        if (data.claude_initialized) {
            claudeStatus.textContent = 'Ready';
            claudeStatus.className = 'status-indicator connected';
        } else {
            claudeStatus.textContent = 'Not Ready';
            claudeStatus.className = 'status-indicator error';
        }
    } catch (error) {
        console.error('Health check failed:', error);
        document.getElementById('proxmox-status').textContent = 'Error';
        document.getElementById('proxmox-status').className = 'status-indicator error';
        document.getElementById('claude-status').textContent = 'Error';
        document.getElementById('claude-status').className = 'status-indicator error';
    }
}

// Load cluster information
async function loadClusterInfo() {
    try {
        const data = await apiCall('/cluster/resources');

        document.getElementById('total-resources').textContent = data.total;
        document.getElementById('total-vms').textContent = data.vms;
        document.getElementById('total-lxcs').textContent = data.lxcs;

        // Get nodes count from cluster info
        const clusterInfo = await apiCall('/cluster/info');
        document.getElementById('total-nodes').textContent = clusterInfo.nodes?.length || 0;
    } catch (error) {
        console.error('Failed to load cluster info:', error);
        showNotification('Failed to load cluster information', 'error');
    }
}

// Start analysis
async function startAnalysis() {
    const btn = document.getElementById('start-analysis-btn');
    btn.disabled = true;
    btn.textContent = 'Starting...';

    try {
        const data = await apiCall('/batch/start', { method: 'POST' });

        currentJobId = data.job_id;
        showNotification(`Batch job ${data.job_id} started!`, 'success');

        // Show active job section
        document.getElementById('active-job-section').style.display = 'block';
        document.getElementById('current-job-id').textContent = data.job_id;

        // Start polling for job status
        startPolling(data.job_id);

        // Reload jobs list
        loadJobs();
    } catch (error) {
        console.error('Failed to start analysis:', error);
        showNotification('Failed to start analysis', 'error');
        btn.disabled = false;
        btn.textContent = 'Start Batch Analysis';
    }
}

// Poll job status
function startPolling(jobId) {
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }

    pollingInterval = setInterval(async () => {
        try {
            const data = await apiCall(`/batch/jobs/${jobId}/status`);
            updateProgress(data);

            if (data.status === 'completed' || data.status === 'failed') {
                clearInterval(pollingInterval);
                pollingInterval = null;

                // Re-enable start button
                const btn = document.getElementById('start-analysis-btn');
                btn.disabled = false;
                btn.textContent = 'Start Batch Analysis';

                // Reload jobs
                loadJobs();

                if (data.status === 'completed') {
                    showNotification('Analysis completed successfully!', 'success');
                } else {
                    showNotification('Analysis failed', 'error');
                }
            }
        } catch (error) {
            console.error('Failed to poll job status:', error);
        }
    }, 2000); // Poll every 2 seconds
}

// Update progress bar
function updateProgress(data) {
    const percentage = data.progress.percentage;
    document.getElementById('progress-fill').style.width = `${percentage}%`;
    document.getElementById('progress-text').textContent = `${percentage}%`;
    document.getElementById('progress-details').textContent =
        `Processed: ${data.progress.processed} / ${data.progress.total}`;
}

// Load jobs list
async function loadJobs() {
    try {
        const data = await apiCall('/batch/jobs');
        const jobsList = document.getElementById('jobs-list');

        if (!data.jobs || data.jobs.length === 0) {
            jobsList.innerHTML = '<p class="empty-state">No jobs yet. Start your first analysis!</p>';
            return;
        }

        jobsList.innerHTML = data.jobs.map(job => {
            const date = new Date(job.started_at).toLocaleString();
            const percentage = job.total_vms > 0
                ? Math.round((job.processed_vms / job.total_vms) * 100)
                : 0;

            return `
                <div class="job-item" onclick="viewJob(${job.id})">
                    <div class="job-info">
                        <div class="job-id">Job #${job.id}</div>
                        <div class="job-meta">
                            Started: ${date} | Progress: ${job.processed_vms}/${job.total_vms} (${percentage}%)
                        </div>
                    </div>
                    <div class="job-status ${job.status}">${job.status.toUpperCase()}</div>
                    <div class="job-actions">
                        ${job.status === 'completed' ? `
                            <button class="btn btn-success" onclick="event.stopPropagation(); downloadJob(${job.id})">
                                Download
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load jobs:', error);
        showNotification('Failed to load jobs', 'error');
    }
}

// View job details
async function viewJob(jobId) {
    try {
        const data = await apiCall(`/batch/jobs/${jobId}`);
        const modal = document.getElementById('job-modal');
        const content = document.getElementById('job-details-content');

        const job = data.job;
        const analyses = data.analyses || [];
        const reports = data.reports || [];

        let html = `
            <div class="job-details">
                <h3>Job #${job.id}</h3>
                <p><strong>Status:</strong> <span class="job-status ${job.status}">${job.status.toUpperCase()}</span></p>
                <p><strong>Started:</strong> ${new Date(job.started_at).toLocaleString()}</p>
                ${job.completed_at ? `<p><strong>Completed:</strong> ${new Date(job.completed_at).toLocaleString()}</p>` : ''}
                <p><strong>Progress:</strong> ${job.processed_vms} / ${job.total_vms}</p>
                ${job.error_message ? `<p class="warning">Error: ${job.error_message}</p>` : ''}

                <h3>Analyzed Resources (${analyses.length})</h3>
        `;

        if (analyses.length > 0) {
            html += '<div class="analyses-list">';
            analyses.forEach(analysis => {
                html += `
                    <div class="analysis-item">
                        <h4>${analysis.vm_name} (${analysis.vm_type.toUpperCase()}-${analysis.vm_id})</h4>
                        <p><strong>Node:</strong> ${analysis.node}</p>
                        ${analysis.analysis ? '<p>✓ Analysis completed</p>' : ''}
                        ${analysis.security_review ? '<p>✓ Security review completed</p>' : ''}
                        ${analysis.optimization_recommendations ? '<p>✓ Optimization recommendations generated</p>' : ''}
                        ${analysis.terraform_template ? '<p>✓ Terraform template generated</p>' : ''}
                        ${analysis.ansible_playbook ? '<p>✓ Ansible playbook generated</p>' : ''}
                    </div>
                `;
            });
            html += '</div>';
        } else {
            html += '<p class="empty-state">No analyses yet</p>';
        }

        if (reports.length > 0) {
            html += '<h3>Infrastructure Reports</h3>';
            reports.forEach(report => {
                html += `
                    <div class="analysis-item">
                        <h4>${report.report_type}</h4>
                        <p><small>${new Date(report.created_at).toLocaleString()}</small></p>
                    </div>
                `;
            });
        }

        if (job.status === 'completed') {
            html += `
                <button class="btn btn-primary" onclick="downloadJob(${jobId})">
                    Download All Outputs
                </button>
            `;
        }

        html += '</div>';

        content.innerHTML = html;
        modal.style.display = 'block';
    } catch (error) {
        console.error('Failed to load job details:', error);
        showNotification('Failed to load job details', 'error');
    }
}

// Download job outputs
function downloadJob(jobId) {
    window.location.href = `${API_BASE}/batch/jobs/${jobId}/download`;
    showNotification('Download started', 'success');
}

// Close modal
function closeModal() {
    document.getElementById('job-modal').style.display = 'none';
}

// Show notification
function showNotification(message, type = 'info') {
    // Simple console notification for now
    // You could implement a toast notification system here
    console.log(`[${type.toUpperCase()}] ${message}`);

    // Optional: Add a simple alert for important messages
    if (type === 'error') {
        alert(message);
    }
}

// Auto-refresh on focus
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        checkHealth();
        loadJobs();
    }
});
