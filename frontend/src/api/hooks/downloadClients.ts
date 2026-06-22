import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createDownloadClient,
  deleteDownloadClient,
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
