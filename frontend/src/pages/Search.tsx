import { useState } from "react";
import { useParams, useNavigate } from "react-router";
import { Group, TextInput, Select, Button, SimpleGrid } from "@mantine/core";

import type { SearchSeriesResponse } from "../api/ApiResponse";
import type { CardItem } from "../types/CardItems";
import { useMetadataSources, useSearchSeries } from "../api/hooks/series";
import AddSeriesModal from "../components/AddSeriesModal";
import ItemCard from "../components/ItemCard/ItemCard";
import { useDisclosure } from "@mantine/hooks";

function Search() {
  const { source, query } = useParams<{ source: string; query?: string }>();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState<string>(query || "");
  const [value, setValue] = useState<string | null>(source || null);
  const [opened, { open, close }] = useDisclosure(false);
  const [selectedItem, setSelectedItem] = useState<SearchSeriesResponse | null>(
    null
  );

  const { data: allSources = [] } = useMetadataSources();
  const metadataSources = allSources.filter((s) => s.enabled);
  const sourceObj = metadataSources.find((s) => s.name === source);

  const { data: results = [] } = useSearchSeries(source, query, sourceObj?.id);

  const handleCardClick = (item: SearchSeriesResponse) => {
    setSelectedItem(item);
    open();
  };

  const handleSearch = () => {
    if (value) {
      const trimmedQuery = searchQuery.trim();
      if (trimmedQuery.length > 0) {
        // Use source name in URL for readability
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
          description={value ? `Search for series on ${value}` : "Select a metadata source"}
          variant="default"
          placeholder="Select metadata source"
          autoSelectOnBlur
          data={metadataSources.map((source) => ({
            value: source.name,
            label: source.name
          }))}
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
          sourceId={metadataSources.find(s => s.name === source)?.id || source}
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
