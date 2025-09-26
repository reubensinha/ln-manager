import { lazy } from "react";
import { TbPuzzle } from "react-icons/tb";
import type { PluginManifest } from "../../types/Plugin";

// Lazy import so unused plugins don't bloat initial bundle
const Plugin1Page = lazy(() => import("./pages/Plugin1Page"));

const Plugin1Manifest: PluginManifest = {
  name: "Plugin 1",
  routes: [{ path: "/plugins/plugin1", element: <Plugin1Page /> }],
  navLinks: [
    {
      label: "Plugin 1",
      icon: TbPuzzle,
      link: "/plugins/plugin1",
    },
  ],
};

export default Plugin1Manifest;