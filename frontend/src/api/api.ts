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
} from "./ApiResponse";

// Get the current protocol and hostname from the browser's address bar

// Construct the API base URL with the different port
const baseURL = `/api/v1`;

const api = axios.create({
  baseURL: baseURL,
});

export async function searchSeries(
  query: string,
  source: string
): Promise<SearchSeriesResponse[]> {
  try {
    const response = await api.get(`/search`, {
      params: { query, source },
    });
    return response.data;
  } catch (error) {
    console.error("Error searching series:", error);
    return [];
  }
}

export async function addSeries(
  source: string,
  external_id: string,
  series_group: string | null = null
): Promise<{ success: boolean; message: string }> {
  try {
    const response = await api.post(`/add/series`, {
      source,
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
  source: string,
  external_id: string
): Promise<SeriesSourceResponse | null> {
  // Placeholder function to simulate fetching series data from an external source
  try {
    const response = await api.get(`/series_details/${source}`, {
      params: { external_id },
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
  return [
    {
      id: "RanobeDB",
      name: "RanobeDB",
      type: "metadata",
      version: "1.0.0",
      description: "Plugin to fetch metadata from RanobeDB",
    },
    {
      id: "plugin1",
      name: "Plugin 1",
      type: "generic",
      version: "0.1.0",
    },
  ];
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
