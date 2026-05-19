document.querySelectorAll('.post-tools').forEach(tools => {
    const container = tools.querySelector('.tools-container')
    const wrapper = tools.closest('.post-wrapper')

    wrapper.appendChild(container)

    tools.addEventListener('click', (e) => {
        e.stopPropagation()

        document.querySelectorAll('.tools-container.open').forEach(c => {
            if (c !== container) c.classList.remove('open')
        })

        const rect = tools.getBoundingClientRect()
        const wrapperRect = wrapper.getBoundingClientRect()
        container.style.top = (rect.bottom - wrapperRect.top + 5) + 'px'
        container.style.right = (wrapperRect.right - rect.right) + 'px'

        container.classList.toggle('open')
    })
})

document.addEventListener('click', () => {
    document.querySelectorAll('.tools-container.open').forEach(c => {
        c.classList.remove('open')
    })
})

document.querySelectorAll('.tool-btn.danger').forEach(btn => {
    btn.addEventListener('click', async (e) => {
        e.stopPropagation()
        const wrapper = btn.closest('.post-wrapper')
        const postId = wrapper.dataset.postId

        const response = await fetch(`/post/${postId}/delete`, { method: 'POST' })
        const data = await response.json()

        if (data.ok) {
            showToast(data.message, "success")
            wrapper.remove()
            document.querySelector('#posts-count').textContent = data.count
            document.querySelector('#posts-declination').textContent = data.declination
        } else {
            showToast(data.error, "error")
        }
    })
})