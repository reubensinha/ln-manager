import { useEffect, useState } from "react";
import { useParams } from "react-router";
import { Text, SimpleGrid, Tabs, Group, Button, Checkbox } from "@mantine/core";
import { TbRefresh } from "react-icons/tb";

import {
  getSeriesById,
  getSeriesGroupById,
  addSeries,
  setBookDownloaded,
} from "../api/api";
import type { Series, SeriesGroupsResponse } from "../api/ApiResponse";
import ItemCard from "../components/ItemCard/ItemCard";
import SeriesInfo from "../components/SeriesInfo";
import { type CardItem } from "../types/CardItems";

function SeriesPage() {
  const { groupID } = useParams<{ groupID: string }>();
  const [seriesGroup, setSeriesGroup] = useState<SeriesGroupsResponse | null>(
    null
  );
  const [series, setSeries] = useState<Series | null>(null);
  const [books, setBooks] = useState<CardItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chapters, setChapters] = useState<CardItem[]>([]);
  const [activeTab, setActiveTab] = useState<string | null>("books");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedBooks, setSelectedBooks] = useState<Set<string>>(new Set());
  const selectMode = selectedBooks.size > 0;

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
            downloaded: item.downloaded,
            monitored: item.monitored,
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

  const handleRefresh = async () => {
    if (!series || !series.metadata_source) return;

    setIsRefreshing(true);
    try {
      await addSeries(
        series.metadata_source.id,
        series.external_id,
        seriesGroup?.id || ""
      );
      // After refreshing, re-fetch the series data
      if (groupID) {
        const updatedGroup = await getSeriesGroupById(groupID);
        setSeriesGroup(updatedGroup);
      }
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleBookSelect = (bookId: string) => {
    setSelectedBooks((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(bookId)) {
        newSet.delete(bookId);
      } else {
        newSet.add(bookId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedBooks.size === books.length) {
      setSelectedBooks(new Set());
    } else {
      setSelectedBooks(new Set(books.map((book) => book.id)));
    }
  };

  const setDownloaded = async (bookId: string, downloaded: boolean) => {
    try {
      await setBookDownloaded(bookId, downloaded);

      if (series) {
        const updatedSeries = await getSeriesById(series.id);
        if (updatedSeries) {
          const booksWithLinks =
            updatedSeries.books?.map((item) => ({
              id: item.id,
              title: item.title,
              img_url: item.img_url,
              link: `/book/${item.id}`,
              in_library: true,
              nsfw_img: item.nsfw_img,
              downloaded: item.downloaded,
              monitored: item.monitored,
            })) ?? [];

          setSeries(updatedSeries);
          setBooks(booksWithLinks);
        }
      }
    } catch (error) {
      console.error("Error setting download:", error);
    }
  };

  const handleBulkAction = async (action: string) => {
    switch (action) {
      case "add_to_library":
        setIsLoading(true);
        try {
          await Promise.all(
            Array.from(selectedBooks).map((bookId) => setDownloaded(bookId, true))
          );
        } finally {
          setIsLoading(false);
          setSelectedBooks(new Set());
        }
        break;
      case "remove_from_library":
        setIsLoading(true);
        try {
          await Promise.all(
            Array.from(selectedBooks).map((bookId) => setDownloaded(bookId, false))
          );
        } finally {
          setIsLoading(false);
          setSelectedBooks(new Set());
        }
        break;
      default:
        break;
    }
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
        <Group justify="space-between">
          <Tabs.List mb={"md"}>
            {seriesGroup.series?.map((seriesItem) => (
              <Tabs.Tab
                key={seriesItem.id}
                value={seriesItem.id}
                disabled={isRefreshing}
              >
                {seriesItem.metadata_source?.name || "Unknown Source"}
              </Tabs.Tab>
            ))}
          </Tabs.List>

          <Button
            mr={"xl"}
            onClick={handleRefresh}
            loading={isRefreshing}
            disabled={isRefreshing}
          >
            <TbRefresh
              style={{
                animation: isRefreshing ? "spin 1s linear infinite" : "none",
              }}
            />
          </Button>
        </Group>

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
              {isLoading && <Text>Updating...</Text>}
              {selectMode && (
                <Group justify="space-between" mb="md">
                  <Group>
                    <Button
                      variant={"filled"}
                      onClick={() => {
                        setSelectedBooks(new Set());
                      }}
                    >
                      {"Cancel Selection"}
                    </Button>

                    <>
                      <Checkbox
                        label="Select All"
                        checked={
                          selectedBooks.size === books.length &&
                          books.length > 0
                        }
                        indeterminate={
                          selectedBooks.size > 0 &&
                          selectedBooks.size < books.length
                        }
                        onChange={handleSelectAll}
                      />
                      <Text size="sm" c="dimmed">
                        {selectedBooks.size} selected
                      </Text>
                    </>
                  </Group>

                  <Group>
                    <Button onClick={() => handleBulkAction("add_to_library")}>
                      Add to Library
                    </Button>
                    <Button
                      onClick={() => handleBulkAction("remove_from_library")}
                    >
                      Remove from Library
                    </Button>
                  </Group>
                </Group>
              )}

              <SimpleGrid
                type="container"
                cols={{ base: 2, "500px": 5, "1000px": 10 }}
              >
                {books.map((bookItem) => (
                  <ItemCard
                    key={bookItem.id}
                    item={bookItem}
                    selectMode={selectMode}
                    selectable={true}
                    selected={selectedBooks.has(bookItem.id)}
                    onSelect={() => handleBookSelect(bookItem.id)}
                  />
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
