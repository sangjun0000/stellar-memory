import { describe, it, expect } from "vitest";
import { getRelativeTime, debounce, truncate, zoneLabel, zoneEmoji } from "../../src/lib/utils";

describe("utils", () => {
  describe("getRelativeTime", () => {
    it("returns '방금 전' for recent dates", () => {
      const now = new Date().toISOString();
      expect(getRelativeTime(now)).toBe("방금 전");
    });

    it("returns minutes for recent past", () => {
      const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
      expect(getRelativeTime(fiveMinAgo)).toBe("5분 전");
    });

    it("returns hours for same-day past", () => {
      const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString();
      expect(getRelativeTime(threeHoursAgo)).toBe("3시간 전");
    });

    it("returns days for recent past", () => {
      const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString();
      expect(getRelativeTime(twoDaysAgo)).toBe("2일 전");
    });
  });

  describe("truncate", () => {
    it("returns original if short enough", () => {
      expect(truncate("hello", 10)).toBe("hello");
    });

    it("truncates with ellipsis", () => {
      expect(truncate("hello world foo bar", 10)).toBe("hello w...");
    });
  });

  describe("zoneLabel", () => {
    it("maps zone numbers to labels", () => {
      expect(zoneLabel(0)).toBe("Core");
      expect(zoneLabel(1)).toBe("Inner");
      expect(zoneLabel(2)).toBe("Outer");
      expect(zoneLabel(3)).toBe("Belt");
      expect(zoneLabel(99)).toBe("Unknown");
    });
  });

  describe("zoneEmoji", () => {
    it("returns emoji for each zone", () => {
      expect(zoneEmoji(0)).toBeTruthy();
      expect(zoneEmoji(1)).toBeTruthy();
      expect(zoneEmoji(2)).toBeTruthy();
      expect(zoneEmoji(3)).toBeTruthy();
    });
  });

  describe("debounce", () => {
    it("debounces function calls", async () => {
      let count = 0;
      const fn = debounce(() => count++, 50);

      fn();
      fn();
      fn();

      expect(count).toBe(0);
      await new Promise((r) => setTimeout(r, 100));
      expect(count).toBe(1);
    });
  });
});
