document.addEventListener('click', (e) => {
    const btn = e.target.closest('.post-info-btn')

    if (btn) {
        e.stopPropagation()
        const tooltip = btn.parentElement.querySelector('.post-tooltip')

        document.querySelectorAll('.post-tooltip').forEach(t => {
            if (t !== tooltip) t.classList.remove('active')
        })

        tooltip.classList.toggle('active')
        return
    }

    document.querySelectorAll('.post-tooltip').forEach(t => {
        t.classList.remove('active')
    })
})