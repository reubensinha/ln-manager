// TODO: Implement API calls when backend is ready.
import axios from 'axios';
import type { searchSeriesResponse, SeriesGroupsResponse } from '../types/ApiResponse';


// Get the current protocol and hostname from the browser's address bar
const protocol = window.location.protocol; // e.g., 'http:' or 'https:'
const hostname = window.location.hostname; // e.g., 'myapp.com' or 'localhost'

// Construct the API base URL with the different port
const apiPort = 8000; // Your API's port
const baseURL = `${protocol}//${hostname}:${apiPort}`;

const api = axios.create({
  baseURL: baseURL,
});

export async function searchSeries(query: string, source: string): Promise<searchSeriesResponse[]> {
  try {
    const response = await api.get(`/api/v1/search`, {
      params: { query, source },  
    });
    return response.data;
  } catch (error) {
    console.error("Error searching series:", error);
    return [];
  }
}

export async function getSeriesGroups(): Promise<SeriesGroupsResponse[]> {
  // Placeholder function to simulate fetching series groups from an API
  return [
    {
      id: "1",
      title: "Series Group 1",
      img_url: "/test_img/32510.jpg",
      series: [
        {
          id: "1",
          source: "ranobeDB",
        },
        {
          id: "2",
          source: "MAL",
        },
      ],
    },
    {
      id: "2",
      title: "Series Group 2",
      img_url: "/test_img/32510.jpg",
      series: [
        {
          id: "3",
          source: "ranobeDB",
        },
        {
          id: "4",
          source: "MAL",
        },
      ],
    },
  ];
}

export async function getSeriesGroupById(id: string) {
  // Placeholder function to simulate fetching series groups from an API

  if (id === "1") {
    return {
      id: "1",
      title: "Series Group 1",
      img_url: "/test_img/32510.jpg",
      series: [
        {
          id: "1",
          source: "ranobeDB",
        },
        {
          id: "2",
          source: "MAL",
        },
      ],
    };
  } else {
    return {
      id: "2",
      title: "Series Group 2",
      img_url: "/test_img/32510.jpg",
      series: [
        {
          id: "3",
          source: "ranobeDB",
        },
        {
          id: "4",
          source: "MAL",
        },
      ],
    };
  }
}

export async function getSeries() {
  // Placeholder function to simulate fetching series data from an API
  return [
    {
      id: "1",
      title: "Series 1",
      description: "Description of Series 1",
      img_url: "/test_img/32510.jpg",
    },
    {
      id: "2",
      title: "Series 2",
      description: "Description of Series 2",
      img_url: "/test_img/32510.jpg",
    },
    {
      id: "3",
      title: "Series 3",
      description: "Description of Series 3",
      img_url: "/test_img/32510.jpg",
    },
    {
      id: "4",
      title: "Series 4",
      description: "Description of Series 4",
      img_url: "/test_img/32510.jpg",
    },
  ];
}

export async function getSeriesById(id: string) {
  // Placeholder function to simulate fetching a single series by ID from an API
  return {
    id,
    title: `Series ${id}`,
    description: `Description of Series ${id}`,
    img_url: "/test_img/32510.jpg",
    books: [
      {
        id: "1",
        title: "Book 1",
        description: "Description of Book 1",
        img_url: "/test_img/32510.jpg",
      },
      {
        id: "2",
        title: "Book 2",
        description: "Description of Book 2",
        img_url: "/test_img/32510.jpg",
      },
    ],
  };
}

export async function getBookByID(id: string) {
  // Placeholder function to simulate fetching a single book by ID from an API
  return {
    id,
    title: `Book ${id}`,
    description: `Description of Book ${id}`,
    img_url: "/test_img/32510.jpg",
  };
}

export async function getPlugins() {
  // Placeholder function to simulate fetching plugins from an API
  return [
    {
      id: "plugin1",
      name: "Plugin 1",
      routes: [
        {
          path: "/plugin1",
          component: "Plugin1",
        },
      ],
      navbarLinks: [
        {
          label: "Plugin 1 Link",
          icon: "TbGauge",
          link: "/plugin1",
        },
      ],
    },
  ];
}
