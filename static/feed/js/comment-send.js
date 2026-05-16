document.querySelectorAll('.comment-send-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        const wrapper = btn.closest('.post-wrapper')
        const postId = wrapper.querySelector('.comment').dataset.postId
        const input = wrapper.querySelector('.comment-input')
        const text = input.value.trim()
        const error = wrapper.querySelector('.error')  // ← только для этого поста
        const send_button = btn

        if (!text) return

        if (text.length > 500) {
            const icon = send_button.querySelector('img')

            error.textContent = 'Длина комментария больше 500 символов'
            error.style.display = 'block'
            send_button.style.background = 'red'
            send_button.style.borderColor = 'red'
            icon.style.filter = 'invert(1) brightness(2)'
            send_button.disabled = true
            send_button.style.cursor = 'not-allowed'

            await new Promise(resolve => setTimeout(resolve, 2000))

            send_button.style.background = ''
            send_button.style.borderColor = 'black'
            icon.style.filter = ''
            send_button.disabled = false
            send_button.style.cursor = 'pointer'

            return
        }

        error.style.display = 'none'

        const formData = new FormData()
        formData.append('text', text)

        await fetch(`/post/${postId}/post-comment`, {
            method: 'POST',
            body: formData
        })

        input.value = ''
        input.style.height = 'auto'

        const response = await fetch(`/post/${postId}/comments`)
        const comments = await response.json()
        const list = wrapper.querySelector('.comments-list')
        list.innerHTML = comments.map(c => `
            <div class="comment-item">
                <div class="comment-header">
                    <a href="/profile/${ c.comment_username }">
                        <img class="comment-avatar" src="${c.comment_avatar_url || '/static/feed/images/default_avatar.svg'}">
                    </a>
                    <div class="comment-author-info">
                        <a href="/profile/${ c.comment_username }">
                            <p class="comment-username">${c.comment_username}</p>
                        </a>
                        <p class="comment-time">${c.comment_created_at}</p>
                    </div>
                </div>
                <div class="comment-text"><p>${c.comment_text}</p></div>
            </div>
        `).join('')

        const counter = wrapper.querySelector('.comment p')
        counter.textContent = comments.length
    })
})