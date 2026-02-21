import type {
  StorePayload,
  StoreResult,
  RecallPayload,
  RecallResponse,
  StatsResponse,
} from "../types";
import { OfflineQueue } from "./offline-queue";

const MAX_STORE_PER_SEC = 2;
const BACKOFF_BASE_MS = 1000;
const MAX_BACKOFF_RETRIES = 3;

export class ApiClient {
  private baseUrl: string;
  private queue: OfflineQueue;
  private storeTimestamps: number[] = [];

  constructor(baseUrl = "http://localhost:9000") {
    this.baseUrl = baseUrl;
    this.queue = new OfflineQueue();
  }

  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/health`, {
        signal: AbortSignal.timeout(3000),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  private isRateLimited(): boolean {
    const now = Date.now();
    this.storeTimestamps = this.storeTimestamps.filter((t) => now - t < 1000);
    return this.storeTimestamps.length >= MAX_STORE_PER_SEC;
  }

  private recordStoreCall(): void {
    this.storeTimestamps.push(Date.now());
  }

  private async fetchWithBackoff(
    url: string,
    init?: RequestInit,
  ): Promise<Response> {
    let lastError: Error | null = null;
    for (let attempt = 0; attempt <= MAX_BACKOFF_RETRIES; attempt++) {
      const res = await fetch(url, init);
      if (res.status === 429) {
        lastError = new Error("Rate limited (429)");
        const delay = BACKOFF_BASE_MS * Math.pow(2, attempt);
        await new Promise((r) => setTimeout(r, delay));
        continue;
      }
      return res;
    }
    throw lastError ?? new Error("Max retries exceeded");
  }

  async store(payload: StorePayload): Promise<StoreResult> {
    // Client-side rate limit: max 2 store/sec
    if (this.isRateLimited()) {
      await this.queue.push({ action: "store", payload });
      return { id: null, error: "rate_limited", queued: true };
    }

    try {
      this.recordStoreCall();
      const res = await this.fetchWithBackoff(`${this.baseUrl}/api/v1/store`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: payload.content,
          importance: payload.importance,
          metadata: payload.metadata,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch {
      await this.queue.push({
        action: "store",
        payload,
      });
      return { id: null, error: "offline", queued: true };
    }
  }

  async recall(payload: RecallPayload): Promise<RecallResponse> {
    try {
      const params = new URLSearchParams({
        q: payload.query,
        limit: String(payload.limit),
      });
      const res = await this.fetchWithBackoff(
        `${this.baseUrl}/api/v1/recall?${params}`,
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch {
      return { memories: [] };
    }
  }

  async forget(memoryId: string): Promise<{ removed: boolean }> {
    try {
      const res = await this.fetchWithBackoff(
        `${this.baseUrl}/api/v1/forget/${memoryId}`,
        { method: "DELETE" },
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch {
      await this.queue.push({
        action: "forget",
        payload: { memoryId },
      });
      return { removed: false };
    }
  }

  async getStats(): Promise<StatsResponse> {
    try {
      const res = await this.fetchWithBackoff(`${this.baseUrl}/api/v1/stats`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch {
      return { total_memories: 0, zones: {} };
    }
  }

  async flushQueue(): Promise<number> {
    return this.queue.flush(async (item) => {
      if (item.action === "store") {
        await this.store(item.payload as StorePayload);
      } else if (item.action === "forget") {
        const p = item.payload as { memoryId: string };
        await this.forget(p.memoryId);
      }
    });
  }
}
