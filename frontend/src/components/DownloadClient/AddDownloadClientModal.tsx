import { Modal, Stack, Card, Text, Group, Badge } from "@mantine/core";
import { useEffect, useState } from "react";
import { getPlugins, getPluginDownloadClients } from "../../api/api";
import type { PluginResponse, PluginCapability } from "../../api/ApiResponse";

interface AddDownloadClientModalProps {
  opened: boolean;
  onClose: () => void;
  onSelectClient: (pluginName: string, pluginId: string, clientCapability: PluginCapability) => void;
}

interface ClientOption {
  plugin: PluginResponse;
  capability: PluginCapability;
}

export function AddDownloadClientModal({ opened, onClose, onSelectClient }: AddDownloadClientModalProps) {
  const [clientOptions, setClientOptions] = useState<ClientOption[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (opened) {
      loadClientOptions();
    }
  }, [opened]);

  const loadClientOptions = async () => {
    setLoading(true);
    try {
      const plugins = await getPlugins();
      
      const options: ClientOption[] = [];
      // Check each plugin for download client capabilities
      for (const plugin of plugins) {
        const capabilities = await getPluginDownloadClients(plugin.name);
        if (capabilities && capabilities.length > 0) {
          for (const capability of capabilities) {
            options.push({ plugin, capability });
          }
        }
      }
      
      setClientOptions(options);
    } catch (error) {
      console.error("Error loading download client options:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Add Download Client"
      size="md"
      centered
    >
      <Stack gap="md">
        {loading ? (
          <Text>Loading available download clients...</Text>
        ) : clientOptions.length === 0 ? (
          <Text c="dimmed">No download client plugins available. Please install a download client plugin first.</Text>
        ) : (
          clientOptions.map((option, idx) => (
            <Card
              key={`${option.plugin.id}-${idx}`}
              shadow="sm"
              padding="md"
              radius="md"
              withBorder
              style={{ cursor: "pointer" }}
              onClick={() => onSelectClient(option.plugin.name, option.plugin.id, option.capability)}
            >
              <Stack gap="xs">
                <Group justify="space-between">
                  <Text fw={500}>{option.capability.name}</Text>
                  <Badge variant="light" size="sm">
                    {option.plugin.name}
                  </Badge>
                </Group>
                {option.capability.description && (
                  <Text size="sm" c="dimmed">
                    {option.capability.description}
                  </Text>
                )}
              </Stack>
            </Card>
          ))
        )}
      </Stack>
    </Modal>
  );
}
