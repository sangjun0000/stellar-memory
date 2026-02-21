import { describe, it, expect } from "vitest";
import { formatMemoryContext } from "../../src/content/shared/injector";

describe("injector", () => {
  describe("formatMemoryContext", () => {
    it("returns empty string for no memories", () => {
      expect(formatMemoryContext([])).toBe("");
    });

    it("formats memories with relative time", () => {
      const memories = [
        {
          id: "m1",
          content: "커피를 좋아함",
          zone: 0,
          importance: 0.8,
          source: "chatgpt",
          createdAt: new Date().toISOString(),
        },
      ];

      const result = formatMemoryContext(memories);
      expect(result).toContain("[Stellar Memory");
      expect(result).toContain("커피를 좋아함");
      expect(result).toContain("기억 끝");
    });

    it("includes all memories", () => {
      const memories = [
        { id: "m1", content: "A", zone: 0, importance: 0.8, source: "chatgpt", createdAt: new Date().toISOString() },
        { id: "m2", content: "B", zone: 1, importance: 0.6, source: "claude", createdAt: new Date().toISOString() },
        { id: "m3", content: "C", zone: 2, importance: 0.4, source: "gemini", createdAt: new Date().toISOString() },
      ];

      const result = formatMemoryContext(memories);
      expect(result).toContain("- A");
      expect(result).toContain("- B");
      expect(result).toContain("- C");
    });
  });
});
