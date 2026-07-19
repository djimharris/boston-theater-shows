/**
 * Status bar component — shows last update time and per-site scraping status.
 */

/**
 * Render the status bar with data from status.json.
 */
function renderStatus(statusData) {
    const summary = document.getElementById('status-summary');
    const expandBtn = document.getElementById('status-expand');
    const details = document.getElementById('status-details');
    const tableBody = document.getElementById('status-table-body');

    if (!statusData) {
        summary.textContent = 'Status unavailable';
        return;
    }

    // Format last run time
    const lastRun = new Date(statusData.last_run);
    const timeAgo = getTimeAgo(lastRun);
    const successCount = statusData.successful || 0;
    const totalCount = statusData.total_sites || 0;

    summary.innerHTML = `
        Last updated: ${lastRun.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
        (${timeAgo})
        &middot;
        <span style="color: ${successCount === totalCount ? 'var(--color-success)' : 'var(--color-error)'}">
            ${successCount}/${totalCount} sites OK
        </span>
    `;

    // Populate details table
    if (statusData.sites) {
        tableBody.innerHTML = statusData.sites.map(site => `
            <tr>
                <td>
                    <a href="${escapeAttr(site.url)}" target="_blank" rel="noopener" style="color: inherit; text-decoration: none;">
                        ${escapeHtml(site.theater_name)}
                    </a>
                </td>
                <td>
                    <span class="status-dot ${site.success ? 'status-dot-success' : 'status-dot-error'}"></span>
                    ${site.success ? 'OK' : escapeHtml(site.error_message || 'Failed')}
                </td>
                <td>${site.shows_found}</td>
                <td>${site.duration_seconds.toFixed(1)}s</td>
            </tr>
        `).join('');
    }

    // Toggle details panel
    expandBtn.addEventListener('click', () => {
        const isExpanded = details.hidden;
        details.hidden = !isExpanded;
        expandBtn.setAttribute('aria-expanded', isExpanded);
        expandBtn.textContent = isExpanded ? 'Hide' : 'Details';
    });
}

/**
 * Get human-readable time ago string.
 */
function getTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'yesterday';
    return `${diffDays} days ago`;
}
