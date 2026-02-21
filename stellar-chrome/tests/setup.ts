import { vi } from "vitest";

// Mock chrome API
const storedData: Record<string, unknown> = {};
const listeners: Array<(changes: unknown, area: string) => void> = [];

const chromeMock = {
  runtime: {
    sendMessage: vi.fn((_msg: unknown, callback?: (res: unknown) => void) => {
      callback?.({});
    }),
    onMessage: {
      addListener: vi.fn(),
      removeListener: vi.fn(),
    },
    onInstalled: {
      addListener: vi.fn(),
    },
    lastError: null as chrome.runtime.LastError | null,
  },
  storage: {
    local: {
      get: vi.fn((keys: string | string[]) => {
        if (typeof keys === "string") {
          return Promise.resolve({ [keys]: storedData[keys] });
        }
        const result: Record<string, unknown> = {};
        for (const k of keys) result[k] = storedData[k];
        return Promise.resolve(result);
      }),
      set: vi.fn((items: Record<string, unknown>) => {
        Object.assign(storedData, items);
        return Promise.resolve();
      }),
    },
    onChanged: {
      addListener: vi.fn((fn: (changes: unknown, area: string) => void) => {
        listeners.push(fn);
      }),
    },
  },
  sidePanel: {
    setPanelBehavior: vi.fn(),
  },
  tabs: {
    onActivated: {
      addListener: vi.fn(),
    },
  },
};

// @ts-expect-error Mock chrome global
globalThis.chrome = chromeMock;
