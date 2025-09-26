import { type PluginManifest } from "./types/Plugin";

// Tell Vite's glob what type each module returns:
const modules = import.meta.glob<{
  default: PluginManifest;
}>("./plugins/**/manifest.tsx", { eager: true });

export const pluginManifests: PluginManifest[] = Object.values(modules).map(
  (m) => m.default
);
