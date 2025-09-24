// TODO: Implement API calls when backend is ready.

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
