import { useEffect, useState } from "react";
import {
  Button,
  Group,
  Modal,
  NumberInput,
  PasswordInput,
  Select,
  Stack,
  Switch,
  Text,
  TextInput,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";

import {
  SECRET_SENTINEL,
  type PluginResponse,
  type PluginSettingField,
} from "../../api/ApiResponse";
import {
  usePluginSettings,
  useUpdatePluginSettings,
} from "../../api/hooks/plugins";

interface PluginSettingsModalProps {
  plugin: PluginResponse;
  opened: boolean;
  onClose: () => void;
}

/**
 * Settings form generated from the schema a plugin declares in
 * BasePlugin.get_settings_schema(), so backend-only plugins need no frontend code.
 */
function PluginSettingsModal({
  plugin,
  opened,
  onClose,
}: PluginSettingsModalProps) {
  const { data, isPending } = usePluginSettings(opened ? plugin.id : null);
  const updateSettings = useUpdatePluginSettings(plugin.id);
  const [values, setValues] = useState<Record<string, unknown>>({});

  useEffect(() => {
    if (data) setValues(data.values);
  }, [data]);

  const schema = data?.settings_schema ?? {};
  const fields = Object.entries(schema);

  const setValue = (name: string, value: unknown) =>
    setValues((current) => ({ ...current, [name]: value }));

  const handleSave = async () => {
    try {
      await updateSettings.mutateAsync(values);
      notifications.show({
        title: "Saved",
        message: `${plugin.name} settings updated.`,
      });
      onClose();
    } catch {
      // The query client's mutation cache already surfaces the error toast.
    }
  };

  const renderField = (name: string, field: PluginSettingField) => {
    const label = field.label ?? name;
    const common = {
      key: name,
      label,
      description: field.description,
      required: field.required,
    };

    if (field.enum) {
      return (
        <Select
          {...common}
          data={field.enum.map((option) => String(option))}
          value={values[name] == null ? null : String(values[name])}
          onChange={(value) => setValue(name, value)}
        />
      );
    }
    if (field.secret) {
      return (
        <PasswordInput
          {...common}
          placeholder={
            values[name] === SECRET_SENTINEL ? "Saved — leave to keep" : "Not set"
          }
          value={values[name] === SECRET_SENTINEL ? "" : String(values[name] ?? "")}
          onChange={(event) => setValue(name, event.currentTarget.value)}
        />
      );
    }
    if (field.type === "boolean") {
      return (
        <Switch
          {...common}
          checked={Boolean(values[name])}
          onChange={(event) => setValue(name, event.currentTarget.checked)}
        />
      );
    }
    if (field.type === "number") {
      return (
        <NumberInput
          {...common}
          value={values[name] == null ? "" : Number(values[name])}
          onChange={(value) =>
            setValue(name, value === "" ? null : Number(value))
          }
        />
      );
    }
    return (
      <TextInput
        {...common}
        value={String(values[name] ?? "")}
        onChange={(event) => setValue(name, event.currentTarget.value)}
      />
    );
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={`${plugin.name} settings`}
      size="lg"
      centered
    >
      <Stack>
        {isPending && <Text>Loading settings...</Text>}
        {!isPending && fields.length === 0 && (
          <Text c="dimmed">This plugin has no configurable settings.</Text>
        )}
        {fields.map(([name, field]) => renderField(name, field))}

        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            loading={updateSettings.isPending}
            disabled={fields.length === 0}
          >
            Save
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

export default PluginSettingsModal;
