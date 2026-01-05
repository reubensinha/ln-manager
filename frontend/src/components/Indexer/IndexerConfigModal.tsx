import { Modal } from "@mantine/core";
import { pluginManifests } from "../../plugin-manifests";
import type { PluginCapability, Indexer } from "../../api/ApiResponse";

interface IndexerConfigModalProps {
  opened: boolean;
  onClose: () => void;
  pluginName: string;
  pluginId: string;
  capability: PluginCapability;
  indexer?: Indexer;
  onSave: (indexer: Omit<Indexer, "id">) => Promise<void>;
}

export function IndexerConfigModal({
  opened,
  onClose,
  pluginName,
  pluginId,
  capability,
  indexer,
  onSave,
}: IndexerConfigModalProps) {
  // Find the plugin manifest
  const manifest = pluginManifests.find(
    (m) => m.name.toLowerCase() === pluginName.toLowerCase()
  );

  // Find the config component for this indexer type
  const ConfigComponent = manifest?.indexerConfigComponents?.[capability.id];

  const handleSave = async (indexerData: Omit<Indexer, "id">) => {
    // Ensure plugin_id is set
    const completeData = {
      ...indexerData,
      plugin_id: indexerData.plugin_id || pluginId,
    };
    await onSave(completeData);
    onClose();
  };

  if (!ConfigComponent) {
    return (
      <Modal opened={opened} onClose={onClose} title="Configure Indexer" centered>
        <p>No configuration component found for {capability.name}</p>
        <p>Plugin: {pluginName}</p>
        <p>This indexer type may not support custom configuration yet.</p>
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
        indexer={indexer}
        pluginId={pluginId}
        onSave={handleSave}
        onCancel={onClose}
      />
    </Modal>
  );
}
