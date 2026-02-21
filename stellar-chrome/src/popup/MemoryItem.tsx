import type { MemoryRecord } from "../types";
import { zoneEmoji, zoneLabel, getRelativeTime, truncate } from "../lib/utils";

interface Props {
  memory: MemoryRecord;
  onDelete: (id: string) => void;
}

export function MemoryItem({ memory, onDelete }: Props) {
  return (
    <div className="flex items-start justify-between gap-2 py-2 px-3 hover:bg-gray-50 rounded-lg group">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1 text-xs text-gray-500 mb-0.5">
          <span>{zoneEmoji(memory.zone)}</span>
          <span className="font-medium">{zoneLabel(memory.zone)}</span>
          <span className="mx-1">&middot;</span>
          <span>{getRelativeTime(memory.createdAt)}</span>
        </div>
        <p className="text-sm text-gray-800 truncate">
          {truncate(memory.content, 80)}
        </p>
      </div>
      <button
        onClick={() => onDelete(memory.id)}
        className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity p-1"
        title="삭제"
      >
        &#128465;&#65039;
      </button>
    </div>
  );
}
