import { useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Group,
  Select,
  Stack,
  Switch,
  Text,
  TextInput,
  Tooltip,
} from "@mantine/core";
import { DataTable, type DataTableColumn } from "mantine-datatable";
import { TbAlertTriangle, TbDownload, TbSearch } from "react-icons/tb";

import {
  usePluginCatalog,
  useInstallFromCatalog,
} from "../../api/hooks/plugins";
import type {
  CatalogEntryResponse,
  CatalogVersion,
} from "../../api/ApiResponse";

/**
 * One selectable offer: a version from a particular repository. Conflicting offers
 * (same version, different file) appear separately, so choosing one here is also how
 * the user resolves a conflict - the backend refuses an ambiguous install otherwise.
 */
function offerValue(v: CatalogVersion) {
  return `${v.version}|${v.repo_id ?? ""}`;
}

function offerLabel(v: CatalogVersion, showRepo: boolean) {
  return showRepo && v.repo_name ? `${v.version} - ${v.repo_name}` : v.version;
}

/**
 * A rendered table row. Normally one per catalog entry, offering everything every
 * repository has; when grouped by repository, one per (entry, repository) pair, offering
 * only that repository's versions - inside a repository's group, listing another's
 * versions would misrepresent what that repository carries.
 */
type Row = {
  entry: CatalogEntryResponse;
  versions: CatalogVersion[];
  /** Unique per row, since one entry can appear under several repository groups. */
  key: string;
};

type Props = {
  /** Called after a successful install, to surface the restart notice. */
  onInstalled: (message: string) => void;
  /** Opens the repositories modal, for the empty state. */
  onManageRepositories: () => void;
};

