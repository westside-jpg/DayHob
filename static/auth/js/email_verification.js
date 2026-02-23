const inputs = document.querySelectorAll('.code-input')

// Фокус на первую клетку сразу при загрузке страницы
inputs[0].focus()

inputs.forEach((input, index) => {
    input.addEventListener('input', () => {
        input.value = input.value.replace(/[^0-9]/g, '')
        if (input.value.length === 1 && index < inputs.length - 1) {
            inputs[index + 1].focus()
        }
    })

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Backspace' && input.value === '' && index > 0) {
            inputs[index - 1].focus()
        }
    })
})

document.querySelector('form').addEventListener('submit', (e) => {
    const code = Array.from(inputs).map(i => i.value).join('')

    // Блокируем отправку если не все 6 цифр заполнены
    if (code.length < 6) {
        e.preventDefault()  // отменяем отправку формы
        inputs[code.length].focus()  // фокус на первую пустую клетку
        return
    }

    document.getElementById('full-code').value = code  // просто обновляем значение
})