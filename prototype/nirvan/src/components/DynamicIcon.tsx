import * as Icons from "lucide-react";
import type { LucideProps } from "lucide-react";

export default function DynamicIcon({ name, ...props }: { name: string } & LucideProps) {
  const Cmp = (Icons as unknown as Record<string, React.ComponentType<LucideProps>>)[name] || Icons.Circle;
  return <Cmp {...props} />;
}
