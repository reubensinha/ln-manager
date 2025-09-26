import type { JSX } from "react";
import { type NavLink } from "./NavLink";


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

export interface PluginManifest {
  name: string;
  routes: { path: string; element: JSX.Element }[];
  navLinks: NavLink[];
}