document.querySelectorAll('.like').forEach(btn => {
    btn.addEventListener('click', async () => {
        const postId = btn.dataset.postId
        const icon = btn.querySelector('.like-icon')
        const counter = btn.querySelector('p')

        const response = await fetch(`/post/${postId}/like`, {
            method: 'POST'
        })
        const data = await response.json()

        if (data.liked) {
            btn.classList.add('liked')
            icon.src = '/static/feed/images/like-filled.svg'
        } else {
            btn.classList.remove('liked')
            icon.src = '/static/feed/images/like.svg'
        }
        counter.textContent = data.count
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