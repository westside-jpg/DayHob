document.getElementById('avatar-input').addEventListener('change', (e) => {
    const file = e.target.files[0]
    if (!file) return

    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if (!allowedTypes.includes(file.type)) {
        alert('Можно загружать только изображения: JPG, PNG, WEBP, GIF')
        e.target.value = ''
        return
    }

    const url = URL.createObjectURL(file)
    const preview = document.getElementById('preview-avatar')
    preview.src = url
    preview.style.display = 'block'
    document.getElementById('arrow').style.display = 'block'
})

document.getElementById('apply-changes').addEventListener('click', async (e) => {
    const formData = new FormData()
    formData.append('bio', document.getElementById('bio').value)
    const fileInput = document.getElementById('avatar-input')
    if (fileInput.files[0]) {
        formData.append('avatar', fileInput.files[0])
    }

    const response = await fetch('/settings/apply', {
        method: 'POST',
        body: formData
    })
    const results = await response.json()

    const preview = document.getElementById('preview-avatar')
    preview.style.display = 'none'
    document.getElementById('arrow').style.display = 'none'

    new_avatar = document.getElementById('current-avatar')
    new_avatar.src = results.avatar_url

    new_bio = document.getElementById('bio')
    new_bio.value = results.bio

    apply_btn = document.getElementById('apply-changes')

    apply_btn.textContent = "Изменения сохранены"
    apply_btn.style.color = 'white'
    apply_btn.style.background = 'black'

    await new Promise(resolve => setTimeout(resolve, 2000))

    apply_btn.textContent = "Применить настройки"
    apply_btn.style.color = 'black'
    apply_btn.style.background = 'white'
})