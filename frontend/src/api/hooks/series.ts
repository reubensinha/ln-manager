import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addSeries,
  getMetadataSources,
  getReleases,
  getSeries,
  getSeriesById,
  getSeriesFromSource,
  getSeriesGroupById,
  getSeriesGroups,
  searchSeries,
  setBookDownloaded,
} from "../api";
import { queryKeys } from "../queryKeys";

/* ---------------------------------- Queries --------------------------------- */

export function useSeriesGroups() {
  return useQuery({
    queryKey: queryKeys.seriesGroups,
    queryFn: getSeriesGroups,
  });
}

export function useSeriesGroup(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.seriesGroup(id ?? ""),
    queryFn: () => getSeriesGroupById(id as string),
    enabled: !!id,
  });
}

export function useSeriesList() {
  return useQuery({
    queryKey: queryKeys.seriesList,
    queryFn: getSeries,
  });
}

export function useSeries(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.series(id ?? ""),
    queryFn: () => getSeriesById(id as string),
    enabled: !!id,
  });
}

export function useReleases() {
  return useQuery({
    queryKey: queryKeys.releases,
    queryFn: getReleases,
  });
}

export function useMetadataSources() {
  return useQuery({
    queryKey: queryKeys.metadataSources,
    queryFn: getMetadataSources,
  });
}

export function useSearchSeries(
  source: string | undefined,
  query: string | undefined,
  sourceId: string | undefined
) {
  return useQuery({
    queryKey: queryKeys.search(source ?? "", query ?? ""),
    queryFn: () => searchSeries(query as string, sourceId as string),
    enabled: !!query && !!sourceId,
  });
}

export function useSeriesFromSource(
  sourceId: string,
  externalId: string | undefined,
  enabled = true
) {
  return useQuery({
    queryKey: queryKeys.seriesFromSource(sourceId, externalId ?? ""),
    queryFn: () => getSeriesFromSource(sourceId, externalId as string),
    enabled: enabled && !!externalId,
  });
}

/* --------------------------------- Mutations -------------------------------- */

export function useAddSeries() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: {
      sourceId: string;
      externalId: string;
      seriesGroup?: string | null;
    }) => addSeries(vars.sourceId, vars.externalId, vars.seriesGroup ?? null),
    onSuccess: () => {
      // Refresh both the grouped (Library) and flat (Spotlight) series lists.
      queryClient.invalidateQueries({ queryKey: queryKeys.seriesGroups });
      queryClient.invalidateQueries({ queryKey: queryKeys.seriesList });
    },
  });
}

export function useSetBookDownloaded(seriesId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { bookId: string; downloaded: boolean }) =>
      setBookDownloaded(vars.bookId, vars.downloaded),
    onSuccess: () => {
      if (seriesId) {
        queryClient.invalidateQueries({ queryKey: queryKeys.series(seriesId) });
      }
      queryClient.invalidateQueries({ queryKey: queryKeys.seriesGroups });
    },
  });
}
