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