import { useQuery } from "@tanstack/react-query";

import {
  getPluginCapabilities,
  getPluginDownloadClients,
  getPluginIndexers,
  getPlugins,
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
