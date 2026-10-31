const terminal = document.getElementById("terminal");
const command = document.getElementById("command");

function escapeHTML(text) {
    return text
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
}

if (command && terminal) {
    command.addEventListener("keydown", async function(event) {
        if (event.key !== "Enter") return;

        event.preventDefault();
        const text = command.value;
        if (!text.trim()) return;

        terminal.innerHTML += `<span class="input">db&gt; ${escapeHTML(text)}</span>\n`;
        command.value = "";

        try {
            const response = await fetch("/db/execute", {
                method: "POST",
                headers: { "Content-Type": "text/plain" },
                body: text
            });

            const result = await response.text();
            terminal.innerHTML += escapeHTML(result) + "\n";
        } catch (error) {
            terminal.innerHTML += `<span class="error">${escapeHTML(error.toString())}</span>\n`;
        }

        terminal.scrollTop = terminal.scrollHeight;
    });
}

