document.addEventListener("DOMContentLoaded", () => {
  const summaryDiv = document.getElementById("summary");
  const advancedBtn = document.getElementById("advancedBtn");

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "summary") {
      summaryDiv.innerText = msg.summary || "No summary available.";
      if (msg.doc_id) {
        advancedBtn.disabled = false;
        advancedBtn.onclick = () => {
          chrome.tabs.create({
            url: `http://localhost:5000/dashboard?doc_id=${encodeURIComponent(msg.doc_id)}`
          });
        };
      }
    }

    if (msg.type === "error") {
      summaryDiv.innerText = "Error: " + msg.message;
    }
  });
});
