import { Modal, Stack, Card, Text, Group, Badge } from "@mantine/core";
import type { PluginCapability } from "../../api/ApiResponse";
import { usePluginDownloadClientOptions } from "../../api/hooks/plugins";

interface AddDownloadClientModalProps {
  opened: boolean;
  onClose: () => void;
  onSelectClient: (pluginName: string, pluginId: string, clientCapability: PluginCapability) => void;
}

export function AddDownloadClientModal({ opened, onClose, onSelectClient }: AddDownloadClientModalProps) {
  const { data: clientOptions = [], isLoading: loading } =
    usePluginDownloadClientOptions(opened);

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
