import { useState } from "react";
import {
  Text,
  Button,
  Group,
  Stack,
  Modal,
  ActionIcon,
  Badge,
  Select,
  Switch,
  Tabs,
  TextInput,
  Tooltip,
  Alert,
} from "@mantine/core";
import { useQueryClient } from "@tanstack/react-query";

import { uploadPlugin, deletePlugin, restartBackend } from "../../api/api";
import {
  usePluginRepositories,
  usePlugins,
  useSetPluginEnabled,
} from "../../api/hooks/plugins";
import { queryKeys } from "../../api/queryKeys";
import type { PluginResponse } from "../../api/ApiResponse";
import { DataTable, type DataTableColumn } from "mantine-datatable";
import { notifications } from "@mantine/notifications";
import {
  TbAlertCircle,
  TbAlertTriangle,
  TbSearch,
  TbServer,
  TbSettings,
  TbTrash,
} from "react-icons/tb";
import FileUploadModal from "../../components/FileUploadModal";
import PluginBrowseTab from "../../components/Plugin/PluginBrowseTab";
import PluginRepositoriesModal from "../../components/Plugin/PluginRepositoriesModal";
import PluginSettingsModal from "../../components/Plugin/PluginSettingsModal";

const STATUS_COLOR: Record<string, string> = {
  loaded: "green",
  failed: "red",
  missing: "orange",
  pending_restart: "blue",
  disabled: "gray",
  safe_mode: "yellow",
};
const STATUS_LABEL: Record<string, string> = {
  loaded: "Loaded",
  failed: "Failed",
  missing: "Missing",
  pending_restart: "Restart needed",
  disabled: "Disabled",
  safe_mode: "Safe mode",
};

