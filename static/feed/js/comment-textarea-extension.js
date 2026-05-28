document.addEventListener('input', (e) => {
    if (!e.target.classList.contains('comment-input')) return
    e.target.style.height = 'auto'
    e.target.style.height = e.target.scrollHeight + 'px'
})