document.querySelectorAll('.stats-item[data-list]').forEach(item => {
    item.addEventListener('click', async (e) => {
        e.preventDefault()
        const username = document.querySelector('.stats').dataset.username
        const listType = item.dataset.list
        const url = `/profile/${username}/${listType}_list`

        const response = await fetch(url, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })

        if (!response.ok) {
            const data = await response.json()
            showToast(data.error || 'Не удалось открыть список', 'error')
            return
        }

        window.location.href = url
    })
})