function PluginBrowseTab({ onInstalled, onManageRepositories }: Props) {
  const { data: catalog, isLoading } = usePluginCatalog();
  const install = useInstallFromCatalog();
  const [chosen, setChosen] = useState<Record<string, string>>({});
  const [installingKey, setInstallingKey] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [repoFilter, setRepoFilter] = useState("all");
  const [groupByRepo, setGroupByRepo] = useState(false);

  const entries = catalog?.plugins ?? [];

  const repoOptions = [
    { value: "all", label: "All repositories" },
    ...[
      ...new Map(
        entries.flatMap((entry) =>
          entry.repos.map((repo) => [repo.id, repo.name] as const)
        )
      ),
    ]
      .map(([value, label]) => ({ value, label }))
      .sort((a, b) => a.label.localeCompare(b.label)),
  ];

  // A filter can outlive what it selected - the repository it names may have been
  // removed or disabled since - which would otherwise leave an empty table behind a
  // blank Select.
  const activeRepo = repoOptions.some((o) => o.value === repoFilter)
    ? repoFilter
    : "all";

  const needle = query.trim().toLowerCase();
  const filtered = entries.filter((entry) => {
    if (activeRepo !== "all" && !entry.repos.some((r) => r.id === activeRepo)) {
      return false;
    }
    if (!needle) return true;
    return [entry.name, entry.author, entry.description].some((field) =>
      field?.toLowerCase().includes(needle)
    );
  });
  const isFiltered = needle !== "" || activeRepo !== "all";

  const rows: Row[] = filtered.map((entry) => ({
    entry,
    versions: entry.versions,
    key: entry.uid,
  }));

  const groups = (() => {
    // Keyed by repository id, not name: two repositories may be given the same name.
    const byRepo = new Map<string, { id: string; label: string; rows: Row[] }>();
    for (const entry of filtered) {
      for (const repo of entry.repos) {
        if (activeRepo !== "all" && repo.id !== activeRepo) continue;
        const group =
          byRepo.get(repo.id) ?? { id: repo.id, label: repo.name, rows: [] };
        // Falling back to every offer matters: when two repositories publish the
        // byte-identical artifact the catalog keeps only the first one's entry, so
        // the second repository offers this plugin while owning none of its listed
        // versions. Installing then sources the file from whichever repository the
        // catalog did keep, which is the truthful record of where the bytes came from.
        const mine = entry.versions.filter((v) => v.repo_id === repo.id);
        group.rows.push({
          entry,
          versions: mine.length > 0 ? mine : entry.versions,
          key: `${entry.uid}|${repo.id}`,
        });
        byRepo.set(repo.id, group);
      }
    }
    return [...byRepo.values()].sort((a, b) => a.label.localeCompare(b.label));
  })();

  // Undefined when a repository lists a plugin whose versions were all dropped (a
  // malformed checksum, say): the entry still reaches us, with an empty `versions`.
  const selectedOffer = (row: Row): CatalogVersion | undefined => {
    if (row.versions.length === 0) return undefined;
    const value = chosen[row.key] ?? offerValue(row.versions[0]);
    return (
      row.versions.find((v) => offerValue(v) === value) ?? row.versions[0]
    );
  };

  const handleInstall = async (row: Row) => {
    const offer = selectedOffer(row);
    if (!offer) return;

    setInstallingKey(row.key);
    try {
      const result = await install.mutateAsync({
        uid: row.entry.uid,
        version: offer.version,
        // Always naming the repository keeps the request unambiguous even when two
        // repositories offer this exact version.
        repository_id: offer.repo_id ?? undefined,
      });
      onInstalled(result.message);
    } catch {
      // The queryClient's mutation cache already shows the backend's message.
    } finally {
      setInstallingKey(null);
    }
  };

  const columns: DataTableColumn<Row>[] = [
    { accessor: "name", title: "Name", render: (row) => row.entry.name },
    {
      accessor: "author",
      title: "Author",
      render: (row) => row.entry.author ?? "-",
    },
    {
      accessor: "version",
      title: "Version",
      render: (row) => {
        if (row.versions.length === 0) {
          return (
            <Text size="sm" c="dimmed">
              None offered
            </Text>
          );
        }
        if (row.versions.length === 1) {
          return row.versions[0].version;
        }
        // More than one offer: the label names the repository only when it
        // disambiguates, so a plain multi-version list stays readable.
        const duplicated = new Set(
          row.versions
            .map((v) => v.version)
            .filter((ver, i, all) => all.indexOf(ver) !== i)
        );
        const offer = selectedOffer(row);
        return (
          <Select
            size="xs"
            w={190}
            comboboxProps={{ withinPortal: true }}
            data={row.versions.map((v) => ({
              value: offerValue(v),
              label: offerLabel(v, duplicated.has(v.version)),
            }))}
            value={offer ? offerValue(offer) : null}
            onChange={(value) =>
              value && setChosen((prev) => ({ ...prev, [row.key]: value }))
            }
            allowDeselect={false}
            aria-label={`Version of ${row.entry.name} to install`}
          />
        );
      },
    },
    // Grouped by repository, the group heading already says who offers the row.
    ...(groupByRepo
      ? []
      : [
          {
            accessor: "repos",
            title: "Offered by",
            render: (row: Row) => (
              <Group gap="xs">
                {row.entry.repos.map((repo) => (
                  <Badge key={repo.id} variant="light" color="gray">
                    {repo.name}
                  </Badge>
                ))}
              </Group>
            ),
          },
        ]),
    {
      accessor: "description",
      title: "Description",
      render: (row) => row.entry.description ?? "-",
    },
    {
      accessor: "actions",
      title: "",
      textAlign: "right",
      render: (row) => {
        if (row.entry.installed) {
          return (
            <Badge color="green" variant="light">
              {row.entry.installed_version
                ? `Installed ${row.entry.installed_version}`
                : "Installed"}
            </Badge>
          );
        }

        const conflicted = row.entry.conflicts.some(
          (c) => c.version === selectedOffer(row)?.version
        );
        const button = (
          <Button
            size="xs"
            leftSection={<TbDownload size={14} />}
            loading={installingKey === row.key}
            disabled={row.versions.length === 0 || installingKey !== null}
            onClick={() => handleInstall(row)}
          >
            Install
          </Button>
        );

        return conflicted ? (
          <Tooltip
            multiline
            maw={320}
            withArrow
            label={
              "Repositories offer different files under this version number. " +
              "The selected repository's file will be installed."
            }
          >
            <Group gap="xs" justify="flex-end" wrap="nowrap">
              <TbAlertTriangle size={16} color="orange" />
              {button}
            </Group>
          </Tooltip>
        ) : (
          button
        );
      },
    },
  ];

  const noRecordsText = isFiltered
    ? "No plugins match the current filters"
    : "No plugins on offer from the configured repositories";

  if (!isLoading && (catalog?.repository_count ?? 0) === 0) {
    return (
      <Alert color="blue" title="No repositories yet">
        <Stack align="flex-start">
          <Text size="sm">
            Add a plugin repository to browse plugins you can install. You can
            always install a <b>.lna</b> file directly with the{" "}
            <b>Install Plugin</b> button.
          </Text>
          <Button size="xs" variant="light" onClick={onManageRepositories}>
            Add a repository
          </Button>
        </Stack>
      </Alert>
    );
  }

  return (
    <Stack>
      {catalog?.stale?.map((repo) => (
        <Alert
          key={repo.id}
          color="yellow"
          icon={<TbAlertTriangle size={18} />}
          title={`'${repo.name}' could not be refreshed`}
        >
          {repo.error ?? "The last refresh failed."} Showing the plugins from
          its last successful refresh.
        </Alert>
      ))}

      <Group gap="md">
        <TextInput
          placeholder="Search plugins..."
          value={query}
          onChange={(e) => setQuery(e.currentTarget.value)}
          leftSection={<TbSearch size={16} />}
          style={{ flex: 1 }}
        />
        <Select
          data={repoOptions}
          value={activeRepo}
          onChange={(value) => setRepoFilter(value ?? "all")}
          allowDeselect={false}
          style={{ width: 220 }}
          aria-label="Filter by repository"
        />
        <Switch
          label="Group by repository"
          checked={groupByRepo}
          onChange={(e) => setGroupByRepo(e.currentTarget.checked)}
        />
      </Group>

      {groupByRepo && groups.length > 0 ? (
        groups.map((group) => (
          <Stack key={group.id} gap="xs">
            <Group gap="xs">
              <Text fw={600} size="sm">
                {group.label}
              </Text>
              <Badge size="sm" variant="light" color="gray">
                {group.rows.length}
              </Badge>
            </Group>
            <DataTable
              columns={columns}
              records={group.rows}
              idAccessor="key"
            />
          </Stack>
        ))
      ) : (
        <DataTable
          columns={columns}
          records={groupByRepo ? [] : rows}
          fetching={isLoading}
          idAccessor="key"
          noRecordsText={noRecordsText}
        />
      )}

      <Text size="xs" c="dimmed">
        Downloads are checked against the checksum published by the repository
        before anything is installed.
      </Text>
    </Stack>
  );
}

export default PluginBrowseTab;
