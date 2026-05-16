const followBtn = document.querySelector('.follow-btn')
if (followBtn) {
    followBtn.addEventListener('click', async () => {
        const username = followBtn.dataset.username
        const response = await fetch(`/profile/${username}/follow`, { method: 'POST' })
        if (!response.ok) return
        const data = await response.json()

        followBtn.textContent = data.is_subscribed ? 'Отписаться' : 'Подписаться'
        followBtn.classList.toggle('unfollow', data.is_subscribed)
        document.querySelector('#followers-count').textContent = data.followers_count
        document.querySelector('#subs-declination').textContent = data.declination_subs
        document.querySelector('#friends-count').textContent = data.friends_count
        document.querySelector('#friends-declination').textContent = data.declination_friends
        const badge = document.getElementById('push-badge')
        if (data.unread_pushes_count === '0') {
            badge.style.display = 'none'
        } else {
            badge.style.display = 'flex'
            badge.textContent = data.unread_pushes_count
        }
    })
}