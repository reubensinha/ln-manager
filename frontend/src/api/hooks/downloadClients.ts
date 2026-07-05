import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";

import {
  createDownloadClient,
  deleteDownloadClient,
  downloadRelease,
  getDownloadClients,
  updateDownloadClient,
} from "../api";
import type { DownloadClient } from "../ApiResponse";
import { queryKeys } from "../queryKeys";

export function useDownloadClients(enabled = true) {
  return useQuery({
    queryKey: queryKeys.downloadClients,
    queryFn: getDownloadClients,
    enabled,
  });
}

export function useCreateDownloadClient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (client: Omit<DownloadClient, "id">) =>
      createDownloadClient(client),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.downloadClients }),
  });
}

export function useUpdateDownloadClient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: {
      id: string;
      data: Partial<Omit<DownloadClient, "id">>;
    }) => updateDownloadClient(vars.id, vars.data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.downloadClients }),
  });
}

export function useDeleteDownloadClient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteDownloadClient(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.downloadClients }),
  });
}

/** Send a release to a download client; errors surface via the central toast. */
export function useDownloadRelease() {
  return useMutation({
    mutationFn: (vars: {
      downloadUrl?: string;
      magnet?: string;
      downloadClientId?: string;
    }) => downloadRelease(vars.downloadUrl, vars.magnet, vars.downloadClientId),
    onSuccess: (data) => {
      notifications.show({
        color: "green",
        title: "Download started",
        message: data.message || "Sent to download client.",
      });
    },
  });
}
