import {
  TbCalendarStats,
  TbGauge,
  TbNotes,
  TbPresentationAnalytics,
} from "react-icons/tb";
import { ScrollArea } from "@mantine/core";
import { LinksGroup } from "./NavbarLinksGroup";
// import { UserButton } from '../UserButton/UserButton';
import classes from "./NavbarNested.module.css";
import { pluginManifests } from "../../plugin-manifests";
import { getPlugins } from "../../api/api";
import { useLocation } from "react-router";

import { type NavLink } from "../../types/NavLink";

const pluginList = await getPlugins();

const isIndexerPlugin = pluginList?.some((p) => p.type === "indexer") ?? false;
const isDownloadClientPlugin =
  pluginList?.some((p) => p.type === "downloadclient") ?? false;

const coreLinkGroup: NavLink[] = [
  { label: "Library", icon: TbGauge, link: "/" },
  { label: "Calendar", icon: TbCalendarStats, link: "/calendar" },
  ...(isIndexerPlugin
    ? [
        {
          label: "Activity",
          icon: TbNotes,
          links: [
            { label: "Queue", link: "activity/queue" },
            { label: "History", link: "activity/history" },
            { label: "Blocklist", link: "activity/blocklist" },
          ],
        },
      ]
    : []),
  {
    label: "Settings",
    icon: TbGauge,
    links: [
      ...(isDownloadClientPlugin
        ? [{ label: "Media Management", link: "/settings/mediamanagement" }]
        : []),

      ...(isIndexerPlugin
        ? [
            { label: "Profiles", link: "/settings/profiles" },
            { label: "Custom Formats", link: "/settings/customformats" },
            { label: "Indexers", link: "/settings/indexers" },
          ]
        : []),

      ...(isDownloadClientPlugin
        ? [{ label: "Download Clients", link: "/settings/downloadclients" }]
        : []),

      { label: "Metadata Sources", link: "/settings/metadatasources" },
      { label: "General", link: "/settings/general" },
      { label: "Plugins", link: "/settings/plugins" },
    ],
  },
  {
    label: "System",
    icon: TbPresentationAnalytics,
    links: [
      { label: "Status", link: "/system/status" },
      { label: "Tasks", link: "/system/tasks" },
      { label: "Events", link: "/system/events" },
      { label: "Logs", link: "/system/logs" },
    ],
  },
];

export function NavbarNested() {
  const location = useLocation();
  const normalize = (p: string) => (p.startsWith("/") ? p : `/${p}`);

  const pluginLinks = pluginManifests.flatMap(
    (plugin) => plugin.navLinks || []
  );
  const combinedLinks = [...coreLinkGroup, ...pluginLinks];

  const links = combinedLinks.map((item) => (
    <LinksGroup
      {...item}
      key={item.label}
      initiallyOpened={
        Array.isArray(item.links)
          ? item.links.some(
              (s) =>
                location.pathname === normalize(s.link) ||
                location.pathname.startsWith(normalize(s.link))
            )
          : false
      }
    />
  ));

  return (
    <nav className={classes.navbar}>
      {/* <div className={classes.header}>
        <Group justify="space-between">
          <Logo style={{ width: 120 }} />
          <Code fw={700}>v3.1.2</Code>
        </Group>
      </div> */}

      <ScrollArea className={classes.links}>
        <div className={classes.linksInner}>{links}</div>
      </ScrollArea>

      {/* <div className={classes.footer}>
        <UserButton />
      </div> */}
    </nav>
  );
}
