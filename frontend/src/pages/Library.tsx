import { useMemo } from "react";
import {
  SimpleGrid,
  Center,
  Loader,
  Group,
  Select,
  SegmentedControl,
  Switch,
  ActionIcon,
  Button,
  Text,
} from "@mantine/core";
import { useLocalStorage } from "@mantine/hooks";
import { TbSortAscending, TbSortDescending } from "react-icons/tb";

import { useSeriesGroups } from "../api/hooks/series";
import type { SeriesGroupsResponse } from "../api/ApiResponse";
import ItemCard from "../components/ItemCard/ItemCard";
import {
  TriStateSelect,
  keysWith,
  type TriStateValue,
} from "../components/common/TriStateSelect";
import { type CardItem } from "../types/CardItems";

type SortKey = "title" | "last_release" | "next_release" | "volumes" | "date_added";
type SortDir = "asc" | "desc";
type MonitoredFilter = "all" | "monitored" | "unmonitored";

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: "title", label: "Title" },
  { value: "last_release", label: "Last release" },
  { value: "next_release", label: "Next release" },
  { value: "volumes", label: "Volumes" },
  { value: "date_added", label: "Date added" },
];

const STATUS_OPTIONS = [
  { value: "continuing", label: "Continuing" },
  { value: "continuing_orig", label: "Continuing (orig)" },
  { value: "completed", label: "Completed" },
  { value: "stalled", label: "Stalled" },
  { value: "missing", label: "Missing" },
  { value: "none", label: "None" },
];

function sortValue(g: SeriesGroupsResponse, key: SortKey): string | number | null {
  switch (key) {
    case "title":
      return g.title?.toLowerCase() ?? "";
    case "last_release":
      return g.last_release_date ?? null;
    case "next_release":
      return g.next_release_date ?? null;
    case "volumes":
      return g.volume_count ?? 0;
    case "date_added":
      return g.created_at ?? null;
  }
}

