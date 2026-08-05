import { useQuery } from "@tanstack/react-query";

import { getNotifications, getTaskStatus, listBackups } from "../api";
import type { Notification } from "../ApiResponse";
import { queryKeys } from "../queryKeys";

// Module-level (stable reference) so React Query memoizes the transform instead of
// re-running it — and returning a new array — on every render.
function sortByTimestampDesc(data: Notification[]): Notification[] {
  return [...data].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export function useNotifications() {
  return useQuery({
    queryKey: queryKeys.notifications,
    queryFn: getNotifications,
    select: sortByTimestampDesc,
  });
}

export function useBackups() {
  return useQuery({
    queryKey: queryKeys.backups,
    queryFn: async () => (await listBackups()).backups ?? [],
  });
}

/** Polls a background task while it's running; stops polling once terminal. */
export function useTaskStatus(taskId: string | null) {
  return useQuery({
    queryKey: queryKeys.taskStatus(taskId ?? ""),
    queryFn: () => getTaskStatus(taskId as string),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.task?.status;
      return status === "completed" || status === "failed" ? false : 1000;
    },
  });
}
