import type { JSX } from "react";
import { type NavLink } from "./NavLink";
import type { Indexer, DownloadClient } from "../api/ApiResponse";


// export interface PluginRoute {
//   path: string;
//   component: React.ComponentType;
// }


// export interface PluginNavbarLink {
//   label: string;
//   icon: React.ComponentType;
//   link: string;
//   subLinks?: PluginNavbarLink[];
// }

// export interface Plugin {
//   id: string;
//   name: string;
//   routes: PluginRoute[];
//   navbarLinks: PluginNavbarLink[];
// }

export interface IndexerConfigProps {
  indexer?: Indexer;
  pluginId: string;
  onSave: (indexer: Omit<Indexer, "id">) => Promise<void>;
  onCancel: () => void;
}

export interface DownloadClientConfigProps {
  client?: DownloadClient;
  pluginId: string;
  onSave: (client: Omit<DownloadClient, "id">) => Promise<void>;
  onCancel: () => void;
}

/**
 * A component a plugin contributes to one of the core UI's extension points
 * (see plugins/extensionPoints.ts).
 */
export interface PluginExtension<TContext = unknown> {
  /** An id from `extensionPoints`. */
  point: string;
  /** Unique within the plugin; used for the React key. */
  id: string;
  /** Lower sorts first. Defaults to 100. */
  order?: number;
  component: React.ComponentType<{ context: TContext }>;
}

export interface PluginManifest {
  name: string;
  routes: { path: string; element: JSX.Element }[];
  navLinks: NavLink[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  extensions?: PluginExtension<any>[];
  indexerConfigComponents?: Record<string, React.ComponentType<IndexerConfigProps>>;
  downloadClientConfigComponents?: Record<string, React.ComponentType<DownloadClientConfigProps>>;
}
