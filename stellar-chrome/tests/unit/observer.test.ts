import { describe, it, expect, vi, beforeEach } from "vitest";
import { createConversationObserver } from "../../src/content/shared/observer";
import type { SiteSelectors, ExtractedMessage } from "../../src/types";

const mockSelectors: SiteSelectors = {
  messageContainer: "#messages",
  userMessage: ".user-msg",
  assistantMessage: ".ai-msg",
  messageText: ".text",
  inputArea: "#input",
  submitButton: "#submit",
  formElement: "form",
};

describe("createConversationObserver", () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="messages"></div>';
  });

  it("connects to container", () => {
    const callback = vi.fn();
    const obs = createConversationObserver(mockSelectors, callback);
    expect(obs).toBeDefined();
    expect(obs.disconnect).toBeInstanceOf(Function);
    obs.disconnect();
  });

  it("detects user messages added to container", async () => {
    const messages: ExtractedMessage[] = [];
    const obs = createConversationObserver(mockSelectors, (msg) =>
      messages.push(msg),
    );

    // Simulate adding a user message
    const container = document.querySelector("#messages")!;
    const userDiv = document.createElement("div");
    userDiv.className = "user-msg";
    userDiv.innerHTML = '<span class="text">Hello AI</span>';
    container.appendChild(userDiv);

    // Wait for MutationObserver + debounce
    await new Promise((r) => setTimeout(r, 400));

    expect(messages.length).toBeGreaterThanOrEqual(1);
    expect(messages[0].role).toBe("user");
    expect(messages[0].content).toBe("Hello AI");

    obs.disconnect();
  });

  it("detects assistant messages", async () => {
    const messages: ExtractedMessage[] = [];
    const obs = createConversationObserver(mockSelectors, (msg) =>
      messages.push(msg),
    );

    const container = document.querySelector("#messages")!;
    const aiDiv = document.createElement("div");
    aiDiv.className = "ai-msg";
    aiDiv.innerHTML = '<span class="text">Hello human</span>';
    container.appendChild(aiDiv);

    await new Promise((r) => setTimeout(r, 400));

    expect(messages.length).toBeGreaterThanOrEqual(1);
    expect(messages[0].role).toBe("assistant");

    obs.disconnect();
  });
});
