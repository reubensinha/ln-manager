import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createIndexer,
  deleteIndexer,
  getIndexers,
  searchIndexers,
  searchSpecificIndexer,
  updateIndexer,
} from "../api";
import type { Indexer } from "../ApiResponse";
import { queryKeys } from "../queryKeys";

export function useIndexers(enabled = true) {
  return useQuery({
    queryKey: queryKeys.indexers,
    queryFn: getIndexers,
    enabled,
  });
}

export function useCreateIndexer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (indexer: Omit<Indexer, "id">) => createIndexer(indexer),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.indexers }),
  });
}

export function useUpdateIndexer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { id: string; data: Partial<Omit<Indexer, "id">> }) =>
      updateIndexer(vars.id, vars.data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.indexers }),
  });
}

export function useDeleteIndexer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteIndexer(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.indexers }),
  });
}

/** Interactive search is user-triggered, so it's a mutation rather than a query. */
export function useIndexerSearch() {
  return useMutation({
    mutationFn: (vars: { query: string; indexerId?: string | null }) =>
      vars.indexerId && vars.indexerId !== "all"
        ? searchSpecificIndexer(vars.indexerId, vars.query)
        : searchIndexers(vars.query),
  });
}
