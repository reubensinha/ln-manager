import axios from "axios";
import type {
  Book,
  Series,
  SearchSeriesResponse,
  SeriesGroupsResponse,
  PluginResponse,
  SeriesSourceResponse,
  Release,
  Notification,
  MetadataSource,
  PluginCapability,
  BackupResponse,
  BackupListResponse,
  TaskResponse,
  TaskStatusResponse,
  RestoreResponse,
  Indexer,
  DownloadClient,
  IndexerResult,
} from "./ApiResponse";

// Get the current protocol and hostname from the browser's address bar

// Construct the API base URL with the different port
const baseURL = `/api/v1`;

const api = axios.create({
  baseURL: baseURL,
});

export async function searchSeries(
  query: string,
  sourceId: string
): Promise<SearchSeriesResponse[]> {
  try {
    const response = await api.get(`/search`, {
      params: { query, source_id: sourceId },
    });
    return response.data;
  } catch (error) {
    console.error("Error searching series:", error);
    return [];
  }
}

export async function addSeries(
  sourceId: string,
  external_id: string,
  series_group: string | null = null
): Promise<{ success: boolean; message: string }> {
  try {
    const response = await api.post(`/add/series`, {
      source_id: sourceId,
      external_id,
      series_group,
    });
    return response.data;
  } catch (error) {
    console.error("Error adding series:", error);
    return { success: false, message: "Failed to add series" };
  }
}

export async function getSeriesGroups(): Promise<SeriesGroupsResponse[]> {
  // Placeholder function to simulate fetching series groups from an API
  try {
    const response = await api.get(`/series-groups`);
    return response.data;
  } catch (error) {
    console.error("Error fetching series groups:", error);
    return [];
  }
}

