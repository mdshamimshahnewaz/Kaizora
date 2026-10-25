import { useState, type ReactNode } from "react";
import {
  ArrowUpRight,
  Check,
  ChevronDown,
  CircleHelp,
  Layers,
  Monitor,
  Moon,
  Plus,
  Search,
  Sun,
} from "lucide-react";
import { toast } from "sonner";
import { ThemeProvider, useTheme } from "@/components/theme/theme-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { TooltipProvider } from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
  TableCaption,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from "@/components/ui/command";
import { Toaster } from "@/components/ui/sonner";
import { IconButton } from "@/components/ui/icon-button";
import { DatePicker } from "@/components/ui/date-picker";

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">{children}</CardContent>
    </Card>
  );
}

function ShowcaseContent() {
  const { theme, setTheme } = useTheme();
  const [date, setDate] = useState<Date>();
  return (
    <div className="min-h-screen">
      <header className="border-b bg-card">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <a
            href="/__ui"
            className="flex items-center gap-3 font-semibold tracking-tight"
          >
            <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Layers size={18} aria-hidden="true" />
            </span>
            Kaizora{" "}
            <span className="font-normal text-muted-foreground">
              / UI library
            </span>
          </a>
          <div className="flex items-center gap-3">
            <Badge variant="outline">Development only</Badge>
            <div
              role="group"
              aria-label="Color theme"
              className="flex gap-1 rounded-lg border p-1"
            >
              {(
                [
                  { value: "light", Icon: Sun },
                  { value: "dark", Icon: Moon },
                  { value: "system", Icon: Monitor },
                ] as const
              ).map(({ value, Icon }) => (
                <IconButton
                  key={value}
                  label={`${value[0].toUpperCase()}${value.slice(1)} theme`}
                  variant={theme === value ? "secondary" : "ghost"}
                  aria-pressed={theme === value}
                  onClick={() => setTheme(value)}
                >
                  <Icon aria-hidden="true" />
                </IconButton>
              ))}
            </div>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl space-y-8 px-6 py-10">
        <section className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="mb-3 text-xs font-semibold tracking-widest text-teal-foreground">
              DESIGN FOUNDATION · 01
            </p>
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              Clarity, in every detail.
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-muted-foreground">
              A shared visual language for Kaizora. Explore the colors, controls
              and interaction patterns that future screens will use.
            </p>
          </div>
          <Button variant="outline" asChild>
            <a href="/">
              Open application
              <ArrowUpRight aria-hidden="true" />
            </a>
          </Button>
        </section>
        <section
          aria-label="Theme colors"
          className="grid grid-cols-2 gap-3 sm:grid-cols-4"
        >
          {[
            { name: "Indigo", role: "Primary actions", color: "bg-primary" },
            { name: "Navy", role: "Structure & depth", color: "bg-navy" },
            { name: "Teal", role: "Supporting accent", color: "bg-teal" },
            {
              name: "Slate",
              role: "Quiet surfaces",
              color: "bg-muted-foreground",
            },
          ].map((item) => (
            <div
              key={item.name}
              className="flex items-center gap-3 rounded-lg border bg-card p-4"
            >
              <span className={`size-9 shrink-0 rounded-md ${item.color}`} />
              <div>
                <p className="text-sm font-medium">{item.name}</p>
                <p className="text-xs text-muted-foreground">{item.role}</p>
              </div>
            </div>
          ))}
        </section>
        <div className="grid gap-6 lg:grid-cols-2">
          <Section
            title="Actions & feedback"
            description="Clear hierarchy. Consistent focus and disabled states."
          >
            <div className="flex flex-wrap gap-2">
              <Button>
                <Plus aria-hidden="true" />
                Primary action
              </Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Quiet</Button>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button disabled>Unavailable</Button>
              <Button variant="destructive">Destructive</Button>
              <IconButton label="Component information" variant="outline">
                <CircleHelp aria-hidden="true" />
              </IconButton>
              <Button
                variant="link"
                onClick={() =>
                  toast.success("Example notification", {
                    description: "Your visual preview is ready.",
                  })
                }
              >
                Show notification
              </Button>
            </div>
            <Separator />
            <div className="flex flex-wrap gap-2">
              {[
                { label: "Success", color: "text-success bg-success/10" },
                { label: "Warning", color: "text-warning bg-warning/10" },
                { label: "Error", color: "text-destructive bg-destructive/10" },
                {
                  label: "Information",
                  color: "text-information bg-information/10",
                },
              ].map((status) => (
                <Badge
                  key={status.label}
                  variant="outline"
                  className={status.color}
                >
                  {status.label}
                </Badge>
              ))}
            </div>
            <Alert>
              <Check aria-hidden="true" />
              <AlertTitle>Ready to reuse</AlertTitle>
              <AlertDescription>
                Semantic tokens keep both themes consistent.
              </AlertDescription>
            </Alert>
          </Section>
          <Section
            title="Inputs & selection"
            description="Reusable controls with explicit, accessible labels."
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="sample-name">Example label</Label>
                <Input id="sample-name" placeholder="Enter a value" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sample-select">Density</Label>
                <Select defaultValue="comfortable">
                  <SelectTrigger id="sample-select" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="comfortable">Comfortable</SelectItem>
                    <SelectItem value="compact">Compact</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="sample-notes">Supporting text</Label>
              <Textarea
                id="sample-notes"
                placeholder="A short, helpful description…"
              />
            </div>
            <div className="flex flex-wrap items-center gap-6">
              <div className="flex items-center gap-2">
                <Checkbox id="sample-check" defaultChecked />
                <Label htmlFor="sample-check">Include details</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch id="sample-switch" defaultChecked />
                <Label htmlFor="sample-switch">Notifications</Label>
              </div>
            </div>
            <RadioGroup
              defaultValue="standard"
              aria-label="Example layout"
              className="flex gap-5"
            >
              <div className="flex items-center gap-2">
                <RadioGroupItem id="standard" value="standard" />
                <Label htmlFor="standard">Standard</Label>
              </div>
              <div className="flex items-center gap-2">
                <RadioGroupItem id="compact" value="compact" />
                <Label htmlFor="compact">Compact</Label>
              </div>
            </RadioGroup>
            <div className="space-y-2">
              <Label htmlFor="sample-date">Example date</Label>
              <DatePicker
                id="sample-date"
                label="Example date"
                value={date}
                onChange={setDate}
              />
            </div>
          </Section>
          <Section
            title="Layers & navigation"
            description="Menus, dialogs and panels share the same visual language."
          >
            <div className="flex flex-wrap gap-2">
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="outline">Open dialog</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>A focused conversation</DialogTitle>
                    <DialogDescription>
                      This is a reusable dialog preview. Press Escape or close
                      to return.
                    </DialogDescription>
                  </DialogHeader>
                  <DialogFooter>
                    <DialogClose asChild>
                      <Button>Done</Button>
                    </DialogClose>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline">
                    Options
                    <ChevronDown aria-hidden="true" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                  <DropdownMenuLabel>Example actions</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onSelect={() => toast("Preview action selected")}
                  >
                    Preview action
                  </DropdownMenuItem>
                  <DropdownMenuItem disabled>
                    Unavailable action
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline">Open sheet</Button>
                </SheetTrigger>
                <SheetContent>
                  <SheetHeader>
                    <SheetTitle>Supporting panel</SheetTitle>
                    <SheetDescription>
                      Use this primitive for contextual content on future
                      screens.
                    </SheetDescription>
                  </SheetHeader>
                </SheetContent>
              </Sheet>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline">Confirmation</Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Confirm example?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This preview does not change any application data.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={() => toast.success("Example confirmed")}
                    >
                      Confirm
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
            <Tabs defaultValue="type">
              <TabsList aria-label="Preview content">
                <TabsTrigger value="type">Typography</TabsTrigger>
                <TabsTrigger value="loading">Loading states</TabsTrigger>
              </TabsList>
              <TabsContent value="type" className="space-y-3 pt-3">
                <h2 className="text-2xl font-semibold tracking-tight">
                  Designed for everyday work.
                </h2>
                <p className="text-sm leading-6 text-muted-foreground">
                  Geist, served locally. A compact scale with comfortable
                  reading space and restrained emphasis.
                </p>
                <p className="text-xs font-medium tracking-wide text-teal-foreground">
                  CAPTION / 12 PX
                </p>
              </TabsContent>
              <TabsContent value="loading" className="space-y-4 pt-3">
                <div
                  role="status"
                  aria-label="Loading example"
                  className="flex gap-3"
                >
                  <Skeleton className="size-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-2/3" />
                    <Skeleton className="h-4 w-1/2" />
                  </div>
                </div>
                <Progress value={60} aria-label="Example progress" />
              </TabsContent>
            </Tabs>
          </Section>
          <Section
            title="Lists & discovery"
            description="Simple table and command primitives. Placeholder content only."
          >
            <Table>
              <TableCaption>Example component inventory</TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead>Component</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">State</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {["Button", "Input", "Dialog"].map((name) => (
                  <TableRow key={name}>
                    <TableCell className="font-medium">{name}</TableCell>
                    <TableCell className="text-muted-foreground">
                      Foundation
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant="secondary">Available</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Command className="rounded-lg border">
              <CommandInput
                aria-label="Find a sample component"
                placeholder="Find a sample component…"
              />
              <CommandList>
                <CommandEmpty>No matching components.</CommandEmpty>
                <CommandGroup heading="Components">
                  <CommandItem onSelect={() => toast("Button selected")}>
                    <Search aria-hidden="true" />
                    Button
                  </CommandItem>
                  <CommandItem onSelect={() => toast("Dialog selected")}>
                    <Layers aria-hidden="true" />
                    Dialog
                  </CommandItem>
                </CommandGroup>
              </CommandList>
            </Command>
          </Section>
        </div>
        <section className="flex flex-wrap items-center justify-between gap-4 rounded-lg border bg-card p-5">
          <div className="flex items-center gap-3">
            <Avatar>
              <AvatarFallback>UI</AvatarFallback>
            </Avatar>
            <div>
              <p className="text-sm font-medium">One consistent foundation</p>
              <p className="text-xs text-muted-foreground">
                shadcn/ui · Tailwind CSS · Lucide
              </p>
            </div>
          </div>
          <ScrollArea className="h-12 w-64 rounded-md border px-3 py-2">
            <p className="text-xs leading-6 text-muted-foreground">
              Shared tokens · Accessible primitives
              <br />
              Light and dark themes
              <br />
              Reusable interaction patterns
            </p>
          </ScrollArea>
        </section>
        <footer className="text-xs text-muted-foreground">
          UI foundation preview · No application data or API connections
        </footer>
      </main>
      <Toaster />
    </div>
  );
}

export default function UIShowcase() {
  return (
    <ThemeProvider>
      <TooltipProvider>
        <ShowcaseContent />
      </TooltipProvider>
    </ThemeProvider>
  );
}
