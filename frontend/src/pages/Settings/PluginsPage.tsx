import { useState, useEffect } from "react";
import {
  Text,
  Button,
  Divider,
  FileButton,
  Group,
  Stack,
  Modal,
} from "@mantine/core";

import { getPlugins, uploadPlugin, restartBackend } from "../../api/api";
import type { PluginResponse } from "../../api/ApiResponse";
import { DataTable } from "mantine-datatable";
import { notifications } from "@mantine/notifications";
import { TbAlertCircle } from "react-icons/tb";

function PluginsPage() {
  const [plugins, setPlugins] = useState<PluginResponse[]>([]);
  const [uploading, setUploading] = useState(false);
  const [restartModalOpened, setRestartModalOpened] = useState(false);
  const [restarting, setRestarting] = useState(false);

  useEffect(() => {
    const fetchPlugins = async () => {
      const response = await getPlugins();
      setPlugins(response);
    };

    fetchPlugins();
  }, []);

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

        // TODO: Pretty sure this just refreshes the page instead of restarting the frontend server which is what we want
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

    setUploading(true);

    try {
      const result = await uploadPlugin(file);

      if (result.success) {
        notifications.show({
          title: "Success",
          message: result.message || "Plugin installed successfully.",
          color: "green",
        });

        setRestartModalOpened(true);
      } else {
        notifications.show({
          title: "Error",
          message: result.message || "Failed to install plugin.",
          color: "red",
        });
      }
    } catch (error) {
      notifications.show({
        title: "Error",
        message: `Failed to install plugin: ${error}`,
        color: "red",
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <Stack>
        <Group>
          <FileButton onChange={handleInstallPlugin} accept=".lna">
            {(props) => (
              <Button {...props} loading={uploading}>
                Install Plugin
              </Button>
            )}
          </FileButton>
        </Group>
        <Divider />
        <DataTable
          columns={[
            { accessor: "name", title: "Name" },
            { accessor: "version", title: "Version" },
            { accessor: "description", title: "Description" },
            { accessor: "type", title: "Type" },
          ]}
          records={plugins}
        />
      </Stack>

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
