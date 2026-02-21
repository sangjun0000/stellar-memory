import { describe, it, expect, vi, beforeEach } from "vitest";
import { ApiClient } from "../../src/lib/api-client";

describe("ApiClient", () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient("http://localhost:9000");
    vi.restoreAllMocks();
  });

  describe("checkHealth", () => {
    it("returns true when server is reachable", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("ok", { status: 200 }),
      );
      expect(await client.checkHealth()).toBe(true);
    });

    it("returns false when server is unreachable", async () => {
      vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("timeout"));
      expect(await client.checkHealth()).toBe(false);
    });
  });

  describe("store", () => {
    it("sends POST to /api/v1/store", async () => {
      const mockFetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ id: "mem-1" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );

      const result = await client.store({
        content: "test memory",
        importance: 0.8,
        metadata: {
          source: "chatgpt",
          url: "https://chatgpt.com",
          role: "user",
          timestamp: Date.now(),
        },
      });

      expect(result.id).toBe("mem-1");
      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:9000/api/v1/store",
        expect.objectContaining({ method: "POST" }),
      );
    });

    it("queues when offline", async () => {
      vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("offline"));

      const result = await client.store({
        content: "test",
        importance: 0.5,
        metadata: {
          source: "chatgpt",
          url: "https://chatgpt.com",
          role: "user",
          timestamp: Date.now(),
        },
      });

      expect(result.id).toBeNull();
      expect(result.queued).toBe(true);
    });
  });

  describe("recall", () => {
    it("sends GET to /api/v1/recall", async () => {
      const memories = [
        { id: "m1", content: "test", zone: 0, importance: 0.8, source: "chatgpt", createdAt: "2026-01-01" },
      ];
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ memories }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );

      const result = await client.recall({ query: "test", limit: 5 });
      expect(result.memories).toHaveLength(1);
      expect(result.memories[0].content).toBe("test");
    });

    it("returns empty on failure", async () => {
      vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("offline"));
      const result = await client.recall({ query: "test", limit: 5 });
      expect(result.memories).toHaveLength(0);
    });
  });

  describe("forget", () => {
    it("sends DELETE to /api/v1/forget/:id", async () => {
      const mockFetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ removed: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );

      const result = await client.forget("mem-123");
      expect(result.removed).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:9000/api/v1/forget/mem-123",
        expect.objectContaining({ method: "DELETE" }),
      );
    });
  });

  describe("getStats", () => {
    it("returns stats on success", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response(JSON.stringify({ total_memories: 42, zones: { "0": 5 } }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );

      const result = await client.getStats();
      expect(result.total_memories).toBe(42);
    });

    it("returns defaults on failure", async () => {
      vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("offline"));
      const result = await client.getStats();
      expect(result.total_memories).toBe(0);
    });
  });
});
