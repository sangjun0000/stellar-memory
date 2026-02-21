import type { SiteSelectors } from "../../types";

const MAX_CONTENT_LENGTH = 10_000;

export function extractText(
  element: HTMLElement,
  textSelector: string,
): string {
  const textEl = element.querySelector(textSelector);
  const raw = textEl?.textContent ?? element.textContent ?? "";
  return raw.trim().slice(0, MAX_CONTENT_LENGTH);
}

export function findInputArea(
  selectors: SiteSelectors,
): HTMLElement | null {
  // Primary: specified selector
  let el = document.querySelector<HTMLElement>(selectors.inputArea);
  if (el) return el;

  // Fallback: common patterns
  el =
    document.querySelector<HTMLElement>("textarea[placeholder]") ||
    document.querySelector<HTMLElement>("[contenteditable='true']");
  if (el) return el;

  console.warn("[Stellar] Input area not found. Memory injection disabled.");
  return null;
}

export function getInputText(el: HTMLElement | null): string {
  if (!el) return "";
  if (el instanceof HTMLTextAreaElement) return el.value;
  return el.textContent ?? "";
}

export function setInputText(el: HTMLElement | null, text: string): void {
  if (!el) return;
  if (el instanceof HTMLTextAreaElement) {
    el.value = text;
    el.dispatchEvent(new Event("input", { bubbles: true }));
  } else if (el.getAttribute("contenteditable")) {
    el.textContent = text;
    el.dispatchEvent(new InputEvent("input", { bubbles: true }));
  }
}
