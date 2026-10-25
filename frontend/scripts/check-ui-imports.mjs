import assert from "node:assert/strict";
const required = {
  "@tanstack/react-table": "useTable",
  "@svar-ui/react-gantt": "Gantt",
  "@dnd-kit/react": "DragDropProvider",
  recharts: "BarChart",
  "react-hook-form": "useForm",
  zod: "z",
  "@hookform/resolvers/zod": "zodResolver",
};
for (const [name, exported] of Object.entries(required)) {
  const library = await import(name);
  assert.ok(library[exported], `${name} must export ${exported}`);
  console.log(`PASS ${name}: ${exported}`);
}
const { z } = await import("zod");
const { zodResolver } = await import("@hookform/resolvers/zod");
const resolver = zodResolver(z.object({ label: z.string().min(1) }));
const result = await resolver({ label: "" }, undefined, {
  fields: {},
  shouldUseNativeValidation: false,
});
assert.ok(result.errors.label, "Zod resolver must reject empty labels");
console.log("PASS React Hook Form / Zod resolver integration");
