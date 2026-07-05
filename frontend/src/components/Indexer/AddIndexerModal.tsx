import { Modal, Stack, Card, Text, Group, Badge } from "@mantine/core";
import type { PluginCapability } from "../../api/ApiResponse";
import { usePluginIndexerOptions } from "../../api/hooks/plugins";

interface AddIndexerModalProps {
  opened: boolean;
  onClose: () => void;
  onSelectIndexer: (pluginName: string, pluginId: string, indexerCapability: PluginCapability) => void;
}

export function AddIndexerModal({ opened, onClose, onSelectIndexer }: AddIndexerModalProps) {
  const { data: indexerOptions = [], isLoading: loading } =
    usePluginIndexerOptions(opened);

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Add Indexer"
      size="md"
      centered
    >
      <Stack gap="md">
        {loading ? (
          <Text>Loading available indexers...</Text>
        ) : indexerOptions.length === 0 ? (
          <Text c="dimmed">No indexer plugins available. Please install an indexer plugin first.</Text>
        ) : (
          indexerOptions.map((option, idx) => (
            <Card
              key={`${option.plugin.id}-${idx}`}
              shadow="sm"
              padding="md"
              radius="md"
              withBorder
              style={{ cursor: "pointer" }}
              onClick={() => onSelectIndexer(option.plugin.name, option.plugin.id, option.capability)}
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
