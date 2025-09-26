import { useState } from "react";
import { TbChevronRight } from "react-icons/tb";
import {
  Box,
  Collapse,
  Group,
  Text,
  ThemeIcon,
  UnstyledButton,
} from "@mantine/core";
import { Link } from "react-router";
import classes from "./NavbarLinksGroup.module.css";
import { type NavLink } from "../../types/NavLink";

// interface NavLink {
//   icon: React.ElementType;
//   label: string;
//   link?: string;
//   initiallyOpened?: boolean;
//   links?: { label: string; link: string }[];
// }

export function LinksGroup({
  icon: Icon,
  label,
  link,
  initiallyOpened,
  links,
}: NavLink) {
  const hasLinks = Array.isArray(links);
  const hasTopLevelLink = typeof link === "string";
  const [opened, setOpened] = useState(initiallyOpened || false);
  const items = (hasLinks ? links : []).map((item) => (
    <Text<typeof Link>
      component={Link}
      className={classes.link}
      to={item.link}
      key={item.label}
      // onClick={(event) => event.preventDefault()}
      onClick={(event) => event.stopPropagation()}
    >
      {item.label}
    </Text>
  ));

  if (hasLinks) {
    return (
      <>
        <UnstyledButton
          onClick={() => setOpened((o) => !o)}
          className={classes.control}
        >
          <Group justify="space-between" gap={0}>
            <Box style={{ display: "flex", alignItems: "center" }}>
              <ThemeIcon variant="light" size={30}>
                <Icon size={18} />
              </ThemeIcon>
              <Box ml="md">{label}</Box>
            </Box>
            {hasLinks && (
              <TbChevronRight
                className={classes.chevron}
                stroke={"1.5"}
                size={16}
                style={{ transform: opened ? "rotate(-90deg)" : "none" }}
              />
            )}
          </Group>
        </UnstyledButton>
        <Collapse in={opened}>{items}</Collapse>
      </>
    );
  }

  if (!hasLinks && hasTopLevelLink) {
    return (
      <Text<typeof Link> component={Link} to={link} className={classes.control}>
        <Group justify="space-between" gap={0}>
          <Box style={{ display: "flex", alignItems: "center" }}>
            <ThemeIcon variant="light" size={30}>
              <Icon size={18} />
            </ThemeIcon>
            <Box ml="md">{label}</Box>
          </Box>
        </Group>
      </Text>
    );
  }

  return (
    <>
      <UnstyledButton
        onClick={() => setOpened((o) => !o)}
        className={classes.control}
      >
        <Group justify="space-between" gap={0}>
          <Box style={{ display: "flex", alignItems: "center" }}>
            <ThemeIcon variant="light" size={30}>
              <Icon size={18} />
            </ThemeIcon>
            <Box ml="md">{label}</Box>
          </Box>
        </Group>
      </UnstyledButton>
    </>
  );
}
