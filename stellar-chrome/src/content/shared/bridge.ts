import type { CSMessage, SiteSelectors } from "../../types";
import { findInputArea, getInputText } from "./extractor";

export function sendToBackground(msg: CSMessage): Promise<unknown> {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(msg, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve(response);
      }
    });
  });
}

/**
 * Track input changes and broadcast to Side Panel for real-time recall.
 * Uses 500ms debounce internally to avoid excessive messages.
 */
export function trackInputChanges(selectors: SiteSelectors): void {
  let debounceTimer: ReturnType<typeof setTimeout>;
  let lastText = "";

  function check() {
    const input = findInputArea(selectors);
    const text = getInputText(input).trim();
    if (text !== lastText) {
      lastText = text;
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        chrome.runtime.sendMessage({
          type: "INPUT_CHANGED",
          payload: { text },
        });
      }, 200);
    }
  }

  // Poll for input changes (works across textarea / contenteditable)
  setInterval(check, 500);
}
