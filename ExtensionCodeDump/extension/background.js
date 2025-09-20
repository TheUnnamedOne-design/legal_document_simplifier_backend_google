chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "sendText") {
    fetch("http://localhost:3000/pdf-text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: message.text })
    })
      .then(res => res.json())
      .then(data => sendResponse({ snippet: data.snippet }))
      .catch(err => sendResponse({ error: err.toString() }));

    return true; // keep sendResponse async
  }
});
