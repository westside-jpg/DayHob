const photoInput = document.getElementById('photo-input')
const uploadZone = document.getElementById('upload-zone')
const uploadPlaceholder = document.getElementById('upload-placeholder')
const previewImage = document.getElementById('preview-image')
const publishBtn = document.getElementById('publish-btn')
const postText = document.getElementById('post-text')
const editBtn = document.getElementById('edit-btn')
const publishText = document.getElementById('publish-btn-text')
const publishImg = document.getElementById('publish-btn-img')

let selectedFile = null

uploadZone.addEventListener('click', (e) => {
    if (e.target.classList.contains('upload-btn')) return
    if (selectedFile) return
    photoInput.click()
})

// Выбор файла
photoInput.addEventListener('change', (e) => {
    const file = e.target.files[0]
    if (!file) return

    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if (!allowedTypes.includes(file.type)) {
        alert('Можно загружать только изображения: JPG, PNG, WEBP, GIF')
        return
    }

    selectedFile = file
    const url = URL.createObjectURL(file)

    previewImage.onload = () => {
        const imgWidth = previewImage.naturalWidth
        const imgHeight = previewImage.naturalHeight
        const zoneWidth = uploadZone.clientWidth - 24
        let scaledHeight = zoneWidth * imgHeight / imgWidth
        scaledHeight = Math.min(scaledHeight, 600)
        uploadZone.style.height = `${scaledHeight + 24}px`
        previewImage.style.width = `${zoneWidth}px`
        previewImage.style.height = `${scaledHeight}px`
        previewImage.style.objectFit = 'contain'
    }

    previewImage.src = url
    previewImage.classList.add('visible')
    uploadPlaceholder.classList.add('hidden')
    uploadZone.classList.add('has-image')
    editBtn.style.display = 'block'
})

// Drag & Drop
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault()
    uploadZone.style.background = '#f5f5f5'
})

uploadZone.addEventListener('dragleave', () => {
    uploadZone.style.background = ''
})

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault()
    uploadZone.style.background = ''
    const file = e.dataTransfer.files[0]
    if (!file) return
    photoInput.files = e.dataTransfer.files
    photoInput.dispatchEvent(new Event('change'))
})

postText.addEventListener('input', () => {
    postText.style.height = 'auto'
    postText.style.height = `${postText.scrollHeight}px`
})

// Публикация поста
publishBtn.addEventListener('click', async () => {
    const text = postText.value.trim()

    if (!text && !selectedFile) {
        alert('Добавьте фото или описание поста')
        return
    }

    publishBtn.style.background = '#d3d3d3'
    publishBtn.style.borderColor = '#a0a0a0'
    publishBtn.disabled = true
    publishBtn.style.cursor = 'not-allowed'

    publishImg.style.display = 'none'
    publishText.style.display = 'block'

    const formData = new FormData()
    formData.append('text', text)
    if (selectedFile) {
        formData.append('image', selectedFile)
    }

    const response = await fetch('/new-post/create', {
        method: 'POST',
        body: formData
    })

    const data = await response.json()

    if (data.ok) {
        window.location.href = '/feed/?publish=true'
    } else {
        showToast(data.message, 'error')
    }
})