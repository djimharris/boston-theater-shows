/**
 * Filter logic for date range and theater selection.
 */

/**
 * Initialize filter controls with default values and theater options.
 */
function initFilters(shows) {
    setDefaultDates();
    populateTheaterOptions(shows);
    setupTheaterDropdown();
}

/**
 * Set default date range: today through end of next month.
 */
function setDefaultDates() {
    const today = new Date();
    const nextMonth = new Date(today.getFullYear(), today.getMonth() + 2, 0);

    const startInput = document.getElementById('filter-start');
    const endInput = document.getElementById('filter-end');

    startInput.value = toDateString(today);
    endInput.value = toDateString(nextMonth);
}

/**
 * Populate the theater dropdown with checkboxes.
 */
function populateTheaterOptions(shows) {
    const theaters = [...new Set(shows.map(s => s.theater_name))].sort();
    const menu = document.getElementById('theater-dropdown-menu');

    menu.innerHTML = theaters.map(name =>
        `<label><input type="checkbox" value="${escapeHtml(name)}"> ${escapeHtml(name)}</label>`
    ).join('');
}

/**
 * Set up the theater dropdown toggle and change handling.
 */
function setupTheaterDropdown() {
    const btn = document.getElementById('theater-dropdown-btn');
    const menu = document.getElementById('theater-dropdown-menu');

    btn.addEventListener('click', () => {
        const isOpen = !menu.hidden;
        menu.hidden = isOpen;
        btn.setAttribute('aria-expanded', !isOpen);
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#theater-dropdown')) {
            menu.hidden = true;
            btn.setAttribute('aria-expanded', 'false');
        }
    });

    // Handle checkbox changes
    menu.addEventListener('change', () => {
        updateTheaterButtonLabel();
        // Trigger filter update via the app
        document.getElementById('filter-start').dispatchEvent(new Event('change'));
    });
}

/**
 * Update the dropdown button text to reflect selection.
 */
function updateTheaterButtonLabel() {
    const btn = document.getElementById('theater-dropdown-btn');
    const checked = getSelectedTheaters();

    if (checked.length === 0) {
        btn.textContent = 'All theaters';
    } else if (checked.length === 1) {
        btn.textContent = checked[0];
    } else {
        btn.textContent = `${checked.length} theaters`;
    }
}

/**
 * Get the list of selected theater names from checkboxes.
 */
function getSelectedTheaters() {
    const menu = document.getElementById('theater-dropdown-menu');
    return Array.from(menu.querySelectorAll('input:checked')).map(cb => cb.value);
}

/**
 * Filter shows based on date range overlap and theater selection.
 *
 * A show overlaps the filter range if:
 *   show.start_date <= filterEnd AND show.end_date >= filterStart
 */
function getFilteredShows(shows, filterStart, filterEnd, selectedTheaters) {
    return shows.filter(show => {
        // Date range overlap check
        if (filterStart && show.end_date < filterStart) return false;
        if (filterEnd && show.start_date > filterEnd) return false;

        // Theater filter (empty selection = show all)
        if (selectedTheaters.length > 0 && !selectedTheaters.includes(show.theater_name)) {
            return false;
        }

        return true;
    });
}

/**
 * Convert Date to YYYY-MM-DD string.
 */
function toDateString(date) {
    return date.toISOString().split('T')[0];
}

/**
 * Escape HTML to prevent XSS when inserting user-controlled text.
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
