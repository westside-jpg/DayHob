document.querySelectorAll('.comment').forEach(btn => {
    btn.addEventListener('click', async () => {
        const postId = btn.dataset.postId
        const section = btn.closest('.post-wrapper').querySelector('.comments-section')
        const icon = btn.querySelector('.comment-icon')

        if (section.classList.contains('open')) {
            section.classList.remove('open')
            icon.src = '/static/feed/images/comment.svg'
            return
        }

        const response = await fetch(`/post/${postId}/comments`)
        const comments = await response.json()

        const list = section.querySelector('.comments-list')
        list.innerHTML = comments.length === 0 ? '<p style="color:gray;font-size:14px">Комментариев пока нет</p>' :
            comments.map(c => `
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

        const counter = btn.closest('.post-wrapper').querySelector('.comment p')
        counter.textContent = comments.length
        section.classList.add('open')
        icon.src = '/static/feed/images/comment-filled.svg'
    })
})