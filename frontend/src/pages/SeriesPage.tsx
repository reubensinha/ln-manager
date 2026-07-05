import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router";
import { Text, SimpleGrid, Tabs, Group, Button, Checkbox } from "@mantine/core";
import { TbRefresh } from "react-icons/tb";
import { useQueryClient } from "@tanstack/react-query";

import {
  useAddSeries,
  useSeries,
  useSeriesGroup,
  useSetBookDownloaded,
} from "../api/hooks/series";
import { queryKeys } from "../api/queryKeys";
import ItemCard from "../components/ItemCard/ItemCard";
import SeriesInfo from "../components/SeriesInfo";
import { type CardItem } from "../types/CardItems";

function SeriesPage() {
  const { groupID } = useParams<{ groupID: string }>();
  const queryClient = useQueryClient();

  const { data: seriesGroup } = useSeriesGroup(groupID);

  // Which series within the group is shown (tabs switch between sources).
  const [selectedSeriesId, setSelectedSeriesId] = useState<string | null>(null);
  const activeSeriesId = selectedSeriesId ?? seriesGroup?.main_series_id;
  const { data: series } = useSeries(activeSeriesId ?? undefined);

  const addSeriesMutation = useAddSeries();
  const setDownloadedMutation = useSetBookDownloaded(series?.id);

  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<string | null>("books");
  const [selectedBooks, setSelectedBooks] = useState<Set<string>>(new Set());
  const selectMode = selectedBooks.size > 0;

  const books: CardItem[] = useMemo(
    () =>
      series?.books?.map((item) => ({
        id: item.id,
        title: item.title,
        img_url: item.img_url,
        link: `/book/${item.id}`,
        in_library: true,
        nsfw_img: item.nsfw_img,
        downloaded: item.downloaded,
        monitored: item.monitored,
      })) ?? [],
    [series]
  );

  const chapters: CardItem[] = useMemo(
    () =>
      series?.chapters?.map((item) => ({
        id: item.id,
        title: item.title,
        img_url: undefined,
        link: `/chapter/${item.id}`,
        in_library: true,
        nsfw_img: false,
      })) ?? [],
    [series]
  );

  // Default to whichever tab has content once the series loads.
  useEffect(() => {
    if (books.length > 0) {
      setActiveTab("books");
    } else if (chapters.length > 0) {
      setActiveTab("chapters");
    }
  }, [books.length, chapters.length]);

  const handleRefresh = async () => {
    if (!series || !series.metadata_source) return;

    await addSeriesMutation.mutateAsync({
      sourceId: series.metadata_source.id,
      externalId: series.external_id,
      seriesGroup: seriesGroup?.id || "",
    });
    // Refresh this group + the currently shown series after a metadata re-fetch.
    if (groupID) {
      queryClient.invalidateQueries({ queryKey: queryKeys.seriesGroup(groupID) });
    }
    if (activeSeriesId) {
      queryClient.invalidateQueries({ queryKey: queryKeys.series(activeSeriesId) });
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

  const handleBulkAction = async (action: string) => {
    const downloaded = action === "add_to_library";
    if (action !== "add_to_library" && action !== "remove_from_library") {
      return;
    }

    setIsLoading(true);
    try {
      await Promise.all(
        Array.from(selectedBooks).map((bookId) =>
          setDownloadedMutation.mutateAsync({ bookId, downloaded })
        )
      );
    } finally {
      setIsLoading(false);
      setSelectedBooks(new Set());
    }
  };

  const isRefreshing = addSeriesMutation.isPending;

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
        onChange={(value) => setSelectedSeriesId(value)}
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
