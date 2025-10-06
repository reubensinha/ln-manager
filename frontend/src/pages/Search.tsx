import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

import type {
  searchSeriesResponse,
  PluginResponse,
} from "../types/ApiResponse";
import { searchSeries, getPlugins } from "../api/api";
import { Group, TextInput, Select, Button } from "@mantine/core";

function Search() {
  const { source, query } = useParams<{ source: string; query?: string }>();
  const [results, setResults] = useState<searchSeriesResponse[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>(query || "");
  const [value, setValue] = useState<string | null>(source || null);
  const [plugins, setPlugins] = useState<PluginResponse[]>([]);

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

  console.log(`results: ${JSON.stringify(results)}`);
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
        />

        <Button
          size="md"
          component={Link}
          to={
            searchQuery.trim().length > 0
              ? `/search/${value}/${encodeURIComponent(searchQuery.trim())}`
              : `/search/${value}`
          }
        >
          Search
        </Button>
      </Group>

      <div>
        <h1>Search</h1>
        <p>Search for books, authors, and more</p>
      </div>
    </>
  );
}

export default Search;
