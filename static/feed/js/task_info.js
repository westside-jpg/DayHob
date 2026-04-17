document.querySelectorAll('.post-info-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.stopPropagation();

        const tooltip = btn.parentElement.querySelector('.post-tooltip');

        document.querySelectorAll('.post-tooltip').forEach(t => {
            if (t !== tooltip) t.classList.remove('active');
        });

        tooltip.classList.toggle('active');
    });
});

document.addEventListener('click', () => {
    document.querySelectorAll('.post-tooltip').forEach(t => {
        t.classList.remove('active');
    });
});