import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

import {
  ActionIcon,
  TextInput,
  Text,
  Group,
  Center,
  Image,
} from "@mantine/core";
import {
  spotlight,
  Spotlight,
  type SpotlightActionGroupData,
} from "@mantine/spotlight";

import { TbSearch } from "react-icons/tb";

import { type SeriesGroupsResponse } from "../types/ApiResponse.ts";
import { getSeriesGroups } from "../api/api.ts";

// TODO: Use API to fetch metadata plugins to search from.

function SpotlightSearch() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [series, setSeries] = useState<SeriesGroupsResponse[]>([]);

  useEffect(() => {
    getSeriesGroups().then((data) => setSeries(data));
  }, []);

  const pinnedActions: SpotlightActionGroupData[] = [
    {
      group: "Add New Series",
      actions: [
        {
          id: "RanobeDB",
          label: "RanobeDB",
          description: "Search RanobeDB for new series",
          onClick: () => {
            const trimmed = query.trim();
            navigate(
              trimmed.length > 0
                ? `/search/RanobeDB/${encodeURIComponent(trimmed)}`
                : "/search/RanobeDB"
            );
          },
        },
      ],
    },
  ];

  const seriesActions: SpotlightActionGroupData[] = [
    {
      group: "Existing Series",
      actions: series.map((s) => ({
        id: s.id,
        label: s.title,
        description: `View series group: ${s.title}`,
        onClick: () => {
          navigate(`/series/${s.id}`);
        },
      })),
    },
  ];

  const filteredActions = seriesActions
    .flatMap((group) => group.actions)
    .filter((a) => a.label?.toLowerCase().includes(query.toLowerCase().trim()));

  return (
    <>
      <TextInput
        placeholder="Search..."
        radius="xl"
        size="md"
        readOnly
        onClick={() => spotlight.open()}
        rightSection={
          <ActionIcon
            variant="light"
            radius="xl"
            size={32}
            onClick={() => spotlight.open()}
          >
            <TbSearch size={18} />
          </ActionIcon>
        }
        styles={{
          input: { cursor: "pointer" },
        }}
      />

      <Spotlight.Root query={query} onQueryChange={setQuery}>
        <Spotlight.Search
          placeholder="Search..."
          leftSection={<TbSearch size={20} stroke="1.5" />}
        />
        <Spotlight.ActionsList>
          {/* pinned actions group */}
          {pinnedActions.map((group) => (
            <div key={group.group} style={{ marginBottom: 10 }}>
              <Text fw={600} size="xs" c="dimmed" mb={4}>
                {group.group}
              </Text>
              {group.actions.map((action) => (
                <Spotlight.Action
                  key={action.id}
                  onClick={action.onClick} // v7 uses onTrigger instead of onClick
                >
                  <Group wrap="nowrap" w="100%">
                    <Text>{action.label}</Text>
                    {action.description && (
                      <Text size="xs" color="dimmed">
                        {action.description}
                      </Text>
                    )}
                  </Group>
                </Spotlight.Action>
              ))}
            </div>
          ))}

          {/* filtered actions group */}
          {seriesActions.map((group) => {
            const filtered = group.actions.filter((a) =>
              a.label?.toLowerCase().includes(query.toLowerCase().trim())
            );

            if (filtered.length === 0) return null;

            return (
              <div key={group.group} style={{ marginTop: 10 }}>
                <Text fw={600} size="xs" c="dimmed" mb={4}>
                  {group.group}
                </Text>

                {filtered.map((action) => (
                  <Spotlight.Action key={action.id} onClick={action.onClick}>
                    <Group wrap="nowrap" w="100%">
                      {series.find((s) => s.id === action.id)?.img_url && (
                        <Center>
                          <Image
                            src={
                              series.find((s) => s.id === action.id)?.img_url
                            }
                            alt={action.label}
                            fit="contain"
                            width={40}
                            height={120}
                            style={{ borderRadius: 4 }}
                          />
                        </Center>
                      )}
                      <div style={{ flex: 1 }}>
                        <Text>{action.label}</Text>
                      </div>
                    </Group>
                  </Spotlight.Action>
                ))}
              </div>
            );
          })}

          {/* empty state */}
          {filteredActions.length === 0 && pinnedActions.length === 0 && (
            <Spotlight.Empty>Nothing found...</Spotlight.Empty>
          )}
        </Spotlight.ActionsList>
      </Spotlight.Root>
    </>
  );
}

export default SpotlightSearch;
