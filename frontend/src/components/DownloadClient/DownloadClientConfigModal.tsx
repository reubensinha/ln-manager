import { Modal } from "@mantine/core";
import { pluginManifests } from "../../plugin-manifests";
import type { PluginCapability, DownloadClient } from "../../api/ApiResponse";

interface DownloadClientConfigModalProps {
  opened: boolean;
  onClose: () => void;
  pluginName: string;
  pluginId: string;
  capability: PluginCapability;
  client?: DownloadClient;
  onSave: (client: Omit<DownloadClient, "id">) => Promise<void>;
}

export function DownloadClientConfigModal({
  opened,
  onClose,
  pluginName,
  pluginId,
  capability,
  client,
  onSave,
}: DownloadClientConfigModalProps) {
  // Find the plugin manifest
  const manifest = pluginManifests.find(
    (m) => m.name.toLowerCase() === pluginName.toLowerCase()
  );

  // Find the config component for this client type
  const ConfigComponent = manifest?.downloadClientConfigComponents?.[capability.id];

  const handleSave = async (clientData: Omit<DownloadClient, "id">) => {
    // Ensure plugin_id is set
    const completeData = {
      ...clientData,
      plugin_id: clientData.plugin_id || pluginId,
    };
    await onSave(completeData);
    onClose();
  };

  if (!ConfigComponent) {
    return (
      <Modal opened={opened} onClose={onClose} title="Configure Download Client" centered>
        <p>No configuration component found for {capability.name}</p>
        <p>Plugin: {pluginName}</p>
        <p>This download client type may not support custom configuration yet.</p>
      </Modal>
    );
  }

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={`Configure ${capability.name}`}
      size="lg"
      centered
    >
      <ConfigComponent
        client={client}
        pluginId={pluginId}
        onSave={handleSave}
        onCancel={onClose}
      />
    </Modal>
  );
}
