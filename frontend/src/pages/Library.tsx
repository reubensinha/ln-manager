import { SimpleGrid, Center, Loader } from "@mantine/core";

import { useSeriesGroups } from "../api/hooks/series";
import ItemCard from "../components/ItemCard/ItemCard";
import { type CardItem } from "../types/CardItems";

function Library() {
  const { data: seriesGroups, isLoading } = useSeriesGroups();

  if (isLoading) {
    return (
      <Center mt="xl">
        <Loader />
      </Center>
    );
  }

  const series: CardItem[] = (seriesGroups ?? []).map((item) => ({
    id: item.id,
    title: item.title,
    img_url: item.img_url,
    link: `/series/${item.id}`,
    in_library: true,
    nsfw_img: item.nsfw_img,
    downloaded: item.download_status,
    monitored: item.monitored,
  }));

  return (
    <SimpleGrid type="container" cols={{ base: 2, "500px": 5, "1000px": 8 }}>
      {series.map((seriesItem) => (
        <ItemCard key={seriesItem.id} item={seriesItem} />
      ))}
    </SimpleGrid>
  );
}

export default Library;
