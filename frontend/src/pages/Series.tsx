import { useEffect, useState } from "react";
import { Text, SimpleGrid, Divider } from "@mantine/core";
import { useParams } from "react-router";

import { getSeriesById, getSeriesGroupById } from "../api/api";
import ItemCard from "../components/ItemCard/ItemCard";
import SeriesInfo from "../components/SeriesInfo";
import {
  type SeriesGroupItem,
  type BookItem,
  type SeriesItem,
} from "../types/CardItems";

function Series() {
  const { groupID } = useParams<{ groupID: string }>();
  const [seriesGroup, setSeriesGroup] = useState<SeriesGroupItem | null>(null);
  const [series, setSeries] = useState<SeriesItem | null>(null);
  const [books, setBooks] = useState<BookItem[]>([]);

  useEffect(() => {
    if (groupID) {
      getSeriesGroupById(groupID).then((data) => {
        setSeriesGroup(data);
      });
    }
  }, [groupID]);

  useEffect(() => {
    if (seriesGroup) {
      getSeriesById(seriesGroup.series[0].id).then((data) => {
        const booksWithLinks = data.books.map((item) => ({
          ...item,
          link: `/book/${item.id}`,
        }));
        setSeries(data);
        setBooks(booksWithLinks);
      });
    }
  }, [seriesGroup]);

  if (!seriesGroup) {
    return <Text>Loading series group...</Text>;
  }

  if (!series) {
    return <Text>Loading series...</Text>;
  }

  return (
    <>
      {/* TODO Series Tabs */}
      <SeriesInfo series={series} />
      <Divider my="md" />
      <SimpleGrid
        type="container"
        cols={{ base: 2, "500px": 5, "1000px": 10 }}
        // spacing={{ base: 10, '300px': 'xl' }}
      >
        {books.map((bookItem) => (
          <ItemCard item={bookItem} />
        ))}
      </SimpleGrid>
    </>
  );
}

export default Series;
