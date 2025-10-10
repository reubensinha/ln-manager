import axios from 'axios';
import type { SearchSeriesResponse, SeriesGroupsResponse, PluginResponse, SeriesSourceResponse } from './ApiResponse';
import type { Book, Series } from '../api/ApiResponse';


// Get the current protocol and hostname from the browser's address bar
const protocol = window.location.protocol; // e.g., 'http:' or 'https:'
const hostname = window.location.hostname; // e.g., 'myapp.com' or 'localhost'

// Construct the API base URL with the different port
const apiPort = 8000; // Your API's port
const baseURL = `${protocol}//${hostname}:${apiPort}/api/v1`;

const api = axios.create({
  baseURL: baseURL,
});

export async function searchSeries(query: string, source: string): Promise<SearchSeriesResponse[]> {
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

export async function addSeries(source: string, external_id: string, series_group: string | null = null): Promise<{ success: boolean; message: string }> {
  try {
    const response = await api.post(`/add/series`, { source, external_id, series_group });
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


export async function getSeriesGroupById(id: string): Promise<SeriesGroupsResponse | null> {
  // Placeholder function to simulate fetching series groups from an API
  try {
    const response = await api.get(`/series-groups/${id}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching series group by ID:", error);
    return null;
  }
}

export async function getSeries() : Promise<Series[]> {
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

export async function getSeriesFromSource(source: string, external_id: string): Promise<SeriesSourceResponse | null> {
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
      routes: [
        {
          path: "/plugin/plugin1",
          component: "Plugin1",
        },
      ],
      navbarLinks: [
        {
          label: "Plugin 1 Link",
          icon: "TbGauge",
          link: "/plugin/plugin1",
        },
      ],
    },
  ];
}
