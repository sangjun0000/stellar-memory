import type { SiteSelectors } from "../types";

export const SELECTORS: Record<string, SiteSelectors> = {
  chatgpt: {
    messageContainer: "main .flex.flex-col",
    userMessage: "[data-message-author-role='user']",
    assistantMessage: "[data-message-author-role='assistant']",
    messageText: ".markdown",
    inputArea: "#prompt-textarea",
    submitButton: "[data-testid='send-button']",
    formElement: "form",
  },
  claude: {
    messageContainer: "[class*='conversation']",
    userMessage: "[data-testid='user-message']",
    assistantMessage: "[data-testid='ai-message']",
    messageText: "[class*='message-content']",
    inputArea: "[contenteditable='true']",
    submitButton: "button[aria-label='Send']",
    formElement: "form",
  },
  gemini: {
    messageContainer: ".conversation-container",
    userMessage: ".user-query",
    assistantMessage: ".model-response",
    messageText: ".message-content",
    inputArea: "rich-textarea .ql-editor",
    submitButton: "button.send-button",
    formElement: "form",
  },
};
