import { useState } from "react";
import { useOptionalAccount } from "@/features/account/account-provider";
import { toast } from "sonner";
import { Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "./theme-provider";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function ThemeMenu() {
  const { theme, setTheme } = useTheme();
  const account = useOptionalAccount();
  const [saving, setSaving] = useState(false);
  const Icon = theme === "system" ? Monitor : theme === "dark" ? Moon : Sun;
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Choose theme" disabled={saving || (account?.signedIn && !account.account)}>
          <Icon aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuRadioGroup
          value={theme}
          onValueChange={async (value) => {
            if (value !== "light" && value !== "dark" && value !== "system") return;
            if (!account?.account) { setTheme(value); return; }
            setSaving(true);
            try { await account.save({ version: account.account.version, preferences: { theme: value } }); }
            catch (cause) { toast.error(cause instanceof Error ? cause.message : "Unable to save theme."); await account.reload().catch(() => undefined); }
            finally { setSaving(false); }
          }}
        >
          <DropdownMenuRadioItem value="light">Light</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="dark">Dark</DropdownMenuRadioItem>
          <DropdownMenuRadioItem value="system">System</DropdownMenuRadioItem>
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
