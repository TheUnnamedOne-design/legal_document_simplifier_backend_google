chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "sendText") {
    console.log("📩 Received text from content script. Sending to backend...");

    fetch("http://localhost:3000/pdf-text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: message.text })
    })
      .then(res => res.json())
      .then(data => {
        console.log("✅ Backend snippet:", data.snippet);
        sendResponse({ snippet: data.snippet });
      })
      .catch(err => {
        console.error("❌ Backend error:", err);
        sendResponse({ error: err.toString() });
      });

    return true; // keep sendResponse async
  }
});
