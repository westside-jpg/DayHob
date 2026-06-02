const messagesContainer = document.querySelector('.chat-messages')
const input = document.querySelector('.chat-footer textarea')
const sendBtn = document.querySelector('.send-message')
const scrollBtn = document.getElementById('scroll-btn')
const scrollCount = document.getElementById('scroll-count')

let unreadCount = 0
let isAtBottom = true

// Подвижная кнопка скролла вниз
function updateScrollButtonPosition() {
    const footer = document.querySelector('.chat-footer')

    scrollBtn.style.bottom =
        (footer.offsetHeight + 20) + 'px'
}

// Слежка за скроллом
messagesContainer.addEventListener('scroll', () => {
    const threshold = 100
    isAtBottom = messagesContainer.scrollHeight - messagesContainer.scrollTop - messagesContainer.clientHeight < threshold

    if (isAtBottom) {
    scrollBtn.classList.remove('visible')
        unreadCount = 0
        scrollCount.textContent = ''
    } else {
        scrollBtn.classList.add('visible')
        if (unreadCount == 0) {
            scrollCount.style.display = 'none'
        }
    }
})

// Скролл вниз по кнопке
scrollBtn.addEventListener('click', () => {
    messagesContainer.scrollTo({ top: messagesContainer.scrollHeight, behavior: 'smooth' })
    scrollBtn.classList.remove('visible')
    unreadCount = 0
    scrollCount.textContent = ''
})

// Добавление сообщения в DOM
function appendMessage(text, time, isMine) {
    const div = document.createElement('div')
    div.className = isMine ? 'user-messages' : 'companion-messages'
    const safeText = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\n/g, '<br>')
    div.innerHTML = `
        <p class="${isMine ? 'user' : 'companion'}-message">${safeText}</p>
        <p class="${isMine ? 'user' : 'companion'}-message-time">${time}</p>
    `
    messagesContainer.appendChild(div)

    if (isMine) {
        // Отправитель: всегда скроллим вниз
        messagesContainer.scrollTop = messagesContainer.scrollHeight
    } else {
        // Получатель: показываем кнопку если не внизу
        if (!isAtBottom) {
            unreadCount++
            scrollCount.style.display = 'flex'
            scrollCount.textContent = unreadCount
            scrollBtn.classList.add('visible')
        } else {
            messagesContainer.scrollTop = messagesContainer.scrollHeight
        }
    }
}

// Авторасширение текстареа
input.addEventListener('input', () => {
    input.style.height = 'auto'
    input.style.height = Math.min(input.scrollHeight, 150) + 'px'

    updateScrollButtonPosition()
})

// Отправка сообщения
function sendMessage() {
    const text = input.value.trim()
    if (!text) return
    ws.send(JSON.stringify({ text }))
    const now = new Date()
    const time = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0')
    appendMessage(text, time, true)
    input.value = ''
    input.style.height = 'auto'
}

// Enter отправляет, Shift+Enter переносит строку
input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        sendMessage()
        updateScrollButtonPosition()
    }
})

sendBtn.addEventListener('click', sendMessage)

// WebSocket для чата
const companionUsername = document.querySelector('.header-info p').textContent.trim()
const ws = new WebSocket(`ws://127.0.0.1:8000/chats/${companionUsername}/ws`)

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    appendMessage(msg.text, msg.time, false)
}

// Скролл вниз при загрузке
messagesContainer.scrollTop = messagesContainer.scrollHeight

updateScrollButtonPosition()