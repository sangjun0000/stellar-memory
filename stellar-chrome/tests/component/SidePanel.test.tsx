import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { SidePanel } from "../../src/sidepanel/SidePanel";

beforeEach(() => {
  const mockMemories = [
    { id: "m1", content: "커피를 좋아함", zone: 0, importance: 0.8, source: "chatgpt", createdAt: "2026-02-19T10:00:00Z" },
    { id: "m2", content: "React 개발자", zone: 1, importance: 0.6, source: "claude", createdAt: "2026-02-15T10:00:00Z" },
  ];

  const mockSettings = {
    enabled: true,
    sites: { chatgpt: true, claude: true, gemini: true },
    injection: { mode: "auto" as const, maxMemories: 5, minImportance: 0.3 },
    api: { baseUrl: "http://localhost:9000", connected: true },
    stats: { totalStored: 42, lastSync: "2026-01-01T00:00:00Z" },
  };

  vi.mocked(chrome.runtime.sendMessage).mockImplementation(
    (msg: unknown, callback?: (res: unknown) => void) => {
      const m = msg as { type: string };
      if (m.type === "RECALL") callback?.({ memories: mockMemories });
      else if (m.type === "GET_SETTINGS") callback?.(mockSettings);
      else if (m.type === "UPDATE_SETTINGS") callback?.(mockSettings);
      else callback?.({});
    },
  );
});

describe("SidePanel", () => {
  it("renders header", async () => {
    render(<SidePanel />);
    await waitFor(() => {
      expect(screen.getByText(/이 대화와 관련된 기억/)).toBeTruthy();
    });
  });

  it("shows memory cards", async () => {
    render(<SidePanel />);
    await waitFor(() => {
      expect(screen.getByText(/커피를 좋아함/)).toBeTruthy();
      expect(screen.getByText(/React 개발자/)).toBeTruthy();
    });
  });

  it("shows injection status text", async () => {
    render(<SidePanel />);
    await waitFor(() => {
      expect(screen.getByText(/기억이 자동 주입됩니다/)).toBeTruthy();
    });
  });

  it("has injection toggle button", async () => {
    render(<SidePanel />);
    await waitFor(() => {
      expect(screen.getByText("[주입 끄기]")).toBeTruthy();
    });
  });

  it("displays source info on memory cards", async () => {
    render(<SidePanel />);
    await waitFor(() => {
      expect(screen.getByText("chatgpt")).toBeTruthy();
      expect(screen.getByText("claude")).toBeTruthy();
    });
  });

  it("shows empty state when no memories", async () => {
    vi.mocked(chrome.runtime.sendMessage).mockImplementation(
      (msg: unknown, callback?: (res: unknown) => void) => {
        const m = msg as { type: string };
        if (m.type === "RECALL") callback?.({ memories: [] });
        else callback?.({});
      },
    );

    render(<SidePanel />);
    await waitFor(() => {
      expect(screen.getByText("관련 기억이 없습니다")).toBeTruthy();
    });
  });
});