function Library() {
  const { data: seriesGroups, isLoading } = useSeriesGroups();

  // Persisted to localStorage so filter/sort preferences survive refreshes.
  const [sortKey, setSortKey] = useLocalStorage<SortKey>({
    key: "library:sortKey",
    defaultValue: "title",
    getInitialValueInEffect: false,
  });
  const [sortDir, setSortDir] = useLocalStorage<SortDir>({
    key: "library:sortDir",
    defaultValue: "asc",
    getInitialValueInEffect: false,
  });
  const [statusFilter, setStatusFilter] = useLocalStorage<TriStateValue>({
    key: "library:statusFilter",
    defaultValue: {},
    getInitialValueInEffect: false,
  });
  const [languageFilter, setLanguageFilter] = useLocalStorage<TriStateValue>({
    key: "library:languageFilter",
    defaultValue: {},
    getInitialValueInEffect: false,
  });
  const [monitoredFilter, setMonitoredFilter] = useLocalStorage<MonitoredFilter>({
    key: "library:monitoredFilter",
    defaultValue: "all",
    getInitialValueInEffect: false,
  });
  const [hideNsfw, setHideNsfw] = useLocalStorage<boolean>({
    key: "library:hideNsfw",
    defaultValue: false,
    getInitialValueInEffect: false,
  });

  const availableLanguages = useMemo(() => {
    const set = new Set<string>();
    (seriesGroups ?? []).forEach((g) =>
      (g.languages ?? []).forEach((l) => set.add(l))
    );
    return Array.from(set).sort();
  }, [seriesGroups]);

  const visibleGroups = useMemo(() => {
    const statusInclude = keysWith(statusFilter, "include");
    const statusExclude = keysWith(statusFilter, "exclude");
    const langInclude = keysWith(languageFilter, "include");
    const langExclude = keysWith(languageFilter, "exclude");

    const filtered = (seriesGroups ?? []).filter((g) => {
      // Download status (single value per group).
      if (statusInclude.length && !statusInclude.includes(g.download_status))
        return false;
      if (statusExclude.includes(g.download_status)) return false;

      // Monitored.
      if (monitoredFilter === "monitored" && !g.monitored) return false;
      if (monitoredFilter === "unmonitored" && g.monitored) return false;

      // NSFW cover.
      if (hideNsfw && g.nsfw_img) return false;

      // Language (a group is published in a set of languages).
      const langs = g.languages ?? [];
      if (langInclude.length && !langInclude.some((l) => langs.includes(l)))
        return false;
      if (langExclude.some((l) => langs.includes(l))) return false;

      return true;
    });

    return [...filtered].sort((a, b) => {
      const av = sortValue(a, sortKey);
      const bv = sortValue(b, sortKey);
      // Null/unknown values always sort to the end, regardless of direction.
      if (av === null && bv === null) return 0;
      if (av === null) return 1;
      if (bv === null) return -1;
      const cmp =
        typeof av === "number" && typeof bv === "number"
          ? av - bv
          : String(av).localeCompare(String(bv));
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [
    seriesGroups,
    sortKey,
    sortDir,
    statusFilter,
    languageFilter,
    monitoredFilter,
    hideNsfw,
  ]);

  const cards: CardItem[] = visibleGroups.map((item) => ({
    id: item.id,
    title: item.title,
    img_url: item.img_url,
    link: `/series/${item.id}`,
    in_library: true,
    nsfw_img: item.nsfw_img,
    downloaded: item.download_status,
    monitored: item.monitored,
  }));

  const total = seriesGroups?.length ?? 0;
  const hasActiveFilters =
    Object.keys(statusFilter).length > 0 ||
    Object.keys(languageFilter).length > 0 ||
    monitoredFilter !== "all" ||
    hideNsfw;

  const clearFilters = () => {
    setStatusFilter({});
    setLanguageFilter({});
    setMonitoredFilter("all");
    setHideNsfw(false);
  };

  if (isLoading) {
    return (
      <Center mt="xl">
        <Loader />
      </Center>
    );
  }

  return (
    <>
      <Group align="flex-end" gap="md" mb="md" wrap="wrap">
        <Group gap={4} align="flex-end">
          <Select
            label="Sort by"
            data={SORT_OPTIONS}
            value={sortKey}
            onChange={(v) => setSortKey((v as SortKey) ?? "title")}
            allowDeselect={false}
            w={150}
          />
          <ActionIcon
            variant="default"
            size="lg"
            aria-label={`Sort ${sortDir === "asc" ? "ascending" : "descending"}`}
            onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
          >
            {sortDir === "asc" ? (
              <TbSortAscending size={18} />
            ) : (
              <TbSortDescending size={18} />
            )}
          </ActionIcon>
        </Group>

        <TriStateSelect
          label="Status"
          options={STATUS_OPTIONS}
          value={statusFilter}
          onChange={setStatusFilter}
          width={190}
        />

        {availableLanguages.length > 0 && (
          <TriStateSelect
            label="Language"
            options={availableLanguages.map((l) => ({
              value: l,
              label: l.toUpperCase(),
            }))}
            value={languageFilter}
            onChange={setLanguageFilter}
            width={140}
          />
        )}

        <div>
          <Text size="sm" fw={500} mb={4}>
            Monitored
          </Text>
          <SegmentedControl
            value={monitoredFilter}
            onChange={(v) => setMonitoredFilter(v as MonitoredFilter)}
            data={[
              { label: "All", value: "all" },
              { label: "Yes", value: "monitored" },
              { label: "No", value: "unmonitored" },
            ]}
          />
        </div>

        <Switch
          label="Hide NSFW"
          checked={hideNsfw}
          onChange={(e) => setHideNsfw(e.currentTarget.checked)}
          mb={8}
        />

        {hasActiveFilters && (
          <Button variant="subtle" onClick={clearFilters} mb={4}>
            Clear filters
          </Button>
        )}
      </Group>

      <Text size="sm" c="dimmed" mb="sm">
        {visibleGroups.length} of {total} series
      </Text>

      {cards.length === 0 ? (
        <Text c="dimmed" mt="xl" ta="center">
          {total === 0
            ? "Your library is empty."
            : "No series match the current filters."}
        </Text>
      ) : (
        <SimpleGrid type="container" cols={{ base: 2, "500px": 5, "1000px": 8 }}>
          {cards.map((seriesItem) => (
            <ItemCard key={seriesItem.id} item={seriesItem} />
          ))}
        </SimpleGrid>
      )}
    </>
  );
}

export default Library;
