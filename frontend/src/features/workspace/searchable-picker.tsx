import { useEffect, useState } from "react";
import { ChevronsUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Pagination, ReadError, useWorkspaceRead } from "./components";

export type Choice = { id: string; label: string };
export type ChoicePage = { count: number; results: Choice[]; next: string | null; previous: string | null };
export type ChoiceLoader = (search: string, page: number, signal: AbortSignal) => Promise<ChoicePage>;

function Choices({ load, query, page, setPage, select }: { load: ChoiceLoader; query: string; page: number; setPage: (page: number) => void; select: (choice: Choice) => void }) {
  const read = useWorkspaceRead(signal => load(query, page, signal));
  if (read.error) return <ReadError message={read.error} retry={read.refresh} />;
  if (!read.data) return <p role="status" className="p-3">Loading choices…</p>;
  return <><CommandList>{read.data.results.map(choice => <CommandItem key={choice.id} value={choice.id} onSelect={() => select(choice)}>{choice.label}</CommandItem>)}{!read.data.count && <p className="p-3 text-sm">No eligible choices. Check organization, status and permissions.</p>}</CommandList><Pagination {...read.data} page={page} change={setPage} /></>;
}

export function SearchablePicker({ label, value, onChange, load, optional = false }: { label: string; value: Choice | null; onChange: (choice: Choice | null) => void; load: ChoiceLoader; optional?: boolean }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  useEffect(() => {
    const timer = window.setTimeout(() => { setQuery(search.trim()); setPage(1); }, 250);
    return () => window.clearTimeout(timer);
  }, [search]);
  return <fieldset className="min-w-0 space-y-2"><legend className="text-sm font-medium">{label}</legend><div className="flex gap-2"><Popover open={open} onOpenChange={setOpen}><PopoverTrigger asChild><Button type="button" variant="outline" aria-label={`Choose ${label.toLowerCase()}`} aria-expanded={open} className="max-w-full justify-between"><span className="truncate">{value?.label || `Choose ${label.toLowerCase()}`}</span><ChevronsUpDown className="size-4 shrink-0" aria-hidden /></Button></PopoverTrigger><PopoverContent aria-label={`${label} choices`} align="start" className="w-[min(26rem,calc(100vw-2rem))]"><Command label={`Search ${label.toLowerCase()}`} shouldFilter={false}><CommandInput aria-label={`Search ${label.toLowerCase()}`} placeholder="Search name or username…" value={search} onValueChange={setSearch} maxLength={100} /><Choices key={`${query}:${page}`} query={query} page={page} setPage={setPage} load={load} select={choice => { onChange(choice); setOpen(false); }} /></Command></PopoverContent></Popover>{optional && <Button type="button" variant="ghost" onClick={() => onChange(null)}>Clear</Button>}</div></fieldset>;
}
