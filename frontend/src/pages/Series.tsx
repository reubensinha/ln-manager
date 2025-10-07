import { useEffect, useState } from "react";
import { Text, SimpleGrid, Divider, Tabs } from "@mantine/core";
import { useParams } from "react-router";

import { getSeriesById, getSeriesGroupById } from "../api/api";
import ItemCard from "../components/ItemCard/ItemCard";
import SeriesInfo from "../components/SeriesInfo";
import {
  type SeriesGroupItem,
  type CardItem,
} from "../types/CardItems";
import { type Series } from "../api/ApiResponse";

function Series() {
  const { groupID } = useParams<{ groupID: string }>();
  const [seriesGroup, setSeriesGroup] = useState<SeriesGroupItem | null>(null);
  const [series, setSeries] = useState<Series | null>(null);
  const [books, setBooks] = useState<CardItem[]>([]);

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
        const booksWithLinks = data?.books?.map((item) => ({
          ...item,
          link: `/book/${item.id}`,
        })) ?? [];
        setSeries(data);
        setBooks(booksWithLinks);
      });
    }
  }, [seriesGroup]);

  const handleTabChange = (seriesId: string) => {
    getSeriesById(seriesId).then((data) => {
      const booksWithLinks = data?.books?.map((item) => ({
        ...item,
        link: `/book/${item.id}`,
      })) ?? [];
      setSeries(data);
      setBooks(booksWithLinks);
    });
  };

  if (!seriesGroup) {
    return <Text>Loading series group...</Text>;
  }

  if (!series) {
    return <Text>Loading series...</Text>;
  }

  return (
    <>
      <Tabs
        defaultValue={seriesGroup.series[0].id}
        onChange={(value) => handleTabChange(value ?? "")}
      >
        <Tabs.List mb={"md"}>
          {seriesGroup.series.map((seriesItem) => (
            <Tabs.Tab key={seriesItem.id} value={seriesItem.id}>
              {seriesItem.source}
            </Tabs.Tab>
          ))}
        </Tabs.List>

        <Tabs.Panel value={series.id}>
          <SeriesInfo series={series} />
          <Divider my="md" />
          <SimpleGrid
            type="container"
            cols={{ base: 2, "500px": 5, "1000px": 10 }}
            // spacing={{ base: 10, '300px': 'xl' }}
          >
            {books.map((bookItem) => (
              <ItemCard key={bookItem.id} item={bookItem} />
            ))}
          </SimpleGrid>
        </Tabs.Panel>
      </Tabs>
    </>
  );
}

export default Series;
