let activeTab = 'users'

const input = document.querySelector('.search-field')
const container = document.getElementById('results-container')
const tabs = document.querySelectorAll('.category-element[data-tab]')

const placeholders = {
    users: 'Начните вводить имя...',
    posts: 'Начните вводить текст поста...',
}

const usersInitialHTML = container.innerHTML

tabs.forEach(tab => {
    tab.addEventListener('click', async () => {
        activeTab = tab.dataset.tab

        tabs.forEach(t => t.classList.remove('open'))
        tab.classList.add('open')

        input.placeholder = placeholders[activeTab]
        input.value = ''

        if (activeTab === 'users') {
            container.innerHTML = usersInitialHTML
        } else {
            await loadPosts('')
        }
    })
})

input.addEventListener('input', async () => {
    const query = input.value.trim()

    if (activeTab === 'users') {
        if (query.length < 2) {
            container.innerHTML = usersInitialHTML
            return
        }
        const users = await fetch(`/search/users?query=${encodeURIComponent(query)}`).then(r => r.json())
        renderUsers(users)
    } else {
        await loadPosts(query)
    }
})

function renderUsers(users) {
    if (users.length === 0) {
        container.innerHTML = '<p style="display: flex; justify-content: center; align-items: center;">Таких пользователей не найдено</p>';
        return
    }
    container.innerHTML = users.map(u => `
        <a href="/profile/${u.username}">
            <div class="result">
                <img class="result-avatar" src="${u.avatar_url || '/static/feed/images/default_avatar.svg'}">
                <p class="result-name">${u.username}</p>
            </div>
        </a>`).join('')
}

async function loadPosts(query) {
    const url = `/search/posts?query=${encodeURIComponent(query)}`
    const posts = await fetch(url).then(r => r.json())

    if (!posts.length) {
        container.innerHTML = '<div class="not-found"><p>Постов не найдено</p></div>'
        return
    }
    container.innerHTML = `<div class="posts">${posts.map(renderPostCard).join('')}</div>`

    processHashtags();
}

function renderPostCard(p) {
    return `
        <div class="post-wrapper" data-post-id="${p.id}">
            <div class="post">
                <div class="post-header">
                    <a href="/profile/${p.author_username}">
                        <img class="post-avatar" src="${p.author_avatar || '/static/feed/images/default_avatar.svg'}">
                    </a>
                    <div class="post-user-info">
                        <a href="/profile/${p.author_username}">
                            <p class="post-username">${p.author_username}</p>
                        </a>
                        <p class="post-time">${p.created_at}</p>
                    </div>
                    <div class="post-info">
                        <p class="post-info-btn">i</p>
                        <div class="post-tooltip">
                            ${p.task_title}
                        </div>
                    </div>
                </div>
                ${p.image_url ? `<img class="post-image" src="${p.image_url}">` : ''}
                ${p.text ? `<p class="post-text">${p.text}</p>` : ''}
            </div>
            <div class="post-footer">
                <div class="like ${p.is_liked ? 'liked' : ''}" data-post-id="${p.id}">
                    <img src="${p.is_liked ? '/static/feed/images/like-filled.svg' : '/static/feed/images/like.svg'}" class="like-icon">
                    <p>${p.likes_count}</p>
                </div>
                <div class="comment" data-post-id="${p.id}">
                    <img src="/static/feed/images/comment.svg" class="comment-icon">
                    <p>${p.comments_count}</p>
                </div>
            </div>
            <div class="comments-section">
                <div class="comments-list"></div>

                <div class="comment-input-row">
                    <img class="comment-avatar" src="${p.current_user?.avatar_url || '/static/feed/images/default_avatar.svg'}">
                    <textarea maxlength="500" class="comment-input" placeholder="Написать комментарий..." rows="1"></textarea>
                    <button class="comment-send-btn">
                        <img src="/static/feed/images/send-comment.svg">
                    </button>
                </div>

                <p class="error" style="display:none"></p>
            </div>
        </div>`
}

const urlParams = new URLSearchParams(window.location.search)
const q = urlParams.get('q')

if (q) {
    tabs.forEach(t => t.classList.remove('open'))
    document.querySelector('[data-tab="posts"]').classList.add('open')
    activeTab = 'posts'
    input.placeholder = placeholders.posts
    input.value = q
    loadPosts(q)
}