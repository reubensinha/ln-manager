import { useEffect, useState } from "react";
import { SimpleGrid } from "@mantine/core";

import { getSeriesGroups } from "../api/api";
import ItemCard from "../components/ItemCard/ItemCard";
import { type SeriesGroupItem } from "../types/CardItems";

function Library() {
  const [series, setSeries] = useState<SeriesGroupItem[]>([]);

  useEffect(() => {
    getSeriesGroups().then((data) => {
      const seriesGroupsWithLinks = data.map((item) => ({
        ...item,
        link: `/series/${item.id}`,
      }));
      setSeries(seriesGroupsWithLinks);
    });
  }, []);

  return (
    <SimpleGrid
      type="container"
      cols={{ base: 2, "500px": 5, "1000px": 8 }}
    >
      {series.map((seriesItem) => (
        <ItemCard key={seriesItem.id} item={seriesItem} />
      ))}
    </SimpleGrid>
  );
}

export default Library;
