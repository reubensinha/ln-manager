import { useState } from "react";
import {
  Box,
  Center,
  Group,
  Text,
  Title,
  Image,
  Stack,
  Badge,
  Button,
  Divider,
  Modal,
  TextInput,
  Loader,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { TbEyeOff, TbSearch, TbRobot } from "react-icons/tb";
import { searchIndexers } from "../api/api";
import type { SeriesSourceResponse, IndexerResult } from "../api/ApiResponse";
import type { PublishingStatus } from "../types/MetadataFieldTypes";
import { IndexerResultTable } from "./Indexer/IndexerResultTable";

const BLUR_NSFW: boolean = true;

function getStatusColor(status?: PublishingStatus): string {
  switch (status) {
    case "ongoing":
      return "blue";
    case "completed":
      return "green";
    case "hiatus":
      return "yellow";
    case "stalled":
      return "orange";
    case "cancelled":
      return "red";
    case "unknown":
    default:
      return "gray";
  }
}

function SeriesInfo({ series }: { series: SeriesSourceResponse }) {
  const [showNsfw, setShowNsfw] = useState(false);
  const [searchModalOpened, { open: openSearchModal, close: closeSearchModal }] = useDisclosure(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<IndexerResult[]>([]);
  const [searching, setSearching] = useState(false);
  const shouldBlur = BLUR_NSFW && series.nsfw_img && !showNsfw;

  const handleInteractiveSearch = () => {
    // Pre-fill search with series title
    setSearchQuery(series.title);
    openSearchModal();
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setSearching(true);
    try {
      const results = await searchIndexers(searchQuery);
      // Map results to include indexer_name from the response
      const mappedResults = results.map((result) => ({
        ...result,
        indexer_name: result.indexer_name || "Unknown",
      }));
      setSearchResults(mappedResults);
    } catch (error) {
      console.error("Error searching indexers:", error);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleDownload = (result: IndexerResult) => {
    // TODO: Implement download functionality
    console.log("Download requested for:", result);
  };

  return (
    <Stack style={{ flex: 1 }}>
      <Group align="flex-start" gap="xl">
        <Box style={{ position: "relative", width: 250, flexShrink: 0 }}>
          <Image
            src={series.img_url}
            alt={series.title}
            style={{
              maxWidth: 250,
              borderRadius: 8,
              filter: shouldBlur ? "blur(20px)" : "none",
              transition: "filter 0.3s ease",
            }}
            fit="contain"
            h={350}
          />
          {shouldBlur && (
            <Box
              onClick={() => setShowNsfw(true)}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: "rgba(0, 0, 0, 0.6)",
                borderRadius: 8,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "background-color 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "rgba(0, 0, 0, 0.7)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "rgba(0, 0, 0, 0.6)";
              }}
            >
              <Center>
                <Stack align="center" gap="xs">
                  <TbEyeOff size={48} color="white" />
                  <Text c="white" fw={600} size="sm">
                    NSFW Content
                  </Text>
                  <Text c="white" size="xs" opacity={0.8}>
                    Click to reveal
                  </Text>
                </Stack>
              </Center>
            </Box>
          )}
        </Box>

        {/* Main Content */}
        <Stack style={{ flex: 1, minWidth: 0 }} gap="md">
          {/* Titles */}
          <Stack gap={4}>
            <Title order={1} style={{ lineHeight: 1.2 }}>
              {series.title}
            </Title>

            {series.romaji && (
              <Text size="lg" c="dimmed" fw={500}>
                {series.romaji}
              </Text>
            )}
            {series.title_orig && (
              <Text size="sm" c="dimmed" fs="italic">
                {series.title_orig}
              </Text>
            )}
          </Stack>

          {/* Two Column Layout */}
          <Group align="flex-start" gap="xl" wrap="nowrap">
            {/* Left Column - Metadata */}
            <Stack gap="lg" style={{ flex: 1, minWidth: 0, maxWidth: 550 }}>
              {/* Publishing Status and Dates */}
              <Group gap="md" wrap="wrap">
                <Badge
                  size="lg"
                  variant="filled"
                  color={getStatusColor(series.publishing_status)}
                >
                  {series.publishing_status}
                </Badge>
                {series.start_date && (
                  <Text size="sm" c="dimmed" fw={500}>
                    {series.start_date}
                    {series.end_date && ` – ${series.end_date}`}
                    {!series.end_date && " – Present"}
                  </Text>
                )}
              </Group>

              {/* Series Statistics */}
              {((series.books && series.books.length > 0) ||
                (series.chapters && series.chapters.length > 0) ||
                series.language ||
                series.orig_language) && (
                <Group gap="lg" wrap="wrap">
                  {series.books && series.books.length > 0 && (
                    <Group gap={6}>
                      <Text size="sm" c="dimmed">
                        Volumes:
                      </Text>
                      <Text size="sm" fw={600}>
                        {series.books.length}
                      </Text>
                    </Group>
                  )}
                  {series.chapters && series.chapters.length > 0 && (
                    <Group gap={6}>
                      <Text size="sm" c="dimmed">
                        Chapters:
                      </Text>
                      <Text size="sm" fw={600}>
                        {series.chapters.length}
                      </Text>
                    </Group>
                  )}
                  {series.language && (
                    <Group gap={6}>
                      <Text size="sm" c="dimmed">
                        Language:
                      </Text>
                      <Text size="sm" fw={600} tt="uppercase">
                        {series.language}
                      </Text>
                    </Group>
                  )}
                  {series.orig_language &&
                    series.orig_language !== series.language && (
                      <Group gap={6}>
                        <Text size="sm" c="dimmed">
                          Original:
                        </Text>
                        <Text size="sm" fw={600} tt="uppercase">
                          {series.orig_language}
                        </Text>
                      </Group>
                    )}
                </Group>
              )}

              {/* Genres */}
              {series.genres && series.genres.length > 0 && (
                <Box>
                  <Text size="sm" fw={600} c="dimmed" mb="xs">
                    Genres
                  </Text>
                  <Group gap="xs" wrap="wrap">
                    {series.genres?.map((genre) => (
                      <Badge key={genre} color="teal" variant="light" size="md">
                        {genre}
                      </Badge>
                    ))}
                  </Group>
                </Box>
              )}
            </Stack>

            {/* Right Column - Staff */}
            {/* Authors, Artists, Other Staff */}
            {(series.authors || series.artists || series.other_staff) && (
              <Stack gap="sm" style={{ minWidth: 250, maxWidth: 350 }}>
                <Text size="sm" fw={600} c="dimmed">
                  Staff
                </Text>
                <Stack gap="sm">
                  {series.authors?.map((author) => (
                    <Group key={author} gap="sm" wrap="nowrap">
                      <Badge size="sm" variant="dot" color="violet" w={80}>
                        Author
                      </Badge>
                      <Text size="sm" fw={500} style={{ flex: 1 }}>
                        {author}
                      </Text>
                    </Group>
                  ))}
                  {series.artists?.map((artist) => (
                    <Group key={artist} gap="sm" wrap="nowrap">
                      <Badge size="sm" variant="dot" color="pink" w={80}>
                        Artist
                      </Badge>
                      <Text size="sm" fw={500} style={{ flex: 1 }}>
                        {artist}
                      </Text>
                    </Group>
                  ))}
                  {series.other_staff?.map((staff) => (
                    <Group key={staff.name} gap="sm" wrap="nowrap">
                      <Badge size="sm" variant="dot" color="cyan" w={80}>
                        {staff.role}
                      </Badge>
                      <Text size="sm" fw={500} style={{ flex: 1 }}>
                        {staff.name}
                      </Text>
                    </Group>
                  ))}
                </Stack>
              </Stack>
            )}
          </Group>

          {/* Tags */}
          <Stack gap="md">
            {series.content_tags && series.content_tags.length > 0 && (
              <Box>
                <Text size="sm" fw={600} c="dimmed" mb="xs">
                  Content Tags
                </Text>
                <Group gap="xs" wrap="wrap">
                  {series.content_tags.map((content_tag) => (
                    <Badge key={content_tag} color="red" variant="light">
                      {content_tag}
                    </Badge>
                  ))}
                </Group>
              </Box>
            )}

            {series.demographics && series.demographics.length > 0 && (
              <Box>
                <Text size="sm" fw={600} c="dimmed" mb="xs">
                  Demographics
                </Text>
                <Group gap="xs" wrap="wrap">
                  {series.demographics.map((demographic) => (
                    <Badge key={demographic} color="blue" variant="light">
                      {demographic}
                    </Badge>
                  ))}
                </Group>
              </Box>
            )}

            {series.tags && series.tags.length > 0 && (
              <Box>
                <Text size="sm" fw={600} c="dimmed" mb="xs">
                  Tags
                </Text>
                <Group gap="xs" wrap="wrap">
                  {series.tags.map((tag) => (
                    <Badge key={tag} color="gray" variant="light">
                      {tag}
                    </Badge>
                  ))}
                </Group>
              </Box>
            )}
          </Stack>

          {/* Publishers */}
          {series.publishers && series.publishers.length > 0 && (
            <Box>
              <Text size="sm" fw={600} c="dimmed" mb="xs">
                Publishers
              </Text>
              <Group gap="xs">
                {series.publishers.map((publisher) => (
                  <Badge key={publisher} color="indigo" variant="light">
                    {publisher}
                  </Badge>
                ))}
              </Group>
            </Box>
          )}

          {/* Action Buttons */}
          <Group gap="sm">
            <Button
              variant="default"
              leftSection={<TbRobot size={18} />}
              disabled
            >
              Automatic Search
            </Button>

            <Button
              variant="outline"
              leftSection={<TbSearch size={18} />}
              onClick={handleInteractiveSearch}
            >
              Interactive Search
            </Button>
          </Group>
        </Stack>
      </Group>

      {/* Description */}
      {series.description && (
        <>
          <Divider />
          <Box>
            <Text size="sm" fw={600} c="dimmed" mb="sm">
              Synopsis
            </Text>
            <Text size="sm" style={{ lineHeight: 1.8 }}>
              {series.description}
            </Text>
          </Box>
        </>
      )}

      <Divider />

      {/* Links */}
      <Box>
        <Text size="sm" fw={600} c="dimmed" mb="sm">
          External Links
        </Text>
        <Group gap="xs">
          <Button
            size="sm"
            variant="light"
            color="gray"
            radius="xl"
            component="a"
            href={series.source_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            Source
          </Button>
          {series.external_links?.map((link) => (
            <Button
              key={link.url}
              size="sm"
              variant="light"
              color="gray"
              radius="xl"
              component="a"
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              {link.name}
            </Button>
          ))}
        </Group>
      </Box>

      {/* Aliases */}
      {series.aliases && series.aliases.length > 0 && (
        <Box>
          <Text size="sm" fw={600} c="dimmed" mb="sm">
            Also Known As
          </Text>
          <Group gap="xs">
            {series.aliases?.map((alias) => (
              <Badge
                key={alias}
                size="sm"
                color="cyan"
                variant="outline"
                tt={"none"}
              >
                {alias}
              </Badge>
            ))}
          </Group>
        </Box>
      )}

      {/* Interactive Search Modal */}
      <Modal
        opened={searchModalOpened}
        onClose={closeSearchModal}
        title="Interactive Search"
        size="xl"
        centered
      >
        <Stack gap="md">
          <Group gap="sm">
            <TextInput
              placeholder="Search for releases..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.currentTarget.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleSearch();
                }
              }}
              leftSection={<TbSearch size={16} />}
              style={{ flex: 1 }}
            />
            <Button onClick={handleSearch} loading={searching}>
              Search
            </Button>
          </Group>

          {searching ? (
            <Center p="xl">
              <Loader />
            </Center>
          ) : (
            <IndexerResultTable
              results={searchResults}
              loading={searching}
              onDownload={handleDownload}
            />
          )}
        </Stack>
      </Modal>
    </Stack>
  );
}

export default SeriesInfo;