export async function getSeriesGroupById(
  id: string
): Promise<SeriesGroupsResponse | null> {
  // Placeholder function to simulate fetching series groups from an API
  try {
    const response = await api.get(`/series-groups/${id}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching series group by ID:", error);
    return null;
  }
}

export async function getSeries(): Promise<Series[]> {
  // Placeholder function to simulate fetching series data from an API
  try {
    const response = await api.get(`/series`);
    return response.data;
  } catch (error) {
    console.error("Error fetching series:", error);
    return [];
  }
}

export async function getSeriesById(id: string): Promise<Series | null> {
  // Placeholder function to simulate fetching a single series by ID from an API
  try {
    const response = await api.get(`/series/${id}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching series by ID:", error);
    return null;
  }
}

export async function getSeriesFromSource(
  sourceId: string,
  external_id: string
): Promise<SeriesSourceResponse | null> {
  // Placeholder function to simulate fetching series data from an external source
  try {
    const response = await api.get(`/series_details`, {
      params: { source_id: sourceId, external_id },
    });
    return response.data;
  } catch (error) {
    console.error("Error searching series:", error);
    return null;
  }
}

export async function getBookByID(id: string): Promise<Book | null> {
  // Placeholder function to simulate fetching a single book by ID from an API
  try {
    const response = await api.get(`/books/${id}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching book by ID:", error);
    return null;
  }
}

export async function getReleases(): Promise<Release[]> {
  try {
    const response = await api.get(`/releases`);
    return response.data;
  } catch (error) {
    console.error("Error fetching releases:", error);
    return [];
  }
}

export async function toggleBookDownloaded(
  bookId: string
): Promise<{ status: string } | null> {
  try {
    const response = await api.patch(`/toggle-book-downloaded/${bookId}`);
    return response.data;
  } catch (error) {
    console.error("Error toggling book downloaded status:", error);
    return null;
  }
}

export async function setBookDownloaded(
  bookId: string,
  downloaded: boolean
): Promise<{ status: string } | null> {
  try {
    const response = await api.patch(`/set-book-downloaded/${bookId}`, null, { params: { downloaded } });
    return response.data;
  } catch (error) {
    console.error("Error setting book downloaded status:", error);
    return null;
  }
}

export async function toggleBookMonitored(
  bookId: string
): Promise<{ status: string } | null> {
  try {
    const response = await api.patch(`/toggle-book-monitored/${bookId}`);
    return response.data;
  } catch (error) {
    console.error("Error toggling book monitored status:", error);
    return null;
  }
}

export async function toggleSeriesDownloaded(
  seriesId: string
): Promise<{ status: string } | null> {
  try {
    const response = await api.patch(`/toggle-series-downloaded/${seriesId}`);
    return response.data;
  } catch (error) {
    console.error("Error toggling series downloaded status:", error);
    return null;
  }
}

export async function toggleSeriesMonitored(
  seriesId: string
): Promise<{ status: string } | null> {
  try {
    const response = await api.patch(`/toggle-series-monitored/${seriesId}`);
    return response.data;
  } catch (error) {
    console.error("Error toggling series monitored status:", error);
    return null;
  }
}

export async function getPlugins(): Promise<PluginResponse[]> {
  // Placeholder function to simulate fetching plugins from an API
  try {
    const response = await api.get(`/plugins`);
    return response.data;
  } catch (error) {
    console.error("Error fetching plugins:", error);
    return [];
  }
}

export async function getPluginCapabilities(): Promise<{
  has_indexers: boolean;
  has_download_clients: boolean;
  has_metadata_sources: boolean;
}> {
  try {
    const response = await api.get(`/plugin-capabilities`);
    return response.data;
  } catch (error) {
    console.error("Error fetching plugin capabilities:", error);
    return {
      has_indexers: false,
      has_download_clients: false,
      has_metadata_sources: false,
    };
  }
}

export async function uploadPlugin(
  file: File
): Promise<{ success: boolean; message: string }> {
  try {
    const formData = new FormData();
    formData.append("plugin", file);

    const response = await api.post(`/plugins/install`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error uploading plugin:", error);
    return { success: false, message: "Failed to upload plugin." };
  }
}

export async function deletePlugin(
  pluginId: string
): Promise<{ success: boolean; message: string }> {
  try {
    const response = await api.delete(`/plugins/${pluginId}`);
    return response.data;
  } catch (error) {
    console.error("Error deleting plugin:", error);
    return { success: false, message: "Failed to delete plugin." };
  }
}

export async function getNotifications(): Promise<Notification[]> {
  try {
    const response = await api.get(`/system/notifications`);
    return response.data;
  } catch (error) {
    console.error("Error fetching notifications:", error);
    return [];
  }
}

export async function restartBackend(): Promise<{
  success: boolean;
  message: string;
}> {
  try {
    const response = await api.post(`/restart`);
    return response.data;
  } catch (error) {
    console.error("Error restarting backend:", error);
    return { success: false, message: "Failed to restart backend." };
  }
}

export async function getMetadataSources(): Promise<MetadataSource[]> {
  try {
    const response = await api.get(`/sources`);
    return response.data;
  } catch (error) {
    console.error("Error fetching metadata sources:", error);
    return [];
  }
}

export async function getPluginSources(pluginName: string): Promise<PluginCapability[]> {
  try {
    const response = await api.get(`/plugins/${pluginName}/sources`);
    return response.data;
  } catch (error) {
    console.error("Error fetching plugin sources:", error);
    return [];
  }
}

export async function getPluginIndexers(pluginName: string): Promise<PluginCapability[]> {
  try {
    const response = await api.get(`/plugins/${pluginName}/indexers`);
    return response.data;
  } catch (error) {
    console.error("Error fetching plugin indexers:", error);
    return [];
  }
}

export async function getPluginClients(pluginName: string): Promise<PluginCapability[]> {
  try {
    const response = await api.get(`/plugins/${pluginName}/clients`);
    return response.data;
  } catch (error) {
    console.error("Error fetching plugin clients:", error);
    return [];
  }
}

export async function getIndexers(): Promise<Indexer[]> {
  try {
    const response = await api.get(`/indexers`);
    return response.data;
  } catch (error) {
    console.error("Error fetching indexers:", error);
    return [];
  }
}

export async function createIndexer(
  indexer: Omit<Indexer, "id">
): Promise<{ success: boolean; indexer?: Indexer; message?: string }> {
  try {
    const response = await api.post(`/indexers`, indexer);
    return { success: true, indexer: response.data };
  } catch (error) {
    console.error("Error creating indexer:", error);
    return { success: false, message: "Failed to create indexer" };
  }
}

export async function updateIndexer(
  indexerId: string,
  indexer: Partial<Omit<Indexer, "id">>
): Promise<{ success: boolean; indexer?: Indexer; message?: string }> {
  try {
    const response = await api.patch(`/indexers/${indexerId}`, indexer);
    return { success: true, indexer: response.data };
  } catch (error) {
    console.error("Error updating indexer:", error);
    return { success: false, message: "Failed to update indexer" };
  }
}

export async function deleteIndexer(
  indexerId: string
): Promise<{ success: boolean; message: string }> {
  try {
    const response = await api.delete(`/indexers/${indexerId}`);
    return response.data;
  } catch (error) {
    console.error("Error deleting indexer:", error);
    return { success: false, message: "Failed to delete indexer" };
  }
}

export async function testIndexerConnection(
  config: { plugin_id?: string; config: Record<string, unknown> }
): Promise<{ success: boolean; message: string }> {
  try {
    const response = await api.post(`/indexers/test-connection`, config);
    return response.data;
  } catch (error) {
    console.error("Error testing indexer connection:", error);
    return { success: false, message: "Failed to test connection" };
  }
}

export async function getDownloadClients(): Promise<DownloadClient[]> {
  try {
    const response = await api.get(`/download-clients`);
    return response.data;
  } catch (error) {
    console.error("Error fetching download clients:", error);
    return [];
  }
}

// Backup & Restore API

export async function createBackup(): Promise<BackupResponse> {
  try {
    const response = await api.post(`/system/backup`);
    return response.data;
  } catch (error) {
    console.error("Error creating backup:", error);
    return { success: false, message: "Failed to create backup" };
  }
}

export async function createBackupAsync(): Promise<TaskResponse> {
  try {
    const response = await api.post(`/system/backup/async`);
    return response.data;
  } catch (error) {
    console.error("Error creating async backup:", error);
    return { success: false, task_id: "", message: "Failed to start backup task" };
  }
}

export async function listBackups(): Promise<BackupListResponse> {
  try {
    const response = await api.get(`/system/backups`);
    return response.data;
  } catch (error) {
    console.error("Error listing backups:", error);
    return { success: false, backups: [], count: 0 };
  }
}

export async function downloadBackup(filename: string): Promise<Blob | null> {
  try {
    const response = await api.get(`/system/backup/download/${filename}`, {
      responseType: "blob",
    });
    return response.data;
  } catch (error) {
    console.error("Error downloading backup:", error);
    return null;
  }
}

export async function deleteBackup(filename: string): Promise<{ success: boolean; message: string }> {
  try {
    const response = await api.delete(`/system/backup/${filename}`);
    return response.data;
  } catch (error) {
    console.error("Error deleting backup:", error);
    return { success: false, message: "Failed to delete backup" };
  }
}

export async function restoreBackup(
  file: File,
  overwrite: boolean = false
): Promise<RestoreResponse> {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post(`/system/restore`, formData, {
      params: { overwrite },
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error restoring backup:", error);
    return { success: false, message: "Failed to restore backup" };
  }
}

export async function restoreBackupAsync(
  file: File,
  overwrite: boolean = false
): Promise<TaskResponse> {
  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post(`/system/restore/async`, formData, {
      params: { overwrite },
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error restoring backup async:", error);
    return { success: false, task_id: "", message: "Failed to start restore task" };
  }
}

export async function getTaskStatus(taskId: string): Promise<TaskStatusResponse | null> {
  try {
    const response = await api.get(`/system/task/${taskId}`);
    return response.data;
  } catch (error) {
    console.error("Error getting task status:", error);
    return null;
  }
}

export async function clearTask(taskId: string): Promise<{ success: boolean; message: string }> {
  try {
    const response = await api.delete(`/system/task/${taskId}`);
    return response.data;
  } catch (error) {
    console.error("Error clearing task:", error);
    return { success: false, message: "Failed to clear task" };
  }
}

export async function searchIndexers(query: string): Promise<IndexerResult[]> {
  try {
    const response = await api.get(`/indexers/search`, {
      params: { query }
    });
    return response.data;
  } catch (error) {
    console.error("Error searching indexers:", error);
    return [];
  }
}
