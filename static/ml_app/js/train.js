let launchButton = document.getElementById("launch")
let progress = document.getElementById("progress")
import { fetchTaskStatus } from "./main.js"
async function fetchApi() {
    const response = await fetch(progress.dataset.url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")  // Important pour Django
        },
        body: JSON.stringify({})
    });

    const result = await response.json();
    console.log(result); // Affiche la réponse de l'API
    return result.url
}



launchButton.onclick = () => {
    const task_promise = fetchApi()
    const intervalId = setInterval(async () => {
        let status = await fetchTaskStatus(task_promise)
        if (status === "Done") clearInterval(intervalId);
        else {
            progress.innerHTML = '';
            const spinner = document.createElement('div');
            spinner.classList.add('spinner', 'me-2');
            spinner.setAttribute('role', 'status');
            const textElement = document.createElement('span');
            textElement.classList.add('me-2')
            textElement.textContent = `Loading... Task ${status}`;
            progress.appendChild(textElement);
            progress.appendChild(spinner);
        }
    }, 1000)
}