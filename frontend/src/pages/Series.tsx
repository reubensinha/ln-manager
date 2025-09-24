import { useEffect, useState } from "react";
import { Text, SimpleGrid, Divider } from "@mantine/core";
import { useParams } from "react-router";

import { getSeriesById } from "../api/api";
import ItemCard from "../components/ItemCard/ItemCard";
import SeriesHeader from "../components/SeriesHeader";
import { type BookItem, type SeriesItem } from "../types/CardItems";

function Series() {
  const { id } = useParams<{ id: string }>();
  const [series, setSeries] = useState<SeriesItem | null>(null);
  const [books, setBooks] = useState<BookItem[]>([]);

  useEffect(() => {
    if (id) {
      getSeriesById(id).then((data) => {
        const booksWithLinks = data.books.map((item) => ({
          ...item,
          link: `/book/${item.id}`,
        }));
        setSeries(data);
        setBooks(booksWithLinks);
      });
    }
  }, [id]);

  // series = getSeriesById(id);
  // books = series.books.map((item) => ({
  //     ...item,
  //     link: `/book/${item.id}`,
  //   }));

  if (!series) {
    return <Text>Loading...</Text>;
  }

  return (
    <>
      <SeriesHeader series={series} />
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
