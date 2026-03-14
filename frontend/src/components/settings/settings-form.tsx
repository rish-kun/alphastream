"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function SettingsForm() {
  const { data: session, update: updateSession } = useSession();
  const [fullName, setFullName] = useState(session?.user?.name || "");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage(null);

    try {
      const response = await fetch("/api/v1/auth/me", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ full_name: fullName }),
      });

      if (!response.ok) {
        throw new Error("Failed to update profile");
      }

      await updateSession();
      setMessage({ type: "success", text: "Profile updated successfully!" });
    } catch {
      setMessage({ type: "error", text: "Failed to update profile. Please try again." });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Profile Settings</CardTitle>
          <CardDescription>
            Update your account profile information.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={session?.user?.email || ""}
                disabled
                className="bg-muted"
              />
              <p className="text-sm text-muted-foreground">
                Email cannot be changed.
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Enter your full name"
              />
            </div>
            {message && (
              <p className={`text-sm ${message.type === "success" ? "text-green-500" : "text-red-500"}`}>
                {message.text}
              </p>
            )}
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Saving..." : "Save Changes"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API Configuration</CardTitle>
          <CardDescription>
            View your API configuration settings.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid gap-1">
              <Label>API URL</Label>
              <p className="text-sm text-muted-foreground font-mono">
                {typeof window !== "undefined" ? window.location.origin : ""}/api/v1
              </p>
            </div>
            <div className="grid gap-1">
              <Label>WebSocket URL</Label>
              <p className="text-sm text-muted-foreground font-mono">
                {typeof window !== "undefined"
                  ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/api/v1`
                  : ""}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
