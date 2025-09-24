import { useEffect, useState } from "react";
import { SimpleGrid } from "@mantine/core";

import { getSeries } from "../api/api";
import ItemCard from "../components/ItemCard/ItemCard";
import { type SeriesItem } from "../types/CardItems";


function Library() {

  const [series, setSeries] = useState<SeriesItem[]>([]);

  useEffect(() => {
    getSeries().then((data) => {
      setSeries(data);
    });
  }, []);

  return (
    <SimpleGrid
        type="container"
        cols={{ base: 2, '500px': 5, '1000px': 10 }}
        // spacing={{ base: 10, '300px': 'xl' }}
      >
        {series.map((seriesItem) => (
          <ItemCard item={seriesItem} />
        ))}
      </SimpleGrid>
  )
}

export default Library;
