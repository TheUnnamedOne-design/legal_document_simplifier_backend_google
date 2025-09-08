// Create context menu once (persists across restarts)
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "factCheckMistral",
    title: "Fact Check with Mistral",
    contexts: ["selection"]
  });
});

// Helper: try to display in page; fallback to notification if context missing
async function displayResult(tabId, text) {
  try {
    // Send to content script (preferred, avoids context invalidated)
    await chrome.tabs.sendMessage(tabId, { type: "SHOW_ALERT", data: text });
  } catch (err) {
    // If tab navigated/unloaded or no content script, show desktop notification
    chrome.notifications.create({
      type: "basic",
      iconUrl: "icon128.png",
      title: "Mistral Fact Check",
      message: (text || "").slice(0, 1000)
    });
  }
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "factCheckMistral") return;

  // Basic guard: only attempt on http(s) pages with a selection
  const sentence = (info.selectionText || "").trim();
  if (!sentence) {
    if (tab?.id) displayResult(tab.id, "No text selected.");
    return;
  }

  try {
    const resp = await fetch("http://127.0.0.1:5000/factcheck", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sentence })
    });

    // Handle non-OK (preflight/CORS or server errors)
    if (!resp.ok) {
      const txt = await resp.text();
      await displayResult(tab.id, `Server error (${resp.status}): ${txt}`);
      return;
    }

    const data = await resp.json();
    await displayResult(tab.id, data.reply || "(empty reply)");
  } catch (e) {
    await displayResult(tab.id, "Fetch failed: " + e);
  }
});
