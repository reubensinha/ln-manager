import { SimpleGrid } from "@mantine/core";
import ItemCard from "../components/ItemCard/ItemCard";

import { getSeries } from "../components/api/series";
import { useEffect, useState } from "react";


type SeriesItem = {
  id: number;
  title: string;
  description: string;
  img_path: string;
};


function Library() {

  const [series, setSeries] = useState<SeriesItem[]>([]);

  useEffect(() => {
    let isMounted = true;

    getSeries().then((data) => {
      if (isMounted) {
        setSeries(data);
      }
    });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <SimpleGrid
        type="container"
        cols={{ base: 2, '500px': 5, '1000px': 10 }}
        // spacing={{ base: 10, '300px': 'xl' }}
      >
        {series.map((seriesItem) => (
          <ItemCard series={seriesItem} />
        ))}
      </SimpleGrid>
  )
}

export default Library;
