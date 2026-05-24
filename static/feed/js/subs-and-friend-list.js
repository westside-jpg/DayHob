document.querySelectorAll('.stats-item[data-list]').forEach(item => {
    item.addEventListener('click', async (e) => {
        e.preventDefault()

        const stats = document.querySelector('.stats')
        const username = stats.dataset.username
        const listType = item.dataset.list
        const url = `/profile/${username}/${listType}_list`

        try {
            const response = await fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })

            let data = {}
            const type = response.headers.get('content-type') || ''
            if (type.includes('application/json')) {
                data = await response.json()
            }

            if (!response.ok || data.ok === false) {
                showToast(data.error || 'Не удалось открыть список', 'error')
                return
            }

            window.location.href = url

        } catch (err) {
            console.error(err)
            showToast('Не удалось открыть список', 'error')
        }
    })
})