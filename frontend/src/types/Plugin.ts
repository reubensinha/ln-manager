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
  onSave: (client: Omit<DownloadClient, "id">) => Promise<void>;
  onCancel: () => void;
}

export interface PluginManifest {
  name: string;
  routes: { path: string; element: JSX.Element }[];
  navLinks: NavLink[];
  indexerConfigComponents?: Record<string, React.ComponentType<IndexerConfigProps>>;
  downloadClientConfigComponents?: Record<string, React.ComponentType<DownloadClientConfigProps>>;
}
