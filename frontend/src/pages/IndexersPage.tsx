import { useEffect, useState } from "react";
import {
  Container,
  Title,
  SimpleGrid,
  Card,
  Text,
  Badge,
  Group,
  Stack,
  Button,
  ActionIcon,
  Menu,
  Switch,
} from "@mantine/core";
import { TbDots, TbTrash, TbSettings } from "react-icons/tb";
import { getIndexers, createIndexer, updateIndexer, deleteIndexer } from "../api/api";
import type { Indexer, PluginCapability } from "../api/ApiResponse";
import { AddIndexerModal } from "../components/AddIndexerModal";
import { IndexerConfigModal } from "../components/IndexerConfigModal";

function IndexersPage() {
  const [indexers, setIndexers] = useState<Indexer[]>([]);
  const [loading, setLoading] = useState(true);
  const [addModalOpened, setAddModalOpened] = useState(false);
  const [configModalOpened, setConfigModalOpened] = useState(false);
  const [selectedPluginName, setSelectedPluginName] = useState<string>("");
  const [selectedPluginId, setSelectedPluginId] = useState<string>("");
  const [selectedCapability, setSelectedCapability] = useState<PluginCapability | null>(null);
  const [editingIndexer, setEditingIndexer] = useState<Indexer | undefined>();

  useEffect(() => {
    loadIndexers();
  }, []);

  const loadIndexers = async () => {
    setLoading(true);
    try {
      const data = await getIndexers();
      setIndexers(data);
    } catch (error) {
      console.error("Error loading indexers:", error);
    } finally {
      setLoading(false);
    }
  };

  const getIndexerCapabilities = (config: Record<string, unknown> | undefined) => {
    // Extract capabilities from config - adjust based on your actual config structure
    const capabilities: string[] = [];
    
    if (config?.rss || config?.supports_rss) {
      capabilities.push("RSS");
    }
    if (config?.automatic_search || config?.supports_automatic_search) {
      capabilities.push("Automatic Search");
    }
    if (config?.interactive_search || config?.supports_interactive_search) {
      capabilities.push("Interactive Search");
    }
    
    // Default capabilities if none found
    if (capabilities.length === 0) {
      return ["RSS", "Automatic Search", "Interactive Search"];
    }
    
    return capabilities;
  };

  const getPriority = (config: Record<string, unknown> | undefined): number => {
    return (config?.priority as number) || 25;
  };

  const handleAddIndexer = () => {
    setEditingIndexer(undefined);
    setAddModalOpened(true);
  };

  const handleSelectIndexer = (pluginName: string, pluginId: string, capability: PluginCapability) => {
    setSelectedPluginName(pluginName);
    setSelectedPluginId(pluginId);
    setSelectedCapability(capability);
    setAddModalOpened(false);
    setConfigModalOpened(true);
  };

  const handleSaveIndexer = async (indexerData: Omit<Indexer, "id">) => {
    const result = await createIndexer(indexerData);
    if (result.success) {
      await loadIndexers();
    }
  };

  const handleEditIndexer = (indexer: Indexer) => {
    setEditingIndexer(indexer);
    setSelectedPluginName(indexer.plugin?.name || "");
    setSelectedPluginId(indexer.plugin_id || "");
    // We need to get the capability for this indexer
    // For now, we'll use a placeholder - you may need to store capability info with the indexer
    setSelectedCapability({ id: "torznab", name: indexer.name, description: indexer.description });
    setConfigModalOpened(true);
  };

  const handleUpdateIndexer = async (indexerData: Omit<Indexer, "id">) => {
    if (!editingIndexer) return;
    
    const result = await updateIndexer(editingIndexer.id, indexerData);
    if (result.success) {
      await loadIndexers();
    }
  };

  const handleToggleEnabled = async (indexerId: string) => {
    const indexer = indexers.find(i => i.id === indexerId);
    if (!indexer) return;

    // Send only the enabled field - backend supports partial updates
    const result = await updateIndexer(indexerId, { 
      enabled: !indexer.enabled 
    });
    
    if (result.success) {
      // Optimistically update the UI
      setIndexers(indexers.map(i => 
        i.id === indexerId ? { ...i, enabled: !i.enabled } : i
      ));
    }
  };

  const handleDelete = async (indexerId: string) => {
    const result = await deleteIndexer(indexerId);
    if (result.success) {
      setIndexers(indexers.filter(indexer => indexer.id !== indexerId));
    }
  };

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="xl">
        <Title order={1}>Indexers</Title>
        <Button leftSection={<span>+</span>} onClick={handleAddIndexer}>
          Add Indexer
        </Button>
      </Group>

      {loading ? (
        <Text>Loading indexers...</Text>
      ) : indexers.length === 0 ? (
        <Card shadow="sm" padding="xl" radius="md" withBorder>
          <Stack align="center" gap="md">
            <Text size="lg" fw={500}>No indexers configured</Text>
            <Text size="sm" c="dimmed">
              Add your first indexer to start finding releases
            </Text>
            <Button onClick={handleAddIndexer}>Add Indexer</Button>
          </Stack>
        </Card>
      ) : (
        <SimpleGrid
          cols={{ base: 1, sm: 2, md: 3, lg: 4 }}
          spacing="md"
        >
          {indexers.map((indexer) => (
            <Card
              key={indexer.id}
              shadow="sm"
              padding="lg"
              radius="md"
              withBorder
              style={{
                opacity: indexer.enabled ? 1 : 0.6,
                transition: "opacity 0.2s",
              }}
            >
              <Stack gap="md">
                <Group justify="space-between" align="flex-start">
                  <div style={{ flex: 1 }}>
                    <Group gap="xs" mb={4}>
                      <Text fw={500} size="lg" lineClamp={1}>
                        {indexer.name}
                      </Text>
                      <ActionIcon
                        variant="subtle"
                        size="sm"
                        color="gray"
                        onClick={() => handleEditIndexer(indexer)}
                      >
                        <TbSettings size={16} />
                      </ActionIcon>
                    </Group>
                    {indexer.plugin?.name && (
                      <Text size="sm" c="dimmed">
                        ({indexer.plugin.name})
                      </Text>
                    )}
                  </div>
                  
                  <Menu position="bottom-end" shadow="md">
                    <Menu.Target>
                      <ActionIcon variant="subtle" color="gray">
                        <TbDots size={18} />
                      </ActionIcon>
                    </Menu.Target>
                    <Menu.Dropdown>
                      <Menu.Item 
                        leftSection={<TbSettings size={16} />}
                        onClick={() => handleEditIndexer(indexer)}
                      >
                        Configure
                      </Menu.Item>
                      <Menu.Item
                        leftSection={<TbTrash size={16} />}
                        color="red"
                        onClick={() => handleDelete(indexer.id)}
                      >
                        Delete
                      </Menu.Item>
                    </Menu.Dropdown>
                  </Menu>
                </Group>

                <Group gap="xs">
                  {getIndexerCapabilities(indexer.config).map((capability) => (
                    <Badge
                      key={capability}
                      variant="light"
                      color="green"
                      size="sm"
                    >
                      {capability}
                    </Badge>
                  ))}
                </Group>

                <Group justify="space-between" align="center">
                  <Text size="sm" fw={500}>
                    Priority: {getPriority(indexer.config)}
                  </Text>
                  <Switch
                    checked={indexer.enabled}
                    onChange={() => handleToggleEnabled(indexer.id)}
                    label="Enabled"
                    size="sm"
                  />
                </Group>

                {indexer.description && (
                  <Text size="xs" c="dimmed" lineClamp={2}>
                    {indexer.description}
                  </Text>
                )}
              </Stack>
            </Card>
          ))}
        </SimpleGrid>
      )}

      <AddIndexerModal
        opened={addModalOpened}
        onClose={() => setAddModalOpened(false)}
        onSelectIndexer={handleSelectIndexer}
      />

      {selectedCapability && (
        <IndexerConfigModal
          opened={configModalOpened}
          onClose={() => setConfigModalOpened(false)}
          pluginName={selectedPluginName}
          pluginId={selectedPluginId}
          capability={selectedCapability}
          indexer={editingIndexer}
          onSave={editingIndexer ? handleUpdateIndexer : handleSaveIndexer}
        />
      )}
    </Container>
  );
}

export default IndexersPage;
