import type { MemoryRecord } from "../types";
import { MemoryItem } from "./MemoryItem";
import { zoneEmoji, zoneLabel } from "../lib/utils";

interface Props {
  memories: MemoryRecord[];
  onDelete: (id: string) => void;
}

export function MemoryList({ memories, onDelete }: Props) {
  if (memories.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-400">
        <span className="text-3xl mb-2">&#128173;</span>
        <p className="text-sm">아직 기억이 없습니다</p>
        <p className="text-xs mt-1">AI와 대화하면 자동으로 기억됩니다</p>
      </div>
    );
  }

  // Group by zone
  const grouped = memories.reduce(
    (acc, m) => {
      const zone = m.zone ?? 0;
      if (!acc[zone]) acc[zone] = [];
      acc[zone].push(m);
      return acc;
    },
    {} as Record<number, MemoryRecord[]>,
  );

  const sortedZones = Object.keys(grouped)
    .map(Number)
    .sort((a, b) => a - b);

  return (
    <div className="px-2 py-1">
      {sortedZones.map((zone) => (
        <div key={zone} className="mb-2">
          <div className="flex items-center gap-1 px-2 py-1 text-xs font-semibold text-gray-500 uppercase">
            <span>{zoneEmoji(zone)}</span>
            <span>{zoneLabel(zone)}</span>
            <span className="text-gray-400">({grouped[zone].length})</span>
          </div>
          {grouped[zone].map((m) => (
            <MemoryItem key={m.id} memory={m} onDelete={onDelete} />
          ))}
        </div>
      ))}
    </div>
  );
}
