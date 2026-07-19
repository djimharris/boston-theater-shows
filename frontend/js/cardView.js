/**
 * Card view rendering — displays shows as a responsive grid of cards.
 */

/**
 * Render the card grid into the given container.
 */
function renderCards(shows, container) {
    const grid = document.createElement('div');
    grid.className = 'card-grid';

    shows.forEach(show => {
        grid.appendChild(createCard(show));
    });

    container.innerHTML = '';
    container.appendChild(grid);
}

/**
 * Create a single show card element.
 */
function createCard(show) {
    const card = document.createElement('article');
    card.className = 'show-card';

    const theaterColor = App.getTheaterColor(show.theater_name);

    // Image or placeholder
    let imageHtml;
    if (show.image_url) {
        imageHtml = `<img class="show-card-image" src="${escapeAttr(show.image_url)}"
                          alt="${escapeAttr(show.title)}" loading="lazy"
                          onerror="this.parentElement.innerHTML='<div class=\\'show-card-image-placeholder\\'>&#127917;</div>'">`;
    } else {
        imageHtml = `<div class="show-card-image-placeholder">&#127917;</div>`;
    }

    // Date display
    const startDisplay = App.formatDisplayDate(show.start_date);
    const endDisplay = App.formatDisplayDate(show.end_date);
    const dateText = show.start_date === show.end_date
        ? startDisplay
        : `${startDisplay} - ${endDisplay}`;

    // Actions
    let actionsHtml = '';
    if (show.ticket_url) {
        actionsHtml += `<a href="${escapeAttr(show.ticket_url)}" target="_blank" rel="noopener" class="btn-ticket">Tickets</a>`;
    }
    actionsHtml += `<a href="${escapeAttr(show.show_url)}" target="_blank" rel="noopener" class="btn-info">More Info</a>`;

    card.innerHTML = `
        ${imageHtml}
        <div class="show-card-body">
            <div class="show-card-theater" style="color: ${theaterColor}">${escapeHtml(show.theater_name)}</div>
            <h3 class="show-card-title">
                <a href="${escapeAttr(show.show_url)}" target="_blank" rel="noopener">${escapeHtml(show.title)}</a>
            </h3>
            <div class="show-card-dates">${escapeHtml(dateText)}</div>
            ${show.description ? `<p class="show-card-description">${escapeHtml(show.description)}</p>` : ''}
            <div class="show-card-actions">${actionsHtml}</div>
        </div>
    `;

    return card;
}

/**
 * Escape attribute value for safe HTML insertion.
 */
function escapeAttr(text) {
    if (!text) return '';
    return text
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}
