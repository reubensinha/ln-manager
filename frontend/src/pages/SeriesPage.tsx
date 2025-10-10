import { useEffect, useState } from "react";
import { Text, SimpleGrid, Tabs } from "@mantine/core";
import { useParams } from "react-router";

import { getSeriesById, getSeriesGroupById } from "../api/api";
import ItemCard from "../components/ItemCard/ItemCard";
import SeriesInfo from "../components/SeriesInfo";
import { type CardItem } from "../types/CardItems";
import type { Series, SeriesGroupsResponse } from "../api/ApiResponse";

function SeriesPage() {
  const { groupID } = useParams<{ groupID: string }>();
  const [seriesGroup, setSeriesGroup] = useState<SeriesGroupsResponse | null>(
    null
  );
  const [series, setSeries] = useState<Series | null>(null);
  const [books, setBooks] = useState<CardItem[]>([]);
  const [chapters, setChapters] = useState<CardItem[]>([]);
  const [activeTab, setActiveTab] = useState<string | null>("books");

  useEffect(() => {
    if (groupID) {
      getSeriesGroupById(groupID).then((data) => {
        setSeriesGroup(data);
      });
    }
  }, [groupID]);

  useEffect(() => {
    if (seriesGroup) {
      getSeriesById(seriesGroup.main_series_id).then((data) => {
        const booksWithLinks =
          data?.books?.map((item) => ({
            id: item.id,
            title: item.title,
            img_url: item.img_url,
            link: `/book/${item.id}`,
            in_library: true,
            nsfw_img: item.nsfw_img,
          })) ?? [];

        const chaptersWithLinks =
          data?.chapters?.map((item) => ({
            id: item.id,
            title: item.title,
            img_url: undefined,
            link: `/chapter/${item.id}`,
            in_library: true,
            nsfw_img: false,
          })) ?? [];

        setSeries(data);
        setChapters(chaptersWithLinks);
        setBooks(booksWithLinks);

        if (booksWithLinks.length > 0) {
          setActiveTab("books");
        } else if (chaptersWithLinks.length > 0) {
          setActiveTab("chapters");
        }
      });
    }
  }, [seriesGroup]);

  const handleSeriesTabChange = (seriesId: string) => {
    getSeriesById(seriesId).then((data) => {
      const booksWithLinks =
        data?.books?.map((item) => ({
          id: item.id,
          title: item.title,
          img_url: item.img_url,
          link: `/book/${item.id}`,
          in_library: true,
          nsfw_img: item.nsfw_img,
        })) ?? [];

      const chaptersWithLinks =
        data?.chapters?.map((item) => ({
          id: item.id,
          title: item.title,
          img_url: undefined,
          link: `/chapter/${item.id}`,
          in_library: true,
          nsfw_img: false,
        })) ?? [];

      setSeries(data);
      setBooks(booksWithLinks);
      setChapters(chaptersWithLinks);

      if (booksWithLinks.length > 0) {
        setActiveTab("books");
      } else if (chaptersWithLinks.length > 0) {
        setActiveTab("chapters");
      }
    });
  };

  if (!seriesGroup) {
    return <Text>Loading series...</Text>;
  }

  if (!series) {
    return <Text>Loading series...</Text>;
  }

  return (
    <>
      <Tabs
        defaultValue={seriesGroup.main_series_id}
        onChange={(value) => handleSeriesTabChange(value ?? "")}
      >
        <Tabs.List mb={"md"}>
          {seriesGroup.series?.map((seriesItem) => (
            <Tabs.Tab key={seriesItem.id} value={seriesItem.id}>
              {seriesItem.plugin.name}
            </Tabs.Tab>
          ))}
        </Tabs.List>

        <Tabs.Panel value={series.id}>
          <SeriesInfo series={series} />

          {books.length === 0 && chapters.length === 0 && (
            <Text mt="md">No books or chapters available.</Text>
          )}

          <Tabs value={activeTab} onChange={setActiveTab}>
            <Tabs.List mt={"md"} mb={"md"}>
              {books.length > 0 && (
                <Tabs.Tab key="books" value="books">
                  Books
                </Tabs.Tab>
              )}
              {chapters.length > 0 && (
                <Tabs.Tab key="chapters" value="chapters">
                  Chapters
                </Tabs.Tab>
              )}
            </Tabs.List>

            <Tabs.Panel value="books">
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

            <Tabs.Panel value="chapters">
              <Text>TODO: Implement chapters tab: {chapters.length}</Text>
            </Tabs.Panel>
          </Tabs>
        </Tabs.Panel>
      </Tabs>
    </>
  );
}

export default SeriesPage;
