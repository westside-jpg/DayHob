function escapeHTML(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function HighlightHashtags(text) {
    const escaped = escapeHTML(text);

    return escaped.replace(
        /#([\p{L}\p{N}_]+)/gu,
        '<a href="/search?q=%23$1" class="hashtag">#$1</a>'
    );
}

function processHashtags() {
    document.querySelectorAll(".post-text").forEach(post => {
        post.innerHTML = HighlightHashtags(post.textContent);
    });
}

processHashtags();