import type { SiteSelectors, ExtractedMessage } from "../../types";
import { extractText } from "./extractor";

const RETRY_INTERVAL = 1000;
const MAX_RETRIES = 30;
const DEBOUNCE_MS = 300;

export function createConversationObserver(
  selectors: SiteSelectors,
  onNewMessage: (msg: ExtractedMessage) => void,
): { disconnect: () => void } {
  let observer: MutationObserver | null = null;
  let debounceTimer: ReturnType<typeof setTimeout>;
  const processedNodes = new WeakSet<Node>();

  function processNode(node: Node) {
    if (!(node instanceof HTMLElement)) return;
    if (processedNodes.has(node)) return;
    processedNodes.add(node);

    const userMsg = node.matches(selectors.userMessage)
      ? node
      : node.querySelector<HTMLElement>(selectors.userMessage);
    const aiMsg = node.matches(selectors.assistantMessage)
      ? node
      : node.querySelector<HTMLElement>(selectors.assistantMessage);

    if (userMsg) {
      const text = extractText(userMsg, selectors.messageText);
      if (text) onNewMessage({ role: "user", content: text });
    }
    if (aiMsg) {
      const text = extractText(aiMsg, selectors.messageText);
      if (text) onNewMessage({ role: "assistant", content: text });
    }
  }

  function startObserving(container: Element) {
    observer = new MutationObserver((mutations) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        for (const mutation of mutations) {
          for (const node of mutation.addedNodes) {
            processNode(node);
          }
        }
      }, DEBOUNCE_MS);
    });

    observer.observe(container, { childList: true, subtree: true });
  }

  // Retry until container is found (SPA loading)
  let retries = 0;
  function tryConnect() {
    const container = document.querySelector(selectors.messageContainer);
    if (container) {
      startObserving(container);
      return;
    }
    if (retries < MAX_RETRIES) {
      retries++;
      setTimeout(tryConnect, RETRY_INTERVAL);
    } else {
      console.warn("[Stellar] Message container not found after retries.");
    }
  }

  tryConnect();

  return {
    disconnect() {
      observer?.disconnect();
      clearTimeout(debounceTimer);
    },
  };
}
