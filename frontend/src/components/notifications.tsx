"use client";
import { useStore } from "@/lib/store";
import { useEffect } from "react";
import { toast } from "sonner";

export function Notifications() {
  const { notifications, removeNotification } = useStore();
  useEffect(() => {
    notifications.forEach((n) => {
      if (n.type === "error") {
        toast.error(n.message);
      } else if (n.type === "success") {
        toast.success(n.message);
      } else {
        toast(n.message);
      }
      removeNotification(n.id);
    });
  }, [notifications, removeNotification]);
  return null;
}
