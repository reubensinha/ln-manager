import { useMemo, useState } from "react";
import { DataTable } from "mantine-datatable";
import type { DataTableSortStatus } from "mantine-datatable";
import {
  Group,
  Text,
  Badge,
  Tooltip,
  ActionIcon,
  TextInput,
  NumberInput,
  Stack,
  Box,
  Button,
} from "@mantine/core";
import { TbDownload, TbAlertCircle, TbSearch } from "react-icons/tb";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import type { IndexerResult } from "../../api/ApiResponse";

dayjs.extend(relativeTime);

interface IndexerResultTableProps {
  results: IndexerResult[];
  loading?: boolean;
  onDownload?: (result: IndexerResult) => void;
}

const PAGE_SIZE = 25;

export function IndexerResultTable({
  results,
  loading = false,
  onDownload,
}: IndexerResultTableProps) {
  const [page, setPage] = useState(1);
  const [sortStatus, setSortStatus] = useState<DataTableSortStatus<IndexerResult>>({
    columnAccessor: "pub_date",
    direction: "desc",
  });
  const [indexerFilter, setIndexerFilter] = useState("");
  const [minScore, setMinScore] = useState<number | string>("");

  // Filter and sort results
  const processedResults = useMemo(() => {
    let filtered = results;

    // Apply indexer name filter
    if (indexerFilter) {
      filtered = filtered.filter((r) =>
        r.indexer_name?.toLowerCase().includes(indexerFilter.toLowerCase())
      );
    }

    // Apply minimum score filter
    if (minScore !== "" && typeof minScore === "number") {
      filtered = filtered.filter((r) => (r.score ?? 0) >= minScore);
    }

    // Sort results
    const sorted = [...filtered].sort((a, b) => {
      const accessor = sortStatus.columnAccessor as keyof IndexerResult;
      let aValue = a[accessor];
      let bValue = b[accessor];

      // Handle undefined/null values
      if (aValue === undefined || aValue === null) return 1;
      if (bValue === undefined || bValue === null) return -1;

      // Handle different data types
      if (accessor === "pub_date") {
        aValue = new Date(aValue as string).getTime();
        bValue = new Date(bValue as string).getTime();
      }

      if (typeof aValue === "number" && typeof bValue === "number") {
        return sortStatus.direction === "asc" ? aValue - bValue : bValue - aValue;
      }

      const aString = String(aValue).toLowerCase();
      const bString = String(bValue).toLowerCase();

      if (sortStatus.direction === "asc") {
        return aString.localeCompare(bString);
      }
      return bString.localeCompare(aString);
    });

    return sorted;
  }, [results, indexerFilter, minScore, sortStatus]);

  // Paginate results
  const paginatedResults = useMemo(() => {
    const from = (page - 1) * PAGE_SIZE;
    const to = from + PAGE_SIZE;
    return processedResults.slice(from, to);
  }, [processedResults, page]);

  const formatBytes = (bytes?: number): string => {
    if (!bytes) return "Unknown";
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    if (bytes === 0) return "0 B";
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatAge = (pubDate?: string): string => {
    if (!pubDate) return "Unknown";
    return dayjs(pubDate).fromNow();
  };

  return (
    <Stack gap="md">
      {/* Filters */}
      <Group gap="md">
        <TextInput
          placeholder="Filter by indexer name..."
          value={indexerFilter}
          onChange={(e) => setIndexerFilter(e.currentTarget.value)}
          leftSection={<TbSearch size={16} />}
          style={{ flex: 1 }}
        />
        <NumberInput
          placeholder="Min score"
          value={minScore}
          onChange={setMinScore}
          min={0}
          max={100}
          style={{ width: 150 }}
        />
        {(indexerFilter || minScore !== "") && (
          <Button
            variant="subtle"
            onClick={() => {
              setIndexerFilter("");
              setMinScore("");
            }}
          >
            Clear Filters
          </Button>
        )}
      </Group>

      {/* Results Table */}
      <DataTable
        withTableBorder
        borderRadius="sm"
        striped
        highlightOnHover
        records={paginatedResults}
        columns={[
          {
            accessor: "pub_date",
            title: "Age",
            sortable: true,
            width: 120,
            render: (result) => (
              <Text size="sm" c="dimmed">
                {formatAge(result.pub_date)}
              </Text>
            ),
          },
          {
            accessor: "title",
            title: "Title",
            sortable: true,
            ellipsis: true,
            render: (result) => (
              <Tooltip label={result.title} multiline maw={400}>
                <Text size="sm" lineClamp={2}>
                  {result.title}
                </Text>
              </Tooltip>
            ),
          },
          {
            accessor: "indexer_name",
            title: "Indexer",
            sortable: true,
            width: 120,
            render: (result) => (
              <Badge size="sm" variant="light">
                {result.indexer_name || "Unknown"}
              </Badge>
            ),
          },
          {
            accessor: "size",
            title: "Size",
            sortable: true,
            width: 100,
            render: (result) => (
              <Text size="sm">{formatBytes(result.size)}</Text>
            ),
          },
          {
            accessor: "seeders",
            title: "Seeders",
            sortable: true,
            width: 90,
            render: (result) => (
              <Text size="sm" c={result.seeders ? "green" : "dimmed"}>
                {result.seeders ?? 0}
              </Text>
            ),
          },
          {
            accessor: "peers",
            title: "Peers",
            sortable: true,
            width: 90,
            render: (result) => (
              <Text size="sm" c={result.peers ? "blue" : "dimmed"}>
                {result.peers ?? 0}
              </Text>
            ),
          },
          {
            accessor: "score",
            title: "Score",
            sortable: true,
            width: 80,
            render: (result) => (
              <Badge
                size="sm"
                color={
                  (result.score ?? 0) >= 80
                    ? "green"
                    : (result.score ?? 0) >= 50
                    ? "yellow"
                    : "red"
                }
              >
                {result.score ?? 0}
              </Badge>
            ),
          },
          {
            accessor: "rejections",
            title: "Rejected",
            width: 90,
            render: (result) => {
              const hasRejections =
                result.rejections && result.rejections.length > 0;
              return hasRejections ? (
                <Tooltip
                  label={
                    <Box>
                      <Text size="sm" fw={600} mb={4}>
                        Rejections:
                      </Text>
                      {result.rejections!.map((rejection, idx) => (
                        <Text key={idx} size="xs">
                          • {rejection}
                        </Text>
                      ))}
                    </Box>
                  }
                  multiline
                  maw={300}
                >
                  <Badge color="red" size="sm" leftSection={<TbAlertCircle size={12} />}>
                    Yes
                  </Badge>
                </Tooltip>
              ) : (
                <Badge color="gray" size="sm" variant="light">
                  No
                </Badge>
              );
            },
          },
          {
            accessor: "actions",
            title: "Actions",
            width: 80,
            textAlign: "center",
            render: (result) => (
              <Group gap={4} justify="center">
                <Tooltip label="Download (Coming Soon)">
                  <ActionIcon
                    variant="subtle"
                    color="blue"
                    onClick={() => onDownload?.(result)}
                    disabled={!onDownload}
                  >
                    <TbDownload size={18} />
                  </ActionIcon>
                </Tooltip>
              </Group>
            ),
          },
        ]}
        totalRecords={processedResults.length}
        recordsPerPage={PAGE_SIZE}
        page={page}
        onPageChange={setPage}
        sortStatus={sortStatus}
        onSortStatusChange={setSortStatus}
        fetching={loading}
        noRecordsText="No results found"
        minHeight={150}
      />

      {/* Results summary */}
      <Text size="sm" c="dimmed">
        Showing {paginatedResults.length} of {processedResults.length} results
        {processedResults.length !== results.length &&
          ` (filtered from ${results.length} total)`}
      </Text>
    </Stack>
  );
}
