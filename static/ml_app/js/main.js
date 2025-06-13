
async function fetchTaskStatus(task_promise) {
    const task_url = await task_promise
    const response = await fetch(task_url, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")  // Important pour Django
        },
    });
    const results = await response.json()
    console.log(results)
    return results.status
}
