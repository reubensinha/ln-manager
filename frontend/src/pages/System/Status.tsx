import { useState, useEffect } from "react";
import {
  Text,
  Button,
  Divider,
  Group,
  Stack,
  Modal,
  ActionIcon,
  Progress,
  Badge,
  Alert,
} from "@mantine/core";
import { Dropzone, MIME_TYPES } from "@mantine/dropzone";
import { DataTable } from "mantine-datatable";
import { notifications } from "@mantine/notifications";
import {
  TbTrash,
  TbDownload,
  TbUpload,
  TbDatabase,
  TbAlertCircle,
  TbX,
  TbCheck,
} from "react-icons/tb";

import {
  createBackupAsync,
  listBackups,
  downloadBackup,
  deleteBackup,
  restoreBackupAsync,
  getTaskStatus,
  clearTask,
} from "../../api/api";
import type { BackupInfo, TaskProgress } from "../../api/ApiResponse";

function Status() {
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [restoreModalOpened, setRestoreModalOpened] = useState(false);
  const [taskProgress, setTaskProgress] = useState<TaskProgress | null>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [overwrite, setOverwrite] = useState(false);

  useEffect(() => {
    fetchBackups();
  }, []);

  useEffect(() => {
    if (!currentTaskId) return;

    const interval = setInterval(async () => {
      const status = await getTaskStatus(currentTaskId);
      if (status?.task) {
        setTaskProgress(status.task);

        if (status.task.status === "completed" || status.task.status === "failed") {
          clearInterval(interval);
          
          if (status.task.status === "completed") {
            notifications.show({
              title: "Success",
              message: status.task.message,
              color: "green",
            });
            fetchBackups();
          } else {
            notifications.show({
              title: "Error",
              message: status.task.error || "Operation failed",
              color: "red",
            });
          }

          // Clean up task after a delay
          setTimeout(async () => {
            await clearTask(currentTaskId);
            setCurrentTaskId(null);
            setTaskProgress(null);
          }, 3000);
        }
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [currentTaskId]);

  const fetchBackups = async () => {
    setLoading(true);
    try {
      const response = await listBackups();
      if (response.success) {
        setBackups(response.backups);
      }
    } catch (error) {
      notifications.show({
        title: "Error",
        message: `Failed to load backups: ${error}`,
        color: "red",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBackup = async () => {
    try {
      const response = await createBackupAsync();
      if (response.success) {
        setCurrentTaskId(response.task_id);
        setTaskProgress({
          status: "pending",
          progress: 0,
          message: "Backup task started...",
          created_at: new Date().toISOString(),
          completed_at: null,
          result: null,
          error: null,
        });
      } else {
        notifications.show({
          title: "Error",
          message: response.message || "Failed to start backup",
          color: "red",
        });
      }
    } catch (error) {
      notifications.show({
        title: "Error",
        message: `Failed to create backup: ${error}`,
        color: "red",
      });
    }
  };

  const handleDownloadBackup = async (filename: string) => {
    try {
      const blob = await downloadBackup(filename);
      if (blob) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        notifications.show({
          title: "Success",
          message: "Backup downloaded successfully",
          color: "green",
        });
      } else {
        notifications.show({
          title: "Error",
          message: "Failed to download backup",
          color: "red",
        });
      }
    } catch (error) {
      notifications.show({
        title: "Error",
        message: `Failed to download backup: ${error}`,
        color: "red",
      });
    }
  };

  const handleDeleteBackup = async (filename: string) => {
    try {
      const response = await deleteBackup(filename);
      if (response.success) {
        notifications.show({
          title: "Success",
          message: "Backup deleted successfully",
          color: "green",
        });
        fetchBackups();
      } else {
        notifications.show({
          title: "Error",
          message: response.message || "Failed to delete backup",
          color: "red",
        });
      }
    } catch (error) {
      notifications.show({
        title: "Error",
        message: `Failed to delete backup: ${error}`,
        color: "red",
      });
    }
  };

  const handleRestoreFromTable = (backup: BackupInfo) => {
    // Convert backup to file for restore
    downloadBackup(backup.filename).then((blob) => {
      if (blob) {
        const file = new File([blob], backup.filename, { type: "application/zip" });
        setSelectedFile(file);
        setRestoreModalOpened(true);
      }
    });
  };

  const handleRestoreSubmit = async () => {
    if (!selectedFile) return;

    try {
      const response = await restoreBackupAsync(selectedFile, overwrite);
      if (response.success) {
        setCurrentTaskId(response.task_id);
        setTaskProgress({
          status: "pending",
          progress: 0,
          message: "Restore task started...",
          created_at: new Date().toISOString(),
          completed_at: null,
          result: null,
          error: null,
        });
        setRestoreModalOpened(false);
        setSelectedFile(null);
        setOverwrite(false);
      } else {
        notifications.show({
          title: "Error",
          message: response.message || "Failed to start restore",
          color: "red",
        });
      }
    } catch (error) {
      notifications.show({
        title: "Error",
        message: `Failed to restore backup: ${error}`,
        color: "red",
      });
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "green";
      case "failed":
        return "red";
      case "running":
        return "blue";
      default:
        return "gray";
    }
  };

  return (
    <>
      <Stack>
        <Group justify="space-between">
          <Group>
            <Button
              leftSection={<TbDatabase size={16} />}
              onClick={handleCreateBackup}
              disabled={!!currentTaskId}
            >
              Create Backup
            </Button>
            <Button
              leftSection={<TbUpload size={16} />}
              variant="light"
              onClick={() => {
                setSelectedFile(null);
                setOverwrite(false);
                setRestoreModalOpened(true);
              }}
              disabled={!!currentTaskId}
            >
              Restore from File
            </Button>
          </Group>
        </Group>

        {taskProgress && (
          <Alert
            icon={
              taskProgress.status === "completed" ? (
                <TbCheck size={16} />
              ) : taskProgress.status === "failed" ? (
                <TbX size={16} />
              ) : undefined
            }
            title={
              <Group gap="xs">
                <Text size="sm" fw={500}>
                  {taskProgress.message}
                </Text>
                <Badge size="sm" color={getStatusColor(taskProgress.status)}>
                  {taskProgress.status}
                </Badge>
              </Group>
            }
            color={getStatusColor(taskProgress.status)}
          >
            <Progress
              value={taskProgress.progress}
              size="sm"
              mt="xs"
              color={getStatusColor(taskProgress.status)}
              animated={taskProgress.status === "running"}
            />
          </Alert>
        )}

        <Divider />

        <DataTable
          columns={[
            {
              accessor: "filename",
              title: "Filename",
              render: (backup) => (
                <Text size="sm" fw={500}>
                  {backup.filename}
                </Text>
              ),
            },
            {
              accessor: "size",
              title: "Size",
              render: (backup) => (
                <Text size="sm">{formatFileSize(backup.size)}</Text>
              ),
            },
            {
              accessor: "created",
              title: "Created",
              render: (backup) => (
                <Text size="sm">{formatDate(backup.created)}</Text>
              ),
            },
            {
              accessor: "version",
              title: "Version",
              render: (backup) => (
                <Badge size="sm" variant="light">
                  {backup.version || "N/A"}
                </Badge>
              ),
            },
            {
              accessor: "actions",
              title: "Actions",
              textAlign: "right",
              render: (backup) => (
                <Group gap="xs" justify="flex-end">
                  <ActionIcon
                    color="blue"
                    variant="subtle"
                    onClick={() => handleDownloadBackup(backup.filename)}
                    title="Download"
                  >
                    <TbDownload size={16} />
                  </ActionIcon>
                  <ActionIcon
                    color="green"
                    variant="subtle"
                    onClick={() => handleRestoreFromTable(backup)}
                    disabled={!!currentTaskId}
                    title="Restore"
                  >
                    <TbUpload size={16} />
                  </ActionIcon>
                  <ActionIcon
                    color="red"
                    variant="subtle"
                    onClick={() => handleDeleteBackup(backup.filename)}
                    title="Delete"
                  >
                    <TbTrash size={16} />
                  </ActionIcon>
                </Group>
              ),
            },
          ]}
          records={backups}
          fetching={loading}
          noRecordsText="No backups found"
        />
      </Stack>

      <Modal
        opened={restoreModalOpened}
        onClose={() => {
          setRestoreModalOpened(false);
          setSelectedFile(null);
          setOverwrite(false);
        }}
        title="Restore Backup"
        centered
        size="lg"
      >
        <Stack gap="md">
          {!selectedFile && (
            <Dropzone
              onDrop={(files) => setSelectedFile(files[0])}
              onReject={() => {
                notifications.show({
                  title: "Error",
                  message: "Please upload a valid ZIP file",
                  color: "red",
                });
              }}
              maxSize={500 * 1024 * 1024} // 500 MB
              accept={[MIME_TYPES.zip]}
            >
              <Group justify="center" gap="xl" mih={120} style={{ pointerEvents: "none" }}>
                <Dropzone.Accept>
                  <TbUpload size={52} />
                </Dropzone.Accept>
                <Dropzone.Reject>
                  <TbX size={52} />
                </Dropzone.Reject>
                <Dropzone.Idle>
                  <TbDatabase size={52} />
                </Dropzone.Idle>

                <div>
                  <Text size="xl" inline>
                    Drag backup file here or click to select
                  </Text>
                  <Text size="sm" c="dimmed" inline mt={7}>
                    Upload a backup ZIP file to restore
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

          <Alert icon={<TbAlertCircle size={16} />} color="orange" variant="light">
            <Stack gap="xs">
              <Text size="sm" fw={500}>
                Warning: Restore will replace all current data
              </Text>
              <Text size="sm">
                Make sure you have a recent backup before proceeding. This action cannot be undone.
              </Text>
              <Group gap="xs" mt="xs">
                <input
                  type="checkbox"
                  id="overwrite-checkbox"
                  checked={overwrite}
                  onChange={(e) => setOverwrite(e.target.checked)}
                />
                <label htmlFor="overwrite-checkbox">
                  <Text size="sm">I understand and want to overwrite existing data</Text>
                </label>
              </Group>
            </Stack>
          </Alert>

          <Group justify="flex-end" mt="md">
            <Button
              variant="default"
              onClick={() => {
                setRestoreModalOpened(false);
                setSelectedFile(null);
                setOverwrite(false);
              }}
            >
              Cancel
            </Button>
            {selectedFile && (
              <Button
                onClick={() => setSelectedFile(null)}
                variant="light"
                color="gray"
              >
                Change File
              </Button>
            )}
            <Button
              onClick={handleRestoreSubmit}
              disabled={!selectedFile || !overwrite}
              color="orange"
            >
              Restore Backup
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}

export default Status;