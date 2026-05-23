document.querySelectorAll('.like').forEach(btn => {
    btn.addEventListener('click', async () => {
        const postId = btn.dataset.postId

        if (!postId) {
            showToast("Пост не найден", "error");
            return;
        }

        const response = await fetch(`/post/${postId}/like`, {
            method: 'POST'
        })
        const data = await response.json()

        if (data.error) {
                showToast(data.error, "error")
                return
        }

        if (data.ok) {
            const icon = btn.querySelector('.like-icon')
            const counter = btn.querySelector('p')
            if (data.liked) {
                btn.classList.add('liked')
                icon.src = '/static/feed/images/like-filled.svg'
            } else {
                btn.classList.remove('liked')
                icon.src = '/static/feed/images/like.svg'
            }
            counter.textContent = data.count
        } else {
            showToast(data.error, "error")
        }
    })
})