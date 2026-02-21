import type { MemoryRecord } from "../types";
import { zoneEmoji, zoneLabel, getRelativeTime } from "../lib/utils";

interface Props {
  memory: MemoryRecord;
}

export function MemoryCard({ memory }: Props) {
  const importancePercent = Math.round(memory.importance * 100);

  return (
    <div className="border border-gray-200 rounded-lg p-3 mb-2">
      <div className="flex items-center gap-1 mb-1">
        <span>{zoneEmoji(memory.zone)}</span>
        <span className="text-sm font-medium text-gray-800">
          {memory.content.length > 60
            ? memory.content.slice(0, 60) + "..."
            : memory.content}
        </span>
      </div>
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <span>{getRelativeTime(memory.createdAt)}</span>
        <span>&middot;</span>
        <span>{memory.source}</span>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <span className="text-xs text-gray-400">
          {zoneLabel(memory.zone)}
        </span>
        <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-stellar-400 rounded-full"
            style={{ width: `${importancePercent}%` }}
          />
        </div>
        <span className="text-xs text-gray-400">{memory.importance.toFixed(1)}</span>
      </div>
    </div>
  );
}
