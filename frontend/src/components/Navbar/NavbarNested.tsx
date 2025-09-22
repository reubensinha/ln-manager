import {
  TbAdjustments,
  TbCalendarStats,
  TbFileAnalytics,
  TbGauge,
  TbLock,
  TbNotes,
  TbPresentationAnalytics,
} from "react-icons/tb";
import { Code, Group, ScrollArea } from "@mantine/core";
import { LinksGroup } from "./NavbarLinksGroup";
// import { UserButton } from '../UserButton/UserButton';
import { Logo } from "./Logo";
import classes from "./NavbarNested.module.css";

const linkGroup = [
  { label: "Dashboard", icon: TbGauge },
  {
    label: "Market news",
    icon: TbNotes,
    initiallyOpened: true,
    links: [
      { label: "Overview", link: "/" },
      { label: "Forecasts", link: "/" },
      { label: "Outlook", link: "/" },
      { label: "Real time", link: "/" },
    ],
  },
  {
    label: "Releases",
    icon: TbCalendarStats,
    links: [
      { label: "Upcoming releases", link: "/" },
      { label: "Previous releases", link: "/" },
      { label: "Releases schedule", link: "/" },
    ],
  },
  { label: "Analytics", icon: TbPresentationAnalytics },
  { label: "Contracts", icon: TbFileAnalytics },
  { label: "Settings", icon: TbAdjustments },
  {
    label: "Security",
    icon: TbLock,
    links: [
      { label: "Enable 2FA", link: "/" },
      { label: "Change password", link: "/" },
      { label: "Recovery codes", link: "/" },
    ],
  },
];

export function NavbarNested() {
  const links = linkGroup.map((item) => (
    <LinksGroup {...item} key={item.label} />
  ));

  return (
    <nav className={classes.navbar}>
      <div className={classes.header}>
        <Group justify="space-between">
          <Logo style={{ width: 120 }} />
          <Code fw={700}>v3.1.2</Code>
        </Group>
      </div>

      <ScrollArea className={classes.links}>
        <div className={classes.linksInner}>{links}</div>
      </ScrollArea>

      {/* <div className={classes.footer}>
        <UserButton />
      </div> */}
    </nav>
  );
}
