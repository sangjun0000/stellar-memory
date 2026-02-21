import type { QueuedAction } from "../types";

const QUEUE_KEY = "stellar_offline_queue";
const MAX_RETRIES = 3;

export class OfflineQueue {
  async push(item: Omit<QueuedAction, "id" | "timestamp" | "retries">): Promise<void> {
    const queue = await this.getAll();
    queue.push({
      ...item,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      retries: 0,
    });
    await chrome.storage.local.set({ [QUEUE_KEY]: queue });
  }

  async getAll(): Promise<QueuedAction[]> {
    const result = await chrome.storage.local.get(QUEUE_KEY);
    return (result[QUEUE_KEY] as QueuedAction[]) || [];
  }

  async flush(handler: (item: QueuedAction) => Promise<void>): Promise<number> {
    const queue = await this.getAll();
    if (queue.length === 0) return 0;

    const remaining: QueuedAction[] = [];
    let processed = 0;

    for (const item of queue) {
      try {
        await handler(item);
        processed++;
      } catch {
        if (item.retries < MAX_RETRIES) {
          remaining.push({ ...item, retries: item.retries + 1 });
        }
        // Drop items exceeding MAX_RETRIES
      }
    }

    await chrome.storage.local.set({ [QUEUE_KEY]: remaining });
    return processed;
  }

  async clear(): Promise<void> {
    await chrome.storage.local.set({ [QUEUE_KEY]: [] });
  }

  async size(): Promise<number> {
    const queue = await this.getAll();
    return queue.length;
  }
}
