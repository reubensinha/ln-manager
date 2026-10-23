import { useMemo } from "react";

import { usePlugins } from "../api/hooks/plugins";
import { pluginManifests } from "../plugin-manifests";
import type { PluginExtension } from "../types/Plugin";

export interface ResolvedExtension<TContext = unknown> {
  pluginName: string;
  extension: PluginExtension<TContext>;
}

/**
 * Components registered for an extension point by plugins the backend reports as
 * loaded.
 *
 * Frontend manifests are bundled at build time, so a plugin that is disabled, failed,
 * missing or held back by safe mode still has its manifest present — the backend status
 * is what decides whether its UI renders. Fails closed: nothing renders until the
 * plugin list has loaded successfully.
 */
export function usePluginExtensions<TContext = unknown>(
  point: string
): ResolvedExtension<TContext>[] {
  const { data: plugins } = usePlugins();

  return useMemo(() => {
    if (!plugins) return [];

    const loaded = new Set(
      plugins
        .filter((plugin) => plugin.status === "loaded")
        .map((plugin) => plugin.name.toLowerCase())
    );

    const resolved: ResolvedExtension<TContext>[] = [];
    for (const manifest of pluginManifests) {
      if (!manifest.extensions?.length) continue;

      if (!loaded.has(manifest.name.toLowerCase())) {
        if (import.meta.env.DEV && !plugins.some((p) => p.name.toLowerCase() === manifest.name.toLowerCase())) {
          console.warn(
            `[plugins] Frontend manifest "${manifest.name}" has no matching backend plugin; its UI will not render.`
          );
        }
        continue;
      }

      for (const extension of manifest.extensions) {
        if (extension.point !== point) continue;
        resolved.push({
          pluginName: manifest.name,
          extension: extension as PluginExtension<TContext>,
        });
      }
    }

    return resolved.sort(
      (a, b) =>
        (a.extension.order ?? 100) - (b.extension.order ?? 100) ||
        a.pluginName.localeCompare(b.pluginName)
    );
  }, [plugins, point]);
}
