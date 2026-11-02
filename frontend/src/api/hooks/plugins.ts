import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addPluginRepository,
  getPluginCapabilities,
  getPluginCatalog,
  getPluginDownloadClients,
  getPluginIndexers,
  getPluginRepositories,
  getPluginSettings,
  getPlugins,
  installFromCatalog,
  refreshPluginRepository,
  removePluginRepository,
  setPluginEnabled,
  updatePluginRepository,
  updatePluginSettings,
} from "../api";
import type { PluginCapability, PluginResponse } from "../ApiResponse";
import { queryKeys } from "../queryKeys";

export interface PluginCapabilityOption {
  plugin: PluginResponse;
  capability: PluginCapability;
}

export function usePlugins() {
  return useQuery({
    queryKey: queryKeys.plugins,
    queryFn: getPlugins,
  });
}

export function usePluginCapabilities() {
  return useQuery({
    queryKey: queryKeys.pluginCapabilities,
    queryFn: getPluginCapabilities,
  });
}

export function useSetPluginEnabled() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { id: string; enabled: boolean }) =>
      setPluginEnabled(vars.id, vars.enabled),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins }),
  });
}

export function usePluginSettings(pluginId: string | null) {
  return useQuery({
    queryKey: queryKeys.pluginSettings(pluginId ?? ""),
    queryFn: () => getPluginSettings(pluginId as string),
    enabled: !!pluginId,
  });
}

export function useUpdatePluginSettings(pluginId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (values: Record<string, unknown>) =>
      updatePluginSettings(pluginId, values),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.pluginSettings(pluginId), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins });
    },
  });
}

export function usePluginRepositories() {
  return useQuery({
    queryKey: queryKeys.pluginRepositories,
    queryFn: getPluginRepositories,
  });
}

export function usePluginCatalog(enabled = true) {
  return useQuery({
    queryKey: queryKeys.pluginCatalog,
    queryFn: getPluginCatalog,
    enabled,
  });
}

/** Adding a repository fetches its index, so the catalog changes too. */
export function useAddPluginRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { url: string; name?: string }) =>
      addPluginRepository(vars.url, vars.name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.pluginRepositories });
      queryClient.invalidateQueries({ queryKey: queryKeys.pluginCatalog });
    },
  });
}

export function useUpdatePluginRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: {
      id: string;
      changes: { name?: string; enabled?: boolean };
    }) => updatePluginRepository(vars.id, vars.changes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.pluginRepositories });
      queryClient.invalidateQueries({ queryKey: queryKeys.pluginCatalog });
    },
  });
}

/** Removing a repository keeps its plugins installed but clears their origin. */
export function useRemovePluginRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => removePluginRepository(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.pluginRepositories });
      queryClient.invalidateQueries({ queryKey: queryKeys.pluginCatalog });
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins });
    },
  });
}

export function useRefreshPluginRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => refreshPluginRepository(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.pluginRepositories });
      queryClient.invalidateQueries({ queryKey: queryKeys.pluginCatalog });
    },
  });
}

export function useInstallFromCatalog() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: {
      uid: string;
      version?: string;
      repository_id?: string;
    }) => installFromCatalog(vars),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins });
      queryClient.invalidateQueries({ queryKey: queryKeys.pluginCatalog });
      queryClient.invalidateQueries({ queryKey: queryKeys.pluginRepositories });
    },
  });
}

/** Fetch all plugins, then expand each into its capabilities of a given kind. */
async function loadCapabilityOptions(
  fetchCaps: (pluginName: string) => Promise<PluginCapability[]>
): Promise<PluginCapabilityOption[]> {
  const plugins = await getPlugins();
  const options: PluginCapabilityOption[] = [];
  for (const plugin of plugins) {
    const capabilities = await fetchCaps(plugin.name);
    for (const capability of capabilities ?? []) {
      options.push({ plugin, capability });
    }
  }
  return options;
}

export function usePluginIndexerOptions(enabled = true) {
  return useQuery({
    queryKey: queryKeys.pluginIndexerOptions,
    queryFn: () => loadCapabilityOptions(getPluginIndexers),
    enabled,
  });
}

export function usePluginDownloadClientOptions(enabled = true) {
  return useQuery({
    queryKey: queryKeys.pluginDownloadClientOptions,
    queryFn: () => loadCapabilityOptions(getPluginDownloadClients),
    enabled,
  });
}
