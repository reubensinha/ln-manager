import { useState, useEffect } from "react";
import {
  Text,
  Button,
  Divider,
  Group,
  Stack,
  ActionIcon,
  Progress,
  Badge,
  Alert,
} from "@mantine/core";
import { DataTable } from "mantine-datatable";
import { notifications } from "@mantine/notifications";
import {
  TbTrash,
  TbDownload,
  TbUpload,
  TbDatabase,
  TbX,
  TbCheck,
} from "react-icons/tb";
import FileUploadModal from "../../components/FileUploadModal";

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
  const [selectedBackupFile, setSelectedBackupFile] = useState<File | null>(null);

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

  const handleRestoreFromTable = async (backup: BackupInfo) => {
    try {
      const blob = await downloadBackup(backup.filename);
      if (blob) {
        const file = new File([blob], backup.filename, { type: "application/zip" });
        setSelectedBackupFile(file);
        setRestoreModalOpened(true);
      } else {
        notifications.show({
          title: "Error",
          message: "Failed to download backup for restore",
          color: "red",
        });
      }
    } catch (error) {
      notifications.show({
        title: "Error",
        message: `Failed to download backup for restore: ${error}`,
        color: "red",
      });
    }
  };

  const handleRestoreSubmit = async (file: File) => {
    try {
      const response = await restoreBackupAsync(file, true);
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
              onClick={() => setRestoreModalOpened(true)}
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

      <FileUploadModal
        opened={restoreModalOpened}
        onClose={() => {
          setRestoreModalOpened(false);
          setSelectedBackupFile(null);
        }}
        onSubmit={handleRestoreSubmit}
        title="Restore Backup"
        initialFile={selectedBackupFile}
        uploadPrompt="Drag backup file here or click to select"
        uploadDescription="Upload a backup ZIP file to restore"
        warningTitle="Warning: Restore will replace all current data"
        warningMessage="Make sure you have a recent backup before proceeding. This action cannot be undone."
        requireConfirmation={true}
        confirmationLabel="I understand and want to overwrite existing data"
        submitLabel="Restore Backup"
        submitColor="orange"
      />
    </>
  );
}

export default Status;