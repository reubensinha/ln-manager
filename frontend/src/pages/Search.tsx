import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router";
import { Group, TextInput, Select, Button, SimpleGrid } from "@mantine/core";

import type { SearchSeriesResponse, PluginResponse } from "../api/ApiResponse";
import type { CardItem } from "../types/CardItems";
import { searchSeries, getPlugins } from "../api/api";
import AddSeriesModal from "../components/AddSeriesModal";
import ItemCard from "../components/ItemCard/ItemCard";
import { useDisclosure } from "@mantine/hooks";

function Search() {
  const { source, query } = useParams<{ source: string; query?: string }>();
  const navigate = useNavigate();
  const [results, setResults] = useState<SearchSeriesResponse[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>(query || "");
  const [value, setValue] = useState<string | null>(source || null);
  const [plugins, setPlugins] = useState<PluginResponse[]>([]);
  const [opened, { open, close }] = useDisclosure(false);
  const [selectedItem, setSelectedItem] = useState<SearchSeriesResponse | null>(
    null
  );

  useEffect(() => {
    // Perform search based on source and query
    if (query && source) {
      searchSeries(query, source).then((data) => setResults(data));
    }
  }, [source, query]);

  useEffect(() => {
    getPlugins().then((data) => {
      const metadataPlugins = data.filter(
        (plugin) => plugin.type === "metadata"
      );
      setPlugins(metadataPlugins);
    });
  }, []);

  const handleCardClick = (item: SearchSeriesResponse) => {
    setSelectedItem(item);
    open();
  };

  const handleSearch = () => {
    if (value) {
      const trimmedQuery = searchQuery.trim();
      if (trimmedQuery.length > 0) {
        navigate(`/search/${value}/${encodeURIComponent(trimmedQuery)}`);
      }
    }
  };

  return (
    <>
      <Group mb="md" align="flex-end" wrap="nowrap">
        <Select
          value={value}
          onChange={setValue}
          size="md"
          label="Metadata Source"
          description={`Search for series on ${value}`}
          variant="default"
          // error="Error: Unknown metadata source"
          placeholder="Select placeholder"
          autoSelectOnBlur
          data={plugins.map((plugin) => plugin.name)}
          defaultSearchValue={source}
          defaultValue={source}
          allowDeselect={false}
        />

        <TextInput
          style={{ flex: 1 }}
          label="Search"
          description="What are you looking for?"
          size="md"
          placeholder={query ? query : "Search..."}
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.currentTarget.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              handleSearch();
            }
          }}
        />

        <Button
          size="md"
          onClick={handleSearch}
        >
          Search
        </Button>
      </Group>

      {source && selectedItem && (
        <AddSeriesModal
          item={selectedItem}
          source={source}
          open={opened}
          onClose={close}
        />
      )}

      <SimpleGrid type="container" cols={{ base: 2, "500px": 5, "1000px": 8 }}>
        {results.map((result) => {
          const cardItem: CardItem = {
            id: result.external_id,
            title: result.title,
            img_url: result.img_url ?? "",
            in_library: false,
          };
          return (
            <Group
              key={result.external_id}
              onClick={() => handleCardClick(result)}
            >
              <ItemCard key={cardItem.title} item={cardItem} />
            </Group>
          );
        })}
      </SimpleGrid>
    </>
  );
}

export default Search;
