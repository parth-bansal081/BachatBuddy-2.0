interface TabItem {
  id: string;
  label: string;
}

interface TabBarProps {
  items: readonly TabItem[];
  activeId: string;
  onSelect: (id: string) => void;
}

export function TabBar({ items, activeId, onSelect }: TabBarProps) {
  return (
    <div className="border-t-2 border-khata-ink flex gap-1 pt-2">
      {items.map((item) => (
        <button
          key={item.id}
          onClick={() => onSelect(item.id)}
          className={`font-num text-sm px-3 py-2 border-b-3 transition-colors ${
            item.id === activeId
              ? "text-khata-vermilion border-khata-vermilion"
              : "text-khata-muted hover:text-khata-ink border-transparent"
          }`}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}