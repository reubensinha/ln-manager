import { QueryClient, QueryCache, MutationCache } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import axios from "axios";

/** Extract a human-readable message from an Axios/Error/unknown failure. */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred";
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: true,
    },
  },
  // Central error handling: any failed query/mutation surfaces a toast instead of
  // failing silently (the old api.ts pattern swallowed errors and returned []/null).
  queryCache: new QueryCache({
    onError: (error) => {
      notifications.show({
        color: "red",
        title: "Failed to load data",
        message: getErrorMessage(error),
      });
    },
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      notifications.show({
        color: "red",
        title: "Action failed",
        message: getErrorMessage(error),
      });
    },
  }),
});
