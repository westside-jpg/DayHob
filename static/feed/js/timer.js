function updateTimer() {
    const now = new Date()

    // Полночь по Владивостоку (UTC+10)
    const nowVlad = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Vladivostok" }))
    const tomorrowVlad = new Date(nowVlad)
    tomorrowVlad.setHours(24, 0, 0, 0)

    const diff = tomorrowVlad - nowVlad
    const hours = Math.floor(diff / 1000 / 3600)
    const minutes = Math.floor((diff / 1000 % 3600) / 60)

    const pad = n => String(n).padStart(2, '0')
    document.querySelector('.daily-time').textContent = `${pad(hours)}:${pad(minutes)}`
}

updateTimer()
setInterval(updateTimer, 30000)