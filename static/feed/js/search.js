const input = document.querySelector('.search-input input')
const container = document.querySelector('.search-result')

const initialHTML = container.innerHTML

input.addEventListener('input', async () => {
    const query = input.value.trim()

    if (query.length < 2) {
        container.innerHTML = initialHTML
        return
    }

    const response = await fetch(`/search/users?query=${query}`)
    const users = await response.json()

    if (users.length === 0) {
        container.innerHTML = '<div class="not-found"><p>Таких пользователей не найдено</p></div>'
        return
    }

    container.innerHTML = users.map(user => `
        <div class="result">
            <img class="result-avatar" src="${user.avatar_url || '/static/feed/images/default_avatar.svg'}" alt="">
            <p class="result-name">${user.username}</p>
        </div>
    `).join('')
})