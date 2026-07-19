/**
 * Calendar view — renders a Gantt-style month grid with colored bars for each show.
 */

// Module-level state for calendar navigation
let calendarMonth = new Date().getMonth();
let calendarYear = new Date().getFullYear();

/**
 * Render the calendar view into the given container.
 */
function renderCalendar(shows, container) {
    container.innerHTML = '';

    const wrapper = document.createElement('div');
    wrapper.className = 'calendar-container';

    // Navigation
    wrapper.appendChild(createCalendarNav());

    // Grid
    const daysInMonth = new Date(calendarYear, calendarMonth + 1, 0).getDate();
    const monthShows = getShowsInMonth(shows, calendarYear, calendarMonth);

    if (monthShows.length === 0) {
        wrapper.innerHTML += `
            <div class="empty-state">
                <h3>No shows this month</h3>
                <p>Try navigating to a different month.</p>
            </div>
        `;
    } else {
        wrapper.appendChild(createCalendarGrid(monthShows, daysInMonth));
    }

    // Legend
    wrapper.appendChild(createLegend(monthShows));

    container.appendChild(wrapper);
}

/**
 * Create month navigation (prev / title / next).
 */
function createCalendarNav() {
    const nav = document.createElement('div');
    nav.className = 'calendar-nav';

    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];

    nav.innerHTML = `
        <button id="cal-prev" aria-label="Previous month">&larr; Prev</button>
        <h2>${monthNames[calendarMonth]} ${calendarYear}</h2>
        <button id="cal-next" aria-label="Next month">Next &rarr;</button>
    `;

    // Attach events after insertion
    setTimeout(() => {
        document.getElementById('cal-prev')?.addEventListener('click', () => {
            calendarMonth--;
            if (calendarMonth < 0) {
                calendarMonth = 11;
                calendarYear--;
            }
            renderCalendar(App.state.calendarShows, document.getElementById('content'));
        });
        document.getElementById('cal-next')?.addEventListener('click', () => {
            calendarMonth++;
            if (calendarMonth > 11) {
                calendarMonth = 0;
                calendarYear++;
            }
            renderCalendar(App.state.calendarShows, document.getElementById('content'));
        });
    }, 0);

    return nav;
}

/**
 * Create the Gantt grid: header row (day numbers) + one row per show.
 */
function createCalendarGrid(shows, daysInMonth) {
    const grid = document.createElement('div');
    grid.className = 'calendar-grid';
    // +1 column for label, then one column per day
    grid.style.gridTemplateColumns = `160px repeat(${daysInMonth}, 1fr)`;

    // Header row
    const headerLabel = document.createElement('div');
    headerLabel.className = 'calendar-day-header';
    headerLabel.textContent = 'Show';
    grid.appendChild(headerLabel);

    for (let d = 1; d <= daysInMonth; d++) {
        const dayHeader = document.createElement('div');
        dayHeader.className = 'calendar-day-header';
        dayHeader.textContent = d;
        grid.appendChild(dayHeader);
    }

    // Show rows
    shows.forEach(show => {
        const color = App.getTheaterColor(show.theater_name);
        const showStart = new Date(show.start_date + 'T00:00:00');
        const showEnd = new Date(show.end_date + 'T00:00:00');
        const monthStart = new Date(calendarYear, calendarMonth, 1);
        const monthEnd = new Date(calendarYear, calendarMonth + 1, 0);

        // Calculate bar start/end days within this month
        const barStartDay = showStart < monthStart ? 1 : showStart.getDate();
        const barEndDay = showEnd > monthEnd ? daysInMonth : showEnd.getDate();

        // Label cell
        const label = document.createElement('div');
        label.className = 'calendar-show-label';
        label.textContent = show.title;
        label.title = `${show.title} (${show.theater_name})`;
        grid.appendChild(label);

        // Day cells
        for (let d = 1; d <= daysInMonth; d++) {
            const cell = document.createElement('div');
            cell.className = 'calendar-cell';

            if (d >= barStartDay && d <= barEndDay) {
                const bar = document.createElement('div');
                bar.className = 'calendar-bar';
                bar.style.backgroundColor = color;

                if (d === barStartDay) bar.classList.add('calendar-bar-start');
                if (d === barEndDay) bar.classList.add('calendar-bar-end');

                // Tooltip data
                bar.dataset.title = show.title;
                bar.dataset.theater = show.theater_name;
                bar.dataset.dates = `${App.formatDisplayDate(show.start_date)} - ${App.formatDisplayDate(show.end_date)}`;

                bar.addEventListener('mouseenter', showTooltip);
                bar.addEventListener('mouseleave', hideTooltip);
                bar.addEventListener('click', () => {
                    window.open(show.show_url, '_blank');
                });

                cell.appendChild(bar);
            }

            grid.appendChild(cell);
        }
    });

    return grid;
}

/**
 * Filter shows to those that overlap the given month.
 */
function getShowsInMonth(shows, year, month) {
    const monthStart = `${year}-${String(month + 1).padStart(2, '0')}-01`;
    const lastDay = new Date(year, month + 1, 0).getDate();
    const monthEnd = `${year}-${String(month + 1).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;

    return shows.filter(show => show.start_date <= monthEnd && show.end_date >= monthStart);
}

/**
 * Create the legend showing theater color mapping.
 */
function createLegend(shows) {
    const theaters = [...new Set(shows.map(s => s.theater_name))].sort();
    const legend = document.createElement('div');
    legend.className = 'calendar-legend';

    theaters.forEach(name => {
        const item = document.createElement('div');
        item.className = 'legend-item';
        const color = App.getTheaterColor(name);
        item.innerHTML = `
            <span class="legend-swatch" style="background: ${color}"></span>
            <span>${escapeHtml(name)}</span>
        `;
        legend.appendChild(item);
    });

    return legend;
}

/**
 * Show tooltip near the hovered bar.
 */
function showTooltip(e) {
    hideTooltip(); // Remove any existing

    const bar = e.target;
    const tooltip = document.createElement('div');
    tooltip.className = 'calendar-tooltip';
    tooltip.id = 'cal-tooltip';
    tooltip.innerHTML = `
        <div class="calendar-tooltip-title">${escapeHtml(bar.dataset.title)}</div>
        <div class="calendar-tooltip-theater">${escapeHtml(bar.dataset.theater)}</div>
        <div class="calendar-tooltip-dates">${escapeHtml(bar.dataset.dates)}</div>
    `;

    document.body.appendChild(tooltip);
    positionTooltip(tooltip, e);

    bar.addEventListener('mousemove', (ev) => positionTooltip(tooltip, ev));
}

/**
 * Position tooltip near the cursor.
 */
function positionTooltip(tooltip, e) {
    const offset = 12;
    let x = e.clientX + offset;
    let y = e.clientY + offset;

    // Keep tooltip within viewport
    const rect = tooltip.getBoundingClientRect();
    if (x + rect.width > window.innerWidth) {
        x = e.clientX - rect.width - offset;
    }
    if (y + rect.height > window.innerHeight) {
        y = e.clientY - rect.height - offset;
    }

    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
}

/**
 * Remove tooltip from DOM.
 */
function hideTooltip() {
    const existing = document.getElementById('cal-tooltip');
    if (existing) existing.remove();
}
