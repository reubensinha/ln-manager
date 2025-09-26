// TODO: Implement API calls when backend is ready.

export async function getSeriesGroups() {
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
