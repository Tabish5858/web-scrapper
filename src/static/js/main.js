document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("upload-form");
  if (form) {
    const statusMessage = document.getElementById("status-message");

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const formData = new FormData(form);
      if (statusMessage) {
        statusMessage.textContent = "Uploading...";
      }

      fetch("/upload", {
        method: "POST",
        body: formData,
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Network response was not ok");
          }
          return response.text();
        })
        .then((html) => {
          // Replace entire body content
          document.body.innerHTML = html;
          // Initialize WebSocket after content is replaced
          setTimeout(initializeWebSocket, 100);
        })
        .catch((error) => {
          if (statusMessage) {
            statusMessage.textContent = "Error: " + error.message;
          }
        });
    });
  }
});

function initializeWebSocket() {
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const socket = new WebSocket(`${wsProtocol}//${window.location.hostname}/ws`);
  const resultsBody = document.getElementById("results-body");
  const progressBar = document.getElementById("progress");
  const currentCount = document.getElementById("current");
  const totalCount = document.getElementById("total");
  const downloadLink = document.getElementById("download-link");
  const statusText = document.getElementById("status");

  // Get URLs from hidden data element
  const urlsData = document.getElementById("urls-data");
  if (!urlsData) {
    console.error("URLs data element not found");
    return;
  }

  const urls = JSON.parse(urlsData.textContent);
  console.log("URLs to scrape:", urls);

  socket.onopen = function () {
    console.log("WebSocket connected, starting scrape...");
    statusText.textContent = "Connected, starting scrape...";
    socket.send(
      JSON.stringify({
        type: "start_scrape",
        urls: urls,
      })
    );
  };

  socket.onmessage = function (event) {
    try {
      const data = JSON.parse(event.data);
      console.log("Received:", data.type);

      if (data.type === "progress") {
        const progress = (data.current / data.total) * 100;
        progressBar.style.width = `${progress}%`;
        currentCount.textContent = data.current;
        statusText.textContent = `Scraping: ${data.current}/${data.total} (${data.pages} pages)`;
      } else if (data.type === "result") {
        const row = document.createElement("tr");
        row.className = "result-row";
        row.innerHTML = `
                  <td><a href="${data.result.url}" target="_blank">${
          data.result.url
        }</a></td>
                  <td>${data.result.company_name}</td>
                  <td>${
                    data.result.email !== "N/A"
                      ? `<a href="mailto:${data.result.email}">${data.result.email}</a>`
                      : "N/A"
                  }</td>
                  <td>${
                    data.result.phone !== "N/A"
                      ? `<a href="tel:${data.result.phone}">${data.result.phone}</a>`
                      : "N/A"
                  }</td>
                  <td>${data.result.location}</td>
              `;
        resultsBody.appendChild(row);
      } else if (data.type === "complete") {
        downloadLink.href = `/download/${data.filename}`;
        downloadLink.style.display = "inline-block";
        statusText.textContent = "Scraping Complete!";
      } else if (data.type === "error") {
        console.error("Server error:", data.message);
        statusText.textContent = `Error: ${data.message}`;
      }
    } catch (error) {
      console.error("Error processing message:", error);
      statusText.textContent = "Error processing data";
    }
  };

  socket.onerror = function (error) {
    console.error("WebSocket Error:", error);
    statusText.textContent = "Connection Error";
    // Try to reconnect after 5 seconds
    setTimeout(initializeWebSocket, 5000);
  };

  socket.onclose = function () {
    console.log("WebSocket connection closed");
    if (statusText.textContent !== "Scraping Complete!") {
      statusText.textContent = "Connection lost, retrying...";
      // Try to reconnect after 5 seconds
      setTimeout(initializeWebSocket, 5000);
    }
  };

  return socket;
}
