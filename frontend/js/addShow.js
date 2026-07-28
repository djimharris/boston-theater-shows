/**
 * Add Show modal — collects show details and copies JSON to clipboard.
 */

(function () {
    const modal = document.getElementById('add-show-modal');
    const form = document.getElementById('add-show-form');
    const openBtn = document.getElementById('add-show-btn');
    const cancelBtn = document.getElementById('add-show-cancel');
    const feedback = document.getElementById('copy-feedback');

    openBtn.addEventListener('click', () => {
        modal.hidden = false;
    });

    cancelBtn.addEventListener('click', closeModal);

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });

    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.hidden) closeModal();
    });

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const entry = {
            title: document.getElementById('add-title').value.trim(),
            theater_name: document.getElementById('add-theater').value.trim(),
            start_date: document.getElementById('add-start').value,
            end_date: document.getElementById('add-end').value,
            show_url: document.getElementById('add-url').value.trim(),
            description: document.getElementById('add-description').value.trim(),
            image_url: document.getElementById('add-image').value.trim(),
            ticket_url: document.getElementById('add-ticket').value.trim(),
        };

        const json = JSON.stringify(entry, null, 2);

        navigator.clipboard.writeText(json).then(() => {
            feedback.hidden = false;
            setTimeout(() => { feedback.hidden = true; }, 2000);
        });
    });

    function closeModal() {
        modal.hidden = true;
        form.reset();
        feedback.hidden = true;
    }
})();
