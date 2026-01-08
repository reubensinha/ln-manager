import { Modal, Stack, Card, Text, Group, Badge } from "@mantine/core";
import { useEffect, useState } from "react";
import { getPlugins, getPluginIndexers } from "../../api/api";
import type { PluginResponse, PluginCapability } from "../../api/ApiResponse";

interface AddIndexerModalProps {
  opened: boolean;
  onClose: () => void;
  onSelectIndexer: (pluginName: string, pluginId: string, indexerCapability: PluginCapability) => void;
}

interface IndexerOption {
  plugin: PluginResponse;
  capability: PluginCapability;
}

export function AddIndexerModal({ opened, onClose, onSelectIndexer }: AddIndexerModalProps) {
  const [indexerOptions, setIndexerOptions] = useState<IndexerOption[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (opened) {
      loadIndexerOptions();
    }
  }, [opened]);

  const loadIndexerOptions = async () => {
    setLoading(true);
    try {
      const plugins = await getPlugins();
      
      const options: IndexerOption[] = [];
      // Check each plugin for indexer capabilities
      for (const plugin of plugins) {
        const capabilities = await getPluginIndexers(plugin.name);
        if (capabilities && capabilities.length > 0) {
          for (const capability of capabilities) {
            options.push({ plugin, capability });
          }
        }
      }
      
      setIndexerOptions(options);
    } catch (error) {
      console.error("Error loading indexer options:", error);
    } finally {
      setLoading(false);
    }
  };

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
