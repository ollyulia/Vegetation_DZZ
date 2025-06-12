document.querySelector("form").addEventListener("submit", async (e) => {
    e.preventDefault();
    document.getElementById("submit-button").disabled = true;
    document.getElementById("message").innerHTML = "Запрос получен. Пожалуйста, ожидайте пока программа скачает, обработает и загрузит снимки...";
    const formData = new FormData(e.target);
    const response = await fetch(e.target.action, {
        method: "POST",
        body: formData,
    });
    const data = await response.json();
    document.getElementById("message").innerHTML = data["message"];
    document.getElementById("submit-button").disabled = false;
});

document.getElementById("generate-scale-btn").addEventListener("click", async () => {
    const response = await fetch("/generate_ndvi_scale", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        }
    });

    const data = await response.json();
    const container = document.getElementById("ndvi-scale-container");
    container.innerHTML = `<img src="${data.scale_url}" alt="NDVI шкала">`;
});

document.getElementById("set-coords-btn").addEventListener("click", () => {
    // Устанавливаем координаты Кольского полуострова
    document.getElementById("lower_left_lat").value = 66.275544;
    document.getElementById("lower_left_lon").value = 32.374940;
    document.getElementById("upper_right_lat").value = 69.449708;
    document.getElementById("upper_right_lon").value = 41.010194;

    const messageDiv = document.getElementById('message');
    messageDiv.innerHTML = `
        <div class="info-message">
            Установлены координаты типичной области Кольского полуострова.<br>
            Обратите внимание: NDVI может покрывать не весь регион из-за траекторий движения спутников.
        </div>
    `;
});
