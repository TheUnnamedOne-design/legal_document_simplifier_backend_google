// Guard to avoid double-binding if re-injected
if (!window.__mistralFactCheckBound) {
  window.__mistralFactCheckBound = true;

  chrome.runtime.onMessage.addListener((message) => {
    if (message?.type === "SHOW_ALERT") {
      // Keep it simple — show the alert in the page context
      alert("Fact Check:\n\n" + (message.data ?? ""));
    }
  });
}
