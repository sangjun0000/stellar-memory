interface Props {
  connected: boolean;
  totalMemories: number;
}

export function StatusBar({ connected, totalMemories }: Props) {
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-gray-50 text-xs text-gray-600">
      <span className="flex items-center gap-1">
        <span
          className={`w-2 h-2 rounded-full ${connected ? "bg-green-500" : "bg-red-400"}`}
        />
        {connected ? "서버 연결됨" : "서버 미연결"}
      </span>
      <span>{totalMemories}개 기억</span>
    </div>
  );
}
