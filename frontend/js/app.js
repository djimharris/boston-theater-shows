/**
 * Main application controller.
 * Manages state, data fetching, view switching, and coordination between modules.
 */

const App = (() => {
    // Application state
    const state = {
        shows: [],
        filteredShows: [],
        calendarShows: [],
        status: null,
        currentView: 'card', // 'card' or 'calendar'
        filters: {
            startDate: '',
            endDate: '',
            theaters: [] // empty = show all
        }
    };

    /**
     * Theater color map — consistent across card badges and calendar bars.
     */
    const THEATER_COLORS = {
        'Huntington Theatre': '#42a5f5',
        'Lyric Stage Company': '#ef5350',
        'Boston Theatre Scene': '#66bb6a',
        'Emerson Colonial Theatre': '#ab47bc',
        'Central Square Theater': '#ffa726',
        'SpeakEasy Stage Company': '#ec407a',
        'Boston Playwrights\' Theatre': '#26c6da',
        'American Repertory Theater': '#7e57c2',
        'Apollinaire Theatre Company': '#9ccc65',
        'Wheelock Family Theatre': '#ff7043',
        'Footlight Club': '#5c6bc0'
    };

    /**
     * Get the color for a theater, with fallback for unknown theaters.
     */
    function getTheaterColor(theaterName) {
        return THEATER_COLORS[theaterName] || '#6b7280';
    }

    /**
     * Initialize the application: fetch data, set up events, render.
     */
    async function init() {
        setupEventListeners();
        await loadData();
        initFilters(state.shows);
        applyFilters();
        renderCurrentView();
    }

    /**
     * Fetch shows.json and status.json from the data directory.
     */
    async function loadData() {
        try {
            const [showsRes, statusRes] = await Promise.all([
                fetch('./data/shows.json'),
                fetch('./data/status.json')
            ]);

            if (showsRes.ok) {
                const showsData = await showsRes.json();
                state.shows = showsData.shows || [];
            } else {
                state.shows = [];
            }

            if (statusRes.ok) {
                state.status = await statusRes.json();
            }
        } catch (err) {
            console.error('Failed to load data:', err);
            state.shows = [];
            state.status = null;
        }

        // Render status regardless of show data success
        if (state.status) {
            renderStatus(state.status);
        }
    }

    /**
     * Set up event listeners for view toggle and filter changes.
     */
    function setupEventListeners() {
        // View toggle buttons
        document.querySelectorAll('.view-toggle button').forEach(btn => {
            btn.addEventListener('click', () => {
                const view = btn.dataset.view;
                switchView(view);
            });
        });

        // Filter changes
        document.getElementById('filter-start').addEventListener('change', onFilterChange);
        document.getElementById('filter-end').addEventListener('change', onFilterChange);
        document.getElementById('filter-reset').addEventListener('click', resetFilters);
    }

    /**
     * Switch between card and calendar views.
     */
    function switchView(viewName) {
        state.currentView = viewName;

        // Update button states
        document.querySelectorAll('.view-toggle button').forEach(btn => {
            const isActive = btn.dataset.view === viewName;
            btn.classList.toggle('active', isActive);
            btn.setAttribute('aria-pressed', isActive);
        });

        renderCurrentView();
    }

    /**
     * Handle filter input changes.
     */
    function onFilterChange() {
        applyFilters();
        renderCurrentView();
    }

    /**
     * Apply current filters to the shows list.
     */
    function applyFilters() {
        const startInput = document.getElementById('filter-start').value;
        const endInput = document.getElementById('filter-end').value;
        const selectedTheaters = getSelectedTheaters();

        state.filters.startDate = startInput;
        state.filters.endDate = endInput;
        state.filters.theaters = selectedTheaters;

        // Card view: date + theater filters
        state.filteredShows = getFilteredShows(
            state.shows,
            state.filters.startDate,
            state.filters.endDate,
            state.filters.theaters
        );

        // Sort by end date ascending (soonest-ending first)
        state.filteredShows.sort((a, b) => a.end_date.localeCompare(b.end_date));

        // Calendar view: theater filter only (month nav handles date)
        state.calendarShows = getFilteredShows(
            state.shows,
            '', // no date start
            '', // no date end
            state.filters.theaters
        );
    }

    /**
     * Reset all filters to defaults.
     */
    function resetFilters() {
        setDefaultDates();
        // Uncheck all theater checkboxes
        document.querySelectorAll('#theater-dropdown-menu input').forEach(cb => cb.checked = false);
        updateTheaterButtonLabel();
        applyFilters();
        renderCurrentView();
    }

    /**
     * Set default date range (today to end of next month).
     */
    function setDefaultDates() {
        const today = new Date();
        const nextMonth = new Date(today.getFullYear(), today.getMonth() + 2, 0);

        document.getElementById('filter-start').value = formatDateInput(today);
        document.getElementById('filter-end').value = formatDateInput(nextMonth);
    }

    /**
     * Format a Date object to YYYY-MM-DD for input[type=date].
     */
    function formatDateInput(date) {
        return date.toISOString().split('T')[0];
    }

    /**
     * Render the currently active view.
     */
    function renderCurrentView() {
        const container = document.getElementById('content');

        if (state.shows.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No show data available</h3>
                    <p>Show data will be available after the next scraper run.</p>
                </div>
            `;
            return;
        }

        if (state.currentView === 'card') {
            if (state.filteredShows.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>No shows match your filters</h3>
                        <p>Try adjusting the date range or theater selection.</p>
                    </div>
                `;
                return;
            }
            renderCards(state.filteredShows, container);
        } else {
            renderCalendar(state.calendarShows, container);
        }
    }

    /**
     * Format a date string for display (e.g., "Jul 18, 2026").
     */
    function formatDisplayDate(dateStr) {
        const date = new Date(dateStr + 'T00:00:00');
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }

    // Public API
    return {
        init,
        state,
        getTheaterColor,
        formatDisplayDate,
        THEATER_COLORS
    };
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', App.init);
