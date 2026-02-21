import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Popup } from "../../src/popup/Popup";

// Mock chrome.runtime.sendMessage with proper responses
beforeEach(() => {
  const mockSettings = {
    enabled: true,
    sites: { chatgpt: true, claude: true, gemini: false },
    injection: { mode: "auto" as const, maxMemories: 5, minImportance: 0.3 },
    api: { baseUrl: "http://localhost:9000", connected: true },
    stats: { totalStored: 42, lastSync: "2026-01-01T00:00:00Z" },
  };

  const mockMemories = [
    { id: "m1", content: "커피를 좋아함", zone: 0, importance: 0.8, source: "chatgpt", createdAt: "2026-02-19T10:00:00Z" },
    { id: "m2", content: "React 개발자", zone: 1, importance: 0.6, source: "claude", createdAt: "2026-02-15T10:00:00Z" },
  ];

  const mockStats = { total_memories: 42, zones: { "0": 5, "1": 23 } };

  vi.mocked(chrome.runtime.sendMessage).mockImplementation(
    (msg: unknown, callback?: (res: unknown) => void) => {
      const m = msg as { type: string };
      if (m.type === "GET_SETTINGS") callback?.(mockSettings);
      else if (m.type === "RECALL") callback?.({ memories: mockMemories });
      else if (m.type === "GET_STATS") callback?.(mockStats);
      else if (m.type === "UPDATE_SETTINGS") callback?.(mockSettings);
      else if (m.type === "FORGET") callback?.({ removed: true });
      else callback?.({});
    },
  );
});

describe("Popup", () => {
  it("renders header with Stellar Memory title", async () => {
    render(<Popup />);
    await waitFor(() => {
      expect(screen.getByText("Stellar Memory")).toBeTruthy();
    });
  });

  it("shows ON/OFF toggle button", async () => {
    render(<Popup />);
    await waitFor(() => {
      expect(screen.getByText("ON")).toBeTruthy();
    });
  });

  it("shows server connection status", async () => {
    render(<Popup />);
    await waitFor(() => {
      expect(screen.getByText(/서버 연결됨/)).toBeTruthy();
    });
  });

  it("shows memory count", async () => {
    render(<Popup />);
    await waitFor(() => {
      expect(screen.getByText(/42개 기억/)).toBeTruthy();
    });
  });

  it("renders memory list with items", async () => {
    render(<Popup />);
    await waitFor(() => {
      expect(screen.getByText(/커피를 좋아함/)).toBeTruthy();
      expect(screen.getByText(/React 개발자/)).toBeTruthy();
    });
  });

  it("renders site toggles", async () => {
    render(<Popup />);
    await waitFor(() => {
      expect(screen.getByText("ChatGPT")).toBeTruthy();
      expect(screen.getByText("Claude")).toBeTruthy();
      expect(screen.getByText("Gemini")).toBeTruthy();
    });
  });

  it("renders injection mode radio buttons", async () => {
    render(<Popup />);
    await waitFor(() => {
      expect(screen.getByText("자동")).toBeTruthy();
      expect(screen.getByText("수동")).toBeTruthy();
    });
  });

  it("has a search input", async () => {
    render(<Popup />);
    await waitFor(() => {
      const input = screen.getByPlaceholderText(/기억 검색/);
      expect(input).toBeTruthy();
    });
  });

  it("sends FORGET message when delete is clicked", async () => {
    render(<Popup />);
    await waitFor(() => {
      expect(screen.getByText(/커피를 좋아함/)).toBeTruthy();
    });

    const deleteButtons = screen.getAllByTitle("삭제");
    fireEvent.click(deleteButtons[0]);

    expect(chrome.runtime.sendMessage).toHaveBeenCalledWith(
      { type: "FORGET", payload: { memoryId: "m1" } },
      expect.any(Function),
    );
  });
});
