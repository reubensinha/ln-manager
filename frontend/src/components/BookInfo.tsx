import { useEffect, useState } from "react";

import {
  Group,
  Text,
  Title,
  Image,
  Stack,
  Badge,
  Box,
  Center,
  Divider,
  Button,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { TbEyeOff } from "react-icons/tb";

import { toggleBookDownloaded } from "../api/api";
import type { Book } from "../api/ApiResponse";

const BLUR_NSFW: boolean = true;

function BookInfo({ book }: { book: Book }) {
  const [showNsfw, { open: openNsfw }] = useDisclosure(false);
  const [isDownloaded, setIsDownloaded] = useState(book.downloaded);
  const [isLoading, setIsLoading] = useState(false);
  const shouldBlur = BLUR_NSFW && book.nsfw_img && !showNsfw;

  useEffect(() => {
    setIsDownloaded(book.downloaded);
  }, [book.downloaded]);

  const handleToggleDownloaded = async () => {
    setIsLoading(true);
    try {
      await toggleBookDownloaded(book.id);
      setIsDownloaded((prev) => !prev);
    } catch (error) {
      console.error("Error toggling download:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Stack style={{ flex: 1 }}>
      <Group align="flex-start" gap="xl">
        <Box style={{ position: "relative", width: 250, flexShrink: 0 }}>
          <Image
            src={book.img_url}
            alt={book.title}
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
              onClick={openNsfw}
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
              {book.title}
            </Title>

            {book.romaji && (
              <Text size="lg" c="dimmed" fw={500}>
                {book.romaji}
              </Text>
            )}
            {book.title_orig && (
              <Text size="sm" c="dimmed" fs="italic">
                {book.title_orig}
              </Text>
            )}
          </Stack>

          {/* Publishing Status and Dates */}
          <Group gap="md" wrap="wrap">
            {book.release_date && <Badge>{book.release_date}</Badge>}
          </Group>

          {/* Series Statistics */}
          {(book.language || book.orig_language) && (
            <Group gap="lg" wrap="wrap">
              {book.language && (
                <Group gap={6}>
                  <Text size="sm" c="dimmed">
                    Language:
                  </Text>
                  <Text size="sm" fw={600} tt="uppercase">
                    {book.language}
                  </Text>
                </Group>
              )}
              {book.orig_language && book.orig_language !== book.language && (
                <Group gap={6}>
                  <Text size="sm" c="dimmed">
                    Original:
                  </Text>
                  <Text size="sm" fw={600} tt="uppercase">
                    {book.orig_language}
                  </Text>
                </Group>
              )}
            </Group>
          )}

          {/* Authors, Artists, Other Staff */}
          {(book.authors || book.artists || book.other_staff) && (
            <Stack gap="sm" style={{ minWidth: 250, maxWidth: 350 }}>
              <Text size="sm" fw={600} c="dimmed">
                Staff
              </Text>
              <Stack gap="sm">
                {book.authors?.map((author) => (
                  <Group key={author} gap="sm" wrap="nowrap">
                    <Badge size="sm" variant="dot" color="violet" w={80}>
                      Author
                    </Badge>
                    <Text size="sm" fw={500} style={{ flex: 1 }}>
                      {author}
                    </Text>
                  </Group>
                ))}
                {book.artists?.map((artist) => (
                  <Group key={artist} gap="sm" wrap="nowrap">
                    <Badge size="sm" variant="dot" color="pink" w={80}>
                      Artist
                    </Badge>
                    <Text size="sm" fw={500} style={{ flex: 1 }}>
                      {artist}
                    </Text>
                  </Group>
                ))}
                {book.other_staff?.map((staff) => (
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

          <Button
            onClick={handleToggleDownloaded}
            loading={isLoading}
            variant={isDownloaded ? "light" : "filled"}
          >
            {isDownloaded ? "In Library" : "Add to Library"}
          </Button>
        </Stack>
      </Group>

      {/* Description */}
      {book.description && (
        <>
          <Divider />
          <Box>
            <Text size="sm" fw={600} c="dimmed" mb="sm">
              Synopsis
            </Text>
            <Text size="sm" style={{ lineHeight: 1.8 }}>
              {book.description}
            </Text>
          </Box>
        </>
      )}
    </Stack>
  );
}

export default BookInfo;
