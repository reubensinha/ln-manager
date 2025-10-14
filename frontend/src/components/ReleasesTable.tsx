import React, { useState } from "react";

import {
  Box,
  Text,
  Collapse,
  UnstyledButton,
  Title,
  Group,
  Menu,
  ActionIcon,
  rem,
  Tooltip,
} from "@mantine/core";
import {
  TbBook,
  TbDeviceDesktop,
  TbHeadphonesFilled,
  TbLink,
  TbChevronRight,
} from "react-icons/tb";

import type { Release } from "../api/ApiResponse";

const formatIcons: Record<string, React.ReactNode> = {
  digital: <TbDeviceDesktop style={{ width: rem(18), height: rem(18) }} />,
  print: <TbBook style={{ width: rem(18), height: rem(18) }} />,
  audio: <TbHeadphonesFilled style={{ width: rem(18), height: rem(18) }} />,
};

function ReleasesTable({ releases }: { releases: Release[] }) {
  const groupedReleases = releases.reduce((acc, release) => {
    const language = release.language || "Unknown";
    if (!acc[language]) {
      acc[language] = [];
    }
    acc[language].push(release);
    return acc;
  }, {} as Record<string, Release[]>);

  const [opened, setOpened] = useState<Record<string, boolean>>(
    Object.fromEntries(Object.keys(groupedReleases).map((lang) => [lang, true]))
  );

  return (
    <Box ml={"xl"} mr={"xl"}>
      <Text size="md" fw={600} c="dimmed" mb="sm">
        Releases
      </Text>
      {Object.entries(groupedReleases).map(([language, releases]) => (
        <Box key={language} mb="md">
          <UnstyledButton
            onClick={() =>
              setOpened((o) => ({ ...o, [language]: !o[language] }))
            }
            style={{ width: "100%" }}
            mb="xs"
          >
            <Group gap="xs">
              <TbChevronRight
                style={{
                  width: rem(16),
                  height: rem(16),
                  transform: opened[language]
                    ? "rotate(90deg)"
                    : "rotate(0deg)",
                  transition: "transform 0.2s ease",
                }}
              />
              <Title order={5} tt={"uppercase"}>
                {language} ({releases.length})
              </Title>
            </Group>
          </UnstyledButton>

          {/* TODO: But the little turning arrow thing on the collapse button text */}
          <Collapse in={opened[language]}>
            {releases.map((release) => (
              <Group key={release.id}>
                <Text size="sm" pl="md">
                  {release.release_date}
                </Text>

                <Tooltip label={release.format} withArrow position="top">
                  <Box w={24}>
                    {
                      formatIcons[
                        release.format?.toLocaleLowerCase() ?? "unknown"
                      ]
                    }
                  </Box>
                </Tooltip>

                {release.language?.toLowerCase() === "ja" ? (
                  <Text size="sm" lineClamp={1} style={{ flex: 1 }}>
                    {release.romaji}
                  </Text>
                ) : (
                  <Text size="sm" lineClamp={1} style={{ flex: 1 }}>
                    {release.title}
                  </Text>
                )}

                {release.links && release.links.length > 0 && (
                  <Menu shadow="md" width={200} withArrow position="left-start">
                    <Menu.Target>
                      <ActionIcon variant="subtle" color="gray">
                        <TbLink style={{ width: rem(16), height: rem(16) }} />
                      </ActionIcon>
                    </Menu.Target>

                    <Menu.Dropdown>
                      {release.links.map((link) => (
                        <Menu.Item
                          key={link.url}
                          component="a"
                          href={link.url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {link.name}
                        </Menu.Item>
                      ))}
                    </Menu.Dropdown>
                  </Menu>
                )}
              </Group>
            ))}
          </Collapse>
        </Box>
      ))}
    </Box>
  );
}

export default ReleasesTable;
