document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.comment')
    if (!btn) return

    const postId = btn.dataset.postId
    if (!postId) return

    const section = btn.closest('.post-wrapper').querySelector('.comments-section')
    const icon = btn.querySelector('.comment-icon')

    const response = await fetch(`/post/${postId}/comments`)
    const comments = await response.json()

    if (comments.error) { showToast(comments.error, "error"); return }

    if (section.classList.contains('open')) {
        section.classList.remove('open')
        icon.src = '/static/feed/images/comment.svg'
        return
    }

    const list = section.querySelector('.comments-list')
    list.innerHTML = comments.length === 0
        ? '<p style="color:gray;font-size:14px">Комментариев пока нет</p>'
        : comments.map(c => `
            <div class="comment-item">
                <div class="comment-header">
                    <a href="/profile/${c.comment_username}">
                        <img class="comment-avatar" src="${c.comment_avatar_url || '/static/feed/images/default_avatar.svg'}">
                    </a>
                    <div class="comment-author-info">
                        <a href="/profile/${c.comment_username}">
                            <p class="comment-username">${c.comment_username}</p>
                        </a>
                        <p class="comment-time">${c.comment_created_at}</p>
                    </div>
                </div>
                <div class="comment-text"><p>${c.comment_text.replace(/\n/g, '<br>')}</p></div>
            </div>`).join('')

    btn.closest('.post-wrapper').querySelector('.comment p').textContent = comments.length
    section.classList.add('open')
    icon.src = '/static/feed/images/comment-filled.svg'
})