function PluginsPage() {
  const queryClient = useQueryClient();
  const { data: plugins = [] } = usePlugins();
  const { data: repositories = [] } = usePluginRepositories();
  const toggleEnabled = useSetPluginEnabled();
  const repoNames = new Map(repositories.map((r) => [r.id, r.name]));
  const safeMode = plugins.some((p) => p.status === "safe_mode");
  const [deleting, setDeleting] = useState(false);
  const [installModalOpened, setInstallModalOpened] = useState(false);
  const [repoModalOpened, setRepoModalOpened] = useState(false);
  const [restartModalOpened, setRestartModalOpened] = useState(false);
  const [restarting, setRestarting] = useState(false);
  const [settingsPlugin, setSettingsPlugin] = useState<PluginResponse | null>(null);
  const [query, setQuery] = useState("");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [groupBySource, setGroupBySource] = useState(false);

  /**
   * Where a plugin came from. One definition drives the Source column, the filter and
   * the grouping, so the three cannot disagree about what a plugin's origin is.
   */
  const sourceOf = (plugin: PluginResponse) => {
    if (plugin.bundled) {
      return { key: "bundled", label: "Bundled", color: "gray" };
    }
    if (plugin.source_repo_id) {
      // A removed repository leaves the plugin installed with its origin cleared, so
      // an unknown id here means the row is mid-refresh.
      return {
        key: `repo:${plugin.source_repo_id}`,
        label: repoNames.get(plugin.source_repo_id) ?? "Repository",
        color: "grape",
      };
    }
    return { key: "uploaded", label: "Uploaded", color: "blue" };
  };

  // Only the sources actually present: a filter entry for a repository nothing was
  // installed from would select an empty table.
  const sourceOptions = [
    { value: "all", label: "All sources" },
    ...[
      ...new Map(
        plugins.map((plugin) => {
          const source = sourceOf(plugin);
          return [source.key, source.label] as const;
        })
      ),
    ]
      .map(([value, label]) => ({ value, label }))
      .sort((a, b) => a.label.localeCompare(b.label)),
  ];

  // A filter can outlive what it selected - the last plugin from a repository
  // uninstalled, say - which would otherwise leave an empty table behind a blank
  // Select.
  const activeSource = sourceOptions.some((o) => o.value === sourceFilter)
    ? sourceFilter
    : "all";

  const needle = query.trim().toLowerCase();
  const visiblePlugins = plugins.filter((plugin) => {
    if (activeSource !== "all" && sourceOf(plugin).key !== activeSource) {
      return false;
    }
    if (!needle) return true;
    return [plugin.name, plugin.author, plugin.description].some((field) =>
      field?.toLowerCase().includes(needle)
    );
  });
  const isFiltered = needle !== "" || activeSource !== "all";

  const sourceGroups = (() => {
    // Keyed by source, not by label: two plugins from different removed repositories
    // are both labelled "Repository" and must still be two groups.
    const groups = new Map<
      string,
      { key: string; label: string; records: PluginResponse[] }
    >();
    for (const plugin of visiblePlugins) {
      const { key, label } = sourceOf(plugin);
      const group = groups.get(key) ?? { key, label, records: [] };
      group.records.push(plugin);
      groups.set(key, group);
    }
    return [...groups.values()].sort((a, b) => a.label.localeCompare(b.label));
  })();

  const handleRestartServers = async () => {
    setRestarting(true);

    try {
      const restart = await restartBackend();

      if (restart.success) {
        notifications.show({
          title: "Success",
          message: restart.message || "Backend restarted successfully.",
          color: "green",
        });

        await new Promise((resolve) => setTimeout(resolve, 2000));

        // TODO: This currently reloads the page but need to restart backend and rebuild frontend.
        window.location.reload();
      } else {
        notifications.show({
          title: "Error",
          message: restart.message || "Failed to restart backend.",
          color: "red",
        });
        setRestarting(false);
      }
    } catch (error) {
      notifications.show({
        title: "Error",
        message: `Failed to restart backend: ${error}`,
        color: "red",
      });
      setRestarting(false);
    }
  };

  // TODO: If install plugin is successful create a popup/modal with a button to restart, The button should call restartBackend from api.tsx, then restart the frontend server
  const handleInstallPlugin = async (file: File | null) => {
    // Placeholder logic for installing a plugin
    if (!file) return;

    try {
      const result = await uploadPlugin(file);

      notifications.show({
        title: "Success",
        message: result.message || "Plugin installed successfully.",
        color: "green",
      });

      setRestartModalOpened(true);

      // Refresh plugins list
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins });
    } catch (error) {
      notifications.show({
        title: "Error",
        message: `Failed to install plugin: ${error}`,
        color: "red",
      });
    }
  };

  const handleUninstallPlugin = async (plugin: PluginResponse) => {
    if (!plugin) return;

    setDeleting(true);

    try {
      const result = await deletePlugin(plugin.id);

      notifications.show({
        title: "Success",
        message: result.message || "Plugin uninstalled successfully.",
        color: "green",
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.plugins });
    } catch (error) {
      notifications.show({
        title: "Error",
        message: `Failed to uninstall plugin: ${error}`,
        color: "red",
      });
    } finally {
      setDeleting(false);
    }
  };

  const installedColumns: DataTableColumn<PluginResponse>[] = [
    { accessor: "name", title: "Name" },
    { accessor: "version", title: "Version" },
    // Grouped by source, the group heading already says where the row came from.
    ...(groupBySource
      ? []
      : [
          {
            accessor: "source",
            title: "Source",
            render: (plugin: PluginResponse) => {
              const source = sourceOf(plugin);
              return (
                <Badge color={source.color} variant="light">
                  {source.label}
                </Badge>
              );
            },
          },
        ]),
    {
      accessor: "status",
      title: "Status",
      render: (plugin) => {
        const st = plugin.status ?? "loaded";
        const badge = (
          <Badge color={STATUS_COLOR[st] ?? "gray"} variant="light">
            {STATUS_LABEL[st] ?? st}
          </Badge>
        );
        return st === "failed" && plugin.error ? (
          <Tooltip label={plugin.error} multiline maw={360} withArrow>
            {badge}
          </Tooltip>
        ) : (
          badge
        );
      },
    },
    {
      accessor: "enabled",
      title: "Enabled",
      render: (plugin) => (
        <Switch
          checked={plugin.enabled}
          onChange={(e) =>
            toggleEnabled.mutate({
              id: plugin.id,
              enabled: e.currentTarget.checked,
            })
          }
          disabled={toggleEnabled.isPending}
          aria-label={`Toggle ${plugin.name}`}
        />
      ),
    },
    { accessor: "description", title: "Description" },
    {
      accessor: "actions",
      title: "Actions",
      textAlign: "right",
      render: (plugin) => (
        <Group gap="xs" justify="flex-end" wrap="nowrap">
          {plugin.has_settings && (
            <Tooltip label="Settings">
              <ActionIcon
                variant="subtle"
                onClick={() => setSettingsPlugin(plugin)}
                aria-label={`Configure ${plugin.name}`}
              >
                <TbSettings size={16} />
              </ActionIcon>
            </Tooltip>
          )}
          <Tooltip
            label={
              plugin.bundled
                ? "Bundled plugins ship with the app and can only be disabled"
                : "Uninstall"
            }
          >
            <ActionIcon
              color="red"
              variant="subtle"
              onClick={() => handleUninstallPlugin(plugin)}
              loading={deleting}
              disabled={plugin.bundled}
              aria-label={`Uninstall ${plugin.name}`}
            >
              <TbTrash size={16} />
            </ActionIcon>
          </Tooltip>
        </Group>
      ),
    },
  ];

  return (
    <>
      <Stack>
        {safeMode && (
          <Alert
            color="yellow"
            icon={<TbAlertTriangle size={18} />}
            title="Safe mode active"
          >
            Plugins are not being loaded because <b>LN_SAFE_MODE</b> is set.
            Remove that environment variable and restart the backend to load
            plugins again.
          </Alert>
        )}

        <Tabs defaultValue="installed" keepMounted={false}>
          <Group justify="space-between" align="flex-end">
            <Tabs.List>
              <Tabs.Tab value="installed">Installed</Tabs.Tab>
              <Tabs.Tab value="browse">Browse</Tabs.Tab>
            </Tabs.List>
            <Group gap="xs" mb="xs">
              <Button
                variant="default"
                leftSection={<TbServer size={16} />}
                onClick={() => setRepoModalOpened(true)}
              >
                Repositories
              </Button>
              <Button onClick={() => setInstallModalOpened(true)}>
                Install Plugin
              </Button>
            </Group>
          </Group>

          <Tabs.Panel value="installed" pt="md">
            <Stack>
              <Group gap="md">
                <TextInput
                  placeholder="Search plugins..."
                  value={query}
                  onChange={(e) => setQuery(e.currentTarget.value)}
                  leftSection={<TbSearch size={16} />}
                  style={{ flex: 1 }}
                />
                <Select
                  data={sourceOptions}
                  value={activeSource}
                  onChange={(value) => setSourceFilter(value ?? "all")}
                  allowDeselect={false}
                  style={{ width: 220 }}
                  aria-label="Filter by source"
                />
                <Switch
                  label="Group by source"
                  checked={groupBySource}
                  onChange={(e) => setGroupBySource(e.currentTarget.checked)}
                />
              </Group>

              {groupBySource && sourceGroups.length > 0 ? (
                sourceGroups.map((group) => (
                  <Stack key={group.key} gap="xs">
                    <Group gap="xs">
                      <Text fw={600} size="sm">
                        {group.label}
                      </Text>
                      <Badge size="sm" variant="light" color="gray">
                        {group.records.length}
                      </Badge>
                    </Group>
                    <DataTable
                      columns={installedColumns}
                      records={group.records}
                    />
                  </Stack>
                ))
              ) : (
                <DataTable
                  columns={installedColumns}
                  records={groupBySource ? [] : visiblePlugins}
                  noRecordsText={
                    isFiltered
                      ? "No plugins match the current filters"
                      : "No plugins installed"
                  }
                />
              )}

              <Text size="xs" c="dimmed">
                Enabling or disabling a plugin takes effect after a backend
                restart.
              </Text>
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="browse" pt="md">
            <PluginBrowseTab
              onManageRepositories={() => setRepoModalOpened(true)}
              onInstalled={(message) => {
                notifications.show({
                  title: "Success",
                  message,
                  color: "green",
                });
                setRestartModalOpened(true);
              }}
            />
          </Tabs.Panel>
        </Tabs>
      </Stack>

      {settingsPlugin && (
        <PluginSettingsModal
          plugin={settingsPlugin}
          opened={!!settingsPlugin}
          onClose={() => setSettingsPlugin(null)}
        />
      )}

      <PluginRepositoriesModal
        opened={repoModalOpened}
        onClose={() => setRepoModalOpened(false)}
      />

      <FileUploadModal
        opened={installModalOpened}
        onClose={() => setInstallModalOpened(false)}
        onSubmit={handleInstallPlugin}
        title="Install Plugin"
        acceptedFileTypes={[".lna"]}
        uploadPrompt="Drag plugin file here or click to select"
        uploadDescription="Upload a .lna plugin file to install"
        submitLabel="Install Plugin"
        submitColor="blue"
      />

      <Modal
        opened={restartModalOpened}
        onClose={() => setRestartModalOpened(false)}
        title="Restart Required"
        centered
      >
        <Stack gap="md">
          <Group gap="xs">
            <TbAlertCircle size={20} />
            <Text size="sm">
              The plugin has been installed. A server restart is required for
              the changes to take effect.
            </Text>
          </Group>

          <Group justify="flex-end" mt="md">
            <Button
              variant="default"
              onClick={() => setRestartModalOpened(false)}
            >
              Later
            </Button>
            <Button
              onClick={handleRestartServers}
              loading={restarting}
              color="blue"
            >
              Restart Now
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}

export default PluginsPage;
