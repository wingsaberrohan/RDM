const RDM_SERVER = "http://127.0.0.1:8765";

chrome.action.onClicked.addListener(async (tab) => {
  const url = tab?.url;
  if (url && (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("ftp://"))) {
    try {
      const res = await fetch(`${RDM_SERVER}/add?url=${encodeURIComponent(url)}`, { method: "GET" });
      if (res.ok) {
        chrome.action.setTitle({ title: "Sent to RDM" });
        setTimeout(() => chrome.action.setTitle({ title: "Send to RDM" }), 2000);
      }
    } catch (e) {
      chrome.action.setTitle({ title: "RDM not running?" });
      setTimeout(() => chrome.action.setTitle({ title: "Send to RDM" }), 3000);
    }
  }
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "rdm-send-link",
    title: "Send link to RDM",
    contexts: ["link"]
  });
});

chrome.contextMenus.onClicked.addListener(async (info) => {
  if (info.menuItemId === "rdm-send-link" && info.linkUrl) {
    try {
      await fetch(`${RDM_SERVER}/add?url=${encodeURIComponent(info.linkUrl)}`, { method: "GET" });
    } catch (e) {}
  }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "sendToRDM" && msg.url) {
    fetch(`${RDM_SERVER}/add?url=${encodeURIComponent(msg.url)}`, { method: "GET" })
      .then(r => sendResponse({ ok: r.ok }))
      .catch(() => sendResponse({ ok: false }));
    return true;
  }
});
