let croppedBlob = null
let cropper = null

document.getElementById('avatar-input').addEventListener('change', (e) => {
    const file = e.target.files[0]
    if (!file) return

    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if (!allowedTypes.includes(file.type)) {
        alert('Можно загружать только изображения: JPG, PNG, WEBP, GIF')
        e.target.value = ''
        return
    }

    const reader = new FileReader()
    reader.onload = (event) => {
        const img = new Image()
        img.onload = () => {
            const image = document.getElementById('crop-image')
            image.src = event.target.result
            image.style.maxHeight = '55vh'
            image.style.width = 'auto'

            if (cropper) cropper.destroy()
            cropper = new Cropper(image, {
                aspectRatio: 1,
                viewMode: 2,
                background: false,
            })

            document.getElementById('crop-modal').style.display = 'flex'
        }
        img.src = event.target.result
    }
    reader.readAsDataURL(file)
    e.target.value = ''
})

document.getElementById('crop-confirm').addEventListener('click', () => {
    const canvas = cropper.getCroppedCanvas({
        width: 800,
        height: 800,
        imageSmoothingQuality: 'high'
    })

    canvas.toBlob(blob => {
        croppedBlob = blob

        const preview = document.getElementById('preview-avatar')
        preview.src = URL.createObjectURL(blob)
        preview.style.display = 'block'
        document.getElementById('arrow').style.display = 'block'
        document.getElementById('crop-modal').style.display = 'none'
    }, 'image/jpeg', 1.0)
})

document.getElementById('apply-changes').addEventListener('click', async () => {
    const bio = document.getElementById('bio').value
    const errorBlock = document.querySelector('.error')
    const btn = document.getElementById('apply-changes')

    if (bio.length > 150) {
        errorBlock.textContent = 'Максимальная длина описания профиля — 150 символов'
        errorBlock.style.display = 'block'

        btn.textContent = "Ошибка"
        btn.style.color = 'white'
        btn.style.background = 'red'
        btn.style.borderColor = 'red'
        btn.disabled = true
        btn.style.cursor = 'not-allowed'

        await new Promise(resolve => setTimeout(resolve, 2000))

        btn.textContent = "Применить настройки"
        btn.style.color = 'black'
        btn.style.background = 'white'
        btn.style.borderColor = 'black'
        btn.disabled = false
        btn.style.cursor = 'pointer'

        return
    }

    btn.textContent = "Подождите, изменения применяются..."
    btn.style.color = 'white'
    btn.style.background = 'gray'
    btn.style.borderColor = 'gray'
    btn.disabled = true
    btn.style.cursor = 'not-allowed'

    errorBlock.style.display = 'none'

    const formData = new FormData()
    formData.append('bio', bio)

    if (croppedBlob) {
        formData.append('avatar', croppedBlob, 'avatar.jpg')
    }

    const response = await fetch('/settings/apply', {
        method: 'POST',
        body: formData
    })

    const results = await response.json()

    if (results.error) {
        errorBlock.textContent = results.error
        errorBlock.style.display = 'block'
        return
    }

    document.getElementById('preview-avatar').style.display = 'none'
    document.getElementById('arrow').style.display = 'none'

    btn.textContent = "Изменения сохранены"
    btn.style.color = 'white'
    btn.style.background = 'black'
    btn.style.borderColor = 'black'

    document.getElementById('current-avatar').src = URL.createObjectURL(croppedBlob)
    document.getElementById('menu-profile-avatar').src = URL.createObjectURL(croppedBlob)

    await new Promise(resolve => setTimeout(resolve, 2000))

    btn.textContent = "Применить настройки"
    btn.style.color = 'black'
    btn.style.background = 'white'
    btn.disabled = false
    btn.style.cursor = 'pointer'
})