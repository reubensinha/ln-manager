import { useState, useEffect } from "react";
import {
  Modal,
  Stack,
  Group,
  Text,
  Button,
  Alert,
  Checkbox,
} from "@mantine/core";
import { Dropzone, MIME_TYPES } from "@mantine/dropzone";
import {
  TbUpload,
  TbX,
  TbCheck,
  TbAlertCircle,
  TbDatabase,
} from "react-icons/tb";

interface FileUploadModalProps {
  opened: boolean;
  onClose: () => void;
  onSubmit: (file: File) => Promise<void>;
  title: string;
  initialFile?: File | null;
  acceptedFileTypes?: string[];
  maxSize?: number;
  uploadPrompt?: string;
  uploadDescription?: string;
  warningTitle?: string;
  warningMessage?: string;
  requireConfirmation?: boolean;
  confirmationLabel?: string;
  submitLabel?: string;
  submitColor?: string;
  icon?: React.ReactNode;
}

function FileUploadModal({
  opened,
  onClose,
  onSubmit,
  title,
  initialFile = null,
  acceptedFileTypes = [
    MIME_TYPES.zip,
    "application/x-zip-compressed",
    "application/x-compressed",
    ".zip",
  ],
  maxSize = 500 * 1024 * 1024, // 500 MB default
  uploadPrompt = "Drag file here or click to select",
  uploadDescription = "Upload a file",
  warningTitle,
  warningMessage,
  requireConfirmation = false,
  confirmationLabel = "I understand and want to proceed",
  submitLabel = "Upload",
  submitColor = "blue",
  icon = <TbDatabase size={52} />,
}: FileUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Set initial file when modal opens
  useEffect(() => {
    if (opened && initialFile) {
      setSelectedFile(initialFile);
    }
  }, [opened, initialFile]);

  const handleClose = () => {
    setSelectedFile(null);
    setConfirmed(false);
    onClose();
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;
    if (requireConfirmation && !confirmed) return;

    setSubmitting(true);
    try {
      await onSubmit(selectedFile);
      handleClose();
    } finally {
      setSubmitting(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <Modal opened={opened} onClose={handleClose} title={title} centered size="lg">
      <Stack gap="md">
        {!selectedFile && (
          <Dropzone
            onDrop={(files) => setSelectedFile(files[0])}
            maxSize={maxSize}
            accept={acceptedFileTypes}
          >
            <Group
              justify="center"
              gap="xl"
              mih={120}
              style={{ pointerEvents: "none" }}
            >
              <Dropzone.Accept>
                <TbUpload size={52} />
              </Dropzone.Accept>
              <Dropzone.Reject>
                <TbX size={52} />
              </Dropzone.Reject>
              <Dropzone.Idle>{icon}</Dropzone.Idle>

              <div>
                <Text size="xl" inline>
                  {uploadPrompt}
                </Text>
                <Text size="sm" c="dimmed" inline mt={7}>
                  {uploadDescription}
                </Text>
              </div>
            </Group>
          </Dropzone>
        )}

        {selectedFile && (
          <Alert icon={<TbCheck size={16} />} color="blue">
            <Text size="sm">
              Selected file: <strong>{selectedFile.name}</strong>
            </Text>
            <Text size="sm" c="dimmed">
              Size: {formatFileSize(selectedFile.size)}
            </Text>
          </Alert>
        )}

        {warningTitle && warningMessage && (
          <Alert icon={<TbAlertCircle size={16} />} color="orange" variant="light">
            <Stack gap="xs">
              <Text size="sm" fw={500}>
                {warningTitle}
              </Text>
              <Text size="sm">{warningMessage}</Text>
              {requireConfirmation && (
                <Checkbox
                  mt="xs"
                  label={confirmationLabel}
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.currentTarget.checked)}
                />
              )}
            </Stack>
          </Alert>
        )}

        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={handleClose}>
            Cancel
          </Button>
          {selectedFile && (
            <Button
              onClick={() => {
                setSelectedFile(null);
                setConfirmed(false);
              }}
              variant="light"
              color="gray"
            >
              Change File
            </Button>
          )}
          <Button
            onClick={handleSubmit}
            disabled={!selectedFile || (requireConfirmation && !confirmed)}
            loading={submitting}
            color={submitColor}
          >
            {submitLabel}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

export default FileUploadModal;
