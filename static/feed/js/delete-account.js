document.querySelector('.delete-account').addEventListener('click', () => {
    const deleteAccount = document.querySelector('.delete-account');
    if (deleteAccount.classList.contains('disabled')) {
        return;
    }

    const modal = document.getElementById('delete-account-modal')
    modal.style.display = 'flex'
    setTimeout(() => modal.classList.add('open'), 10)
})

document.getElementById('delete-no').addEventListener('click', () => {
    const modal = document.getElementById('delete-account-modal')
    modal.classList.remove('open')
    setTimeout(() => modal.style.display = 'none', 300)
})

document.getElementById('delete-yes').addEventListener('click', async() => {
    const response = await fetch(
        `/settings/delete-account`, {
        method: 'POST',
    })
    const data = await response.json()

    if (!data.ok) {
        showToast(data.error, "error")
        return
    }

    window.location.href = '/?deleted=true'

})