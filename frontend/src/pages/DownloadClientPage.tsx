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
import { TbDots, TbTrash, TbSettings, TbPlugConnected } from "react-icons/tb";
import {
  getDownloadClients,
  createDownloadClient,
  updateDownloadClient,
  deleteDownloadClient,
  getPluginDownloadClients,
} from "../api/api";
import type { DownloadClient, PluginCapability } from "../api/ApiResponse";
import { AddDownloadClientModal } from "../components/DownloadClient/AddDownloadClientModal";
import { DownloadClientConfigModal } from "../components/DownloadClient/DownloadClientConfigModal";

function DownloadClientPage() {
  const [clients, setClients] = useState<DownloadClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [addModalOpened, setAddModalOpened] = useState(false);
  const [configModalOpened, setConfigModalOpened] = useState(false);
  const [selectedPluginName, setSelectedPluginName] = useState<string>("");
  const [selectedPluginId, setSelectedPluginId] = useState<string>("");
  const [selectedCapability, setSelectedCapability] =
    useState<PluginCapability | null>(null);
  const [editingClient, setEditingClient] = useState<
    DownloadClient | undefined
  >();

  useEffect(() => {
    loadClients();
  }, []);

  const loadClients = async () => {
    setLoading(true);
    try {
      const data = await getDownloadClients();
      setClients(data);
    } catch (error) {
      console.error("Error loading download clients:", error);
    } finally {
      setLoading(false);
    }
  };

  const getClientFeatures = (
    config: Record<string, unknown> | undefined
  ) => {
    // Extract features from config
    const features: string[] = [];

    if (config?.ssl || config?.use_ssl) {
      features.push("SSL");
    }
    if (config?.authentication || config?.username) {
      features.push("Auth");
    }

    // Default features
    if (features.length === 0) {
      return ["Download", "Upload"];
    }

    return features;
  };

  const getHostInfo = (
    config: Record<string, unknown> | undefined
  ): string => {
    const host = config?.host as string;
    const port = config?.port as number;
    
    if (host && port) {
      return `${host}:${port}`;
    } else if (host) {
      return host;
    }
    
    return "Not configured";
  };

  const handleAddClient = () => {
    setEditingClient(undefined);
    setAddModalOpened(true);
  };

  const handleSelectClient = (
    pluginName: string,
    pluginId: string,
    capability: PluginCapability
  ) => {
    setSelectedPluginName(pluginName);
    setSelectedPluginId(pluginId);
    setSelectedCapability(capability);
    setAddModalOpened(false);
    setConfigModalOpened(true);
  };

  const handleSaveClient = async (clientData: Omit<DownloadClient, "id">) => {
    const result = await createDownloadClient(clientData);
    if (result.success) {
      await loadClients();
    }
  };

  const handleEditClient = async (client: DownloadClient) => {
    setEditingClient(client);
    setSelectedPluginName(client.plugin?.name || "");
    setSelectedPluginId(client.plugin_id || "");
    
    // Fetch the actual capabilities from the plugin to get the correct capability ID
    try {
      const capabilities = await getPluginDownloadClients(client.plugin?.name || "");
      // For now, assume the first capability matches (since qBittorrent only has one)
      // In the future, we might need to match based on config schema or store capability_id in the DB
      const capability = capabilities && capabilities.length > 0 ? capabilities[0] : {
        id: "qbittorrent", // fallback
        name: client.name,
        description: client.description,
      };
      setSelectedCapability(capability);
    } catch (error) {
      console.error("Error fetching plugin capabilities:", error);
      // Fallback to a basic capability object
      setSelectedCapability({
        id: "qbittorrent", // hardcoded fallback for qBittorrent
        name: client.name,
        description: client.description,
      });
    }
    
    setConfigModalOpened(true);
  };

  const handleUpdateClient = async (clientData: Omit<DownloadClient, "id">) => {
    if (!editingClient) return;

    const result = await updateDownloadClient(editingClient.id, clientData);
    if (result.success) {
      await loadClients();
    }
  };

  const handleToggleEnabled = async (clientId: string) => {
    const client = clients.find((c) => c.id === clientId);
    if (!client) return;

    const result = await updateDownloadClient(clientId, {
      enabled: !client.enabled,
    });

    if (result.success) {
      setClients(
        clients.map((c) =>
          c.id === clientId ? { ...c, enabled: !c.enabled } : c
        )
      );
    }
  };

  const handleDelete = async (clientId: string) => {
    const result = await deleteDownloadClient(clientId);
    if (result.success) {
      setClients(clients.filter((client) => client.id !== clientId));
    }
  };

  return (
    <Container size="xl" py="xl">
      <Group justify="space-between" mb="xl">
        <Title order={1}>Download Clients</Title>
        <Button leftSection={<span>+</span>} onClick={handleAddClient}>
          Add Download Client
        </Button>
      </Group>

      {loading ? (
        <Text>Loading download clients...</Text>
      ) : clients.length === 0 ? (
        <Card shadow="sm" padding="xl" radius="md" withBorder>
          <Stack align="center" gap="md">
            <TbPlugConnected size={48} style={{ opacity: 0.3 }} />
            <Text size="lg" fw={500}>
              No download clients configured
            </Text>
            <Text size="sm" c="dimmed">
              Add your first download client to start downloading releases
            </Text>
            <Button onClick={handleAddClient}>Add Download Client</Button>
          </Stack>
        </Card>
      ) : (
        <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing="md">
          {clients.map((client) => (
            <Card
              key={client.id}
              shadow="sm"
              padding="lg"
              radius="md"
              withBorder
              style={{
                opacity: client.enabled ? 1 : 0.6,
                transition: "opacity 0.2s",
              }}
            >
              <Stack gap="md">
                <Group justify="space-between" align="flex-start">
                  <div style={{ flex: 1 }}>
                    <Group gap="xs" mb={4}>
                      <Text fw={500} size="lg" lineClamp={1}>
                        {client.name}
                      </Text>
                      <ActionIcon
                        variant="subtle"
                        size="sm"
                        color="gray"
                        onClick={() => handleEditClient(client)}
                      >
                        <TbSettings size={16} />
                      </ActionIcon>
                    </Group>
                    {client.plugin?.name && (
                      <Text size="sm" c="dimmed">
                        ({client.plugin.name})
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
                        onClick={() => handleEditClient(client)}
                      >
                        Configure
                      </Menu.Item>
                      <Menu.Item
                        leftSection={<TbTrash size={16} />}
                        color="red"
                        onClick={() => handleDelete(client.id)}
                      >
                        Delete
                      </Menu.Item>
                    </Menu.Dropdown>
                  </Menu>
                </Group>

                <Group gap="xs" wrap="wrap">
                  {client.is_default && (
                    <Badge key="default" variant="filled" color="green" size="sm">
                      Default
                    </Badge>
                  )}
                  {getClientFeatures(client.config).map((feature) => (
                    <Badge key={feature} variant="light" color="blue" size="sm">
                      {feature}
                    </Badge>
                  ))}
                </Group>

                <Stack gap="xs">
                  <Group justify="space-between" align="center">
                    <Text size="xs" c="dimmed">
                      Host:
                    </Text>
                    <Text size="xs" fw={500}>
                      {getHostInfo(client.config)}
                    </Text>
                  </Group>
                  
                  <Group justify="space-between" align="center">
                    <Switch
                      checked={client.enabled}
                      onChange={() => handleToggleEnabled(client.id)}
                      label="Enabled"
                      size="sm"
                    />
                  </Group>
                </Stack>

                {client.description && (
                  <Text size="xs" c="dimmed" lineClamp={2}>
                    {client.description}
                  </Text>
                )}
              </Stack>
            </Card>
          ))}
        </SimpleGrid>
      )}

      <AddDownloadClientModal
        opened={addModalOpened}
        onClose={() => setAddModalOpened(false)}
        onSelectClient={handleSelectClient}
      />

      {selectedCapability && (
        <DownloadClientConfigModal
          opened={configModalOpened}
          onClose={() => setConfigModalOpened(false)}
          pluginName={selectedPluginName}
          pluginId={selectedPluginId}
          capability={selectedCapability}
          client={editingClient}
          onSave={editingClient ? handleUpdateClient : handleSaveClient}
        />
      )}
    </Container>
  );
}

export default DownloadClientPage;
