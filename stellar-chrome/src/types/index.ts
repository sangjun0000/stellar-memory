// ─── Chrome Storage Settings ───

export interface StellarSettings {
  enabled: boolean;
  sites: {
    chatgpt: boolean;
    claude: boolean;
    gemini: boolean;
  };
  injection: {
    mode: "auto" | "manual";
    maxMemories: number;
    minImportance: number;
  };
  api: {
    baseUrl: string;
    connected: boolean;
  };
  stats: {
    totalStored: number;
    lastSync: string;
  };
}

export const DEFAULT_SETTINGS: StellarSettings = {
  enabled: true,
  sites: { chatgpt: true, claude: true, gemini: true },
  injection: { mode: "auto", maxMemories: 5, minImportance: 0.3 },
  api: { baseUrl: "http://localhost:9000", connected: false },
  stats: { totalStored: 0, lastSync: "" },
};

// ─── Site Types ───

export type SiteName = "chatgpt" | "claude" | "gemini";

// ─── Content Script ↔ Background Message Protocol ───

export type CSMessage =
  | { type: "STORE"; payload: StorePayload }
  | { type: "RECALL"; payload: RecallPayload }
  | { type: "FORGET"; payload: { memoryId: string } }
  | { type: "GET_SETTINGS" }
  | { type: "UPDATE_SETTINGS"; payload: Partial<StellarSettings> }
  | { type: "GET_STATS" }
  | { type: "CHECK_CONNECTION" };

export interface StorePayload {
  content: string;
  importance: number;
  metadata: {
    source: SiteName;
    url: string;
    role: "user" | "assistant";
    conversationId?: string;
    timestamp: number;
  };
}

export interface RecallPayload {
  query: string;
  limit: number;
  source?: SiteName;
}

// ─── API Responses ───

export interface MemoryRecord {
  id: string;
  content: string;
  zone: number;
  importance: number;
  source: string;
  createdAt: string;
}

export interface RecallResponse {
  memories: MemoryRecord[];
}

export interface StoreResult {
  id: string | null;
  error?: string;
  queued?: boolean;
}

export interface StatsResponse {
  total_memories: number;
  zones: Record<string, number>;
}

// ─── Site Selectors ───

export interface SiteSelectors {
  messageContainer: string;
  userMessage: string;
  assistantMessage: string;
  messageText: string;
  inputArea: string;
  submitButton: string;
  formElement: string;
}

// ─── Extracted Message ───

export interface ExtractedMessage {
  role: "user" | "assistant";
  content: string;
}

// ─── Offline Queue ───

export interface QueuedAction {
  id: string;
  action: "store" | "forget";
  payload: unknown;
  timestamp: number;
  retries: number;
}
