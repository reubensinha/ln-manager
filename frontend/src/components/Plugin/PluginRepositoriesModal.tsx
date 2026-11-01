import { useState } from "react";
import {
  ActionIcon,
  Anchor,
  Badge,
  Button,
  Collapse,
  Group,
  Modal,
  Paper,
  Stack,
  Switch,
  Text,
  TextInput,
  Tooltip,
} from "@mantine/core";
import { DataTable } from "mantine-datatable";
import { TbPlus, TbRefresh, TbTrash, TbX } from "react-icons/tb";

import {
  useAddPluginRepository,
  usePluginRepositories,
  useRefreshPluginRepository,
  useRemovePluginRepository,
  useUpdatePluginRepository,
} from "../../api/hooks/plugins";

function formatRefreshed(value?: string | null) {
  if (!value) return "Never";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? "Never" : parsed.toLocaleString();
}

type Props = {
  opened: boolean;
  onClose: () => void;
};

function PluginRepositoriesModal({ opened, onClose }: Props) {
  const { data: repositories = [], isLoading } = usePluginRepositories();
  const addRepository = useAddPluginRepository();
  const updateRepository = useUpdatePluginRepository();
  const removeRepository = useRemovePluginRepository();
  const refreshRepository = useRefreshPluginRepository();

  // The add form expands inside this modal rather than opening a second one on top of
  // it: stacked modals hide the list the user is adding to.
  const [addOpened, setAddOpened] = useState(false);
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);

  const handleAdd = async () => {
    try {
      await addRepository.mutateAsync({
        url: url.trim(),
        name: name.trim() || undefined,
      });
      setAddOpened(false);
      setUrl("");
      setName("");
    } catch {
      // The mutation cache toast carries the backend's reason; keep the form open
      // with the URL intact so it can be corrected.
    }
  };

  const runWithBusy = async (id: string, action: () => Promise<unknown>) => {
    setBusyId(id);
    try {
      await action();
    } catch {
      // Already reported by the mutation cache.
    } finally {
      setBusyId(null);
    }
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Plugin Repositories"
      size="xl"
      centered
    >
      <Stack>
        <Group>
          <Button
            leftSection={
              addOpened ? <TbX size={16} /> : <TbPlus size={16} />
            }
            variant={addOpened ? "default" : "filled"}
            onClick={() => setAddOpened((open) => !open)}
          >
            {addOpened ? "Cancel" : "Add Repository"}
          </Button>
        </Group>

        <Collapse in={addOpened}>
          <Paper withBorder p="md">
            <Stack gap="md">
              <TextInput
                label="Repository URL"
                placeholder="https://example.com/plugins/index.json"
                description="Must be https. The index is fetched now, so a URL that cannot be read is rejected."
                value={url}
                onChange={(e) => setUrl(e.currentTarget.value)}
                required
              />
              <TextInput
                label="Name"
                placeholder="Taken from the repository if left blank"
                value={name}
                onChange={(e) => setName(e.currentTarget.value)}
              />
              <Text size="xs" c="dimmed">
                A repository can install code that runs on this server. Only add
                ones you trust.
              </Text>
              <Group justify="flex-end">
                <Button
                  onClick={handleAdd}
                  loading={addRepository.isPending}
                  disabled={!url.trim()}
                >
                  Add Repository
                </Button>
              </Group>
            </Stack>
          </Paper>
        </Collapse>

        <DataTable
          columns={[
            { accessor: "name", title: "Name" },
            {
              accessor: "url",
              title: "URL",
              render: (repo) => (
                <Anchor href={repo.url} target="_blank" size="sm">
                  {repo.url}
                </Anchor>
              ),
            },
            {
              accessor: "plugin_count",
              title: "Installed",
              render: (repo) => `${repo.plugin_count}`,
            },
            {
              accessor: "last_refreshed_at",
              title: "Last refreshed",
              render: (repo) =>
                repo.last_error ? (
                  <Tooltip
                    label={repo.last_error}
                    multiline
                    maw={360}
                    withArrow
                  >
                    <Badge color="red" variant="light">
                      Failed
                    </Badge>
                  </Tooltip>
                ) : (
                  <Text size="sm">
                    {formatRefreshed(repo.last_refreshed_at)}
                  </Text>
                ),
            },
            {
              accessor: "enabled",
              title: "Enabled",
              render: (repo) => (
                <Switch
                  checked={repo.enabled}
                  onChange={(e) =>
                    updateRepository.mutate({
                      id: repo.id,
                      changes: { enabled: e.currentTarget.checked },
                    })
                  }
                  disabled={updateRepository.isPending}
                  aria-label={`Toggle ${repo.name}`}
                />
              ),
            },
            {
              accessor: "actions",
              title: "",
              textAlign: "right",
              render: (repo) => (
                <Group gap="xs" justify="flex-end" wrap="nowrap">
                  <Tooltip label="Refresh">
                    <ActionIcon
                      variant="subtle"
                      loading={busyId === repo.id}
                      onClick={() =>
                        runWithBusy(repo.id, () =>
                          refreshRepository.mutateAsync(repo.id)
                        )
                      }
                      aria-label={`Refresh ${repo.name}`}
                    >
                      <TbRefresh size={16} />
                    </ActionIcon>
                  </Tooltip>
                  <Tooltip label="Remove">
                    <ActionIcon
                      color="red"
                      variant="subtle"
                      loading={busyId === repo.id}
                      onClick={() =>
                        runWithBusy(repo.id, () =>
                          removeRepository.mutateAsync(repo.id)
                        )
                      }
                      aria-label={`Remove ${repo.name}`}
                    >
                      <TbTrash size={16} />
                    </ActionIcon>
                  </Tooltip>
                </Group>
              ),
            },
          ]}
          records={repositories}
          fetching={isLoading}
          noRecordsText="No repositories added yet"
        />

        <Text size="xs" c="dimmed">
          Disabling a repository hides its plugins from Browse but keeps
          anything already installed. Removing one also keeps its plugins
          installed.
        </Text>
      </Stack>
    </Modal>
  );
}

export default PluginRepositoriesModal;
