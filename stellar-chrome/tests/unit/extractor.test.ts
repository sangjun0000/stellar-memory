import { describe, it, expect } from "vitest";
import { extractText, getInputText, setInputText } from "../../src/content/shared/extractor";

describe("extractor", () => {
  describe("extractText", () => {
    it("extracts text from matching child", () => {
      const el = document.createElement("div");
      el.innerHTML = '<span class="text">Hello World</span>';
      expect(extractText(el, ".text")).toBe("Hello World");
    });

    it("falls back to element textContent", () => {
      const el = document.createElement("div");
      el.textContent = "Fallback text";
      expect(extractText(el, ".nonexistent")).toBe("Fallback text");
    });

    it("truncates long content", () => {
      const el = document.createElement("div");
      el.innerHTML = `<span class="text">${"a".repeat(20000)}</span>`;
      const result = extractText(el, ".text");
      expect(result.length).toBe(10000);
    });
  });

  describe("getInputText", () => {
    it("returns value from textarea", () => {
      const textarea = document.createElement("textarea");
      textarea.value = "test value";
      expect(getInputText(textarea)).toBe("test value");
    });

    it("returns textContent from div", () => {
      const div = document.createElement("div");
      div.textContent = "div text";
      expect(getInputText(div)).toBe("div text");
    });

    it("returns empty for null", () => {
      expect(getInputText(null)).toBe("");
    });
  });

  describe("setInputText", () => {
    it("sets value on textarea", () => {
      const textarea = document.createElement("textarea");
      setInputText(textarea, "new value");
      expect(textarea.value).toBe("new value");
    });

    it("sets textContent on contenteditable", () => {
      const div = document.createElement("div");
      div.setAttribute("contenteditable", "true");
      setInputText(div, "new content");
      expect(div.textContent).toBe("new content");
    });

    it("does nothing for null", () => {
      setInputText(null, "test");
      // No error thrown
    });
  });
});
