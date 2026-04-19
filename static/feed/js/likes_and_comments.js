document.querySelectorAll('.like').forEach(btn => {
    btn.addEventListener('click', () => {
        const icon = btn.querySelector('.like-icon')
        if (btn.classList.contains('liked')) {
            btn.classList.remove('liked')
            icon.src = '/static/feed/images/like.svg'
        } else {
            btn.classList.add('liked')
            icon.src = '/static/feed/images/like-filled.svg'
        }
    })
})

document.querySelectorAll('.comment').forEach(btn => {
    btn.addEventListener('click', () => {
        const icon = btn.querySelector('.comment-icon')
        if (btn.classList.contains('commented')) {
            btn.classList.remove('commented')
            icon.src = '/static/feed/images/comment.svg'
        } else {
            btn.classList.add('commented')
            icon.src = '/static/feed/images/comment-filled.svg'
        }
    })
})