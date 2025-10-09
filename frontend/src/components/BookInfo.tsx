import { Group, Text, Title, Image, Stack, Badge } from "@mantine/core";
import type { Book } from "../api/ApiResponse";

function BookInfo({ book }: { book: Book }) {
  return (
    <Group align="flex-start">
      <Image
        src={book.img_path}
        alt={book.title}
        style={{ maxWidth: 250, borderRadius: 8 }}
        fit="contain"
        // mb="xl"
      />

      <Stack style={{ flex: 1 }}>
        <Title order={1}>{book.title}</Title>

        {/* TODO: Placeholder links */}
        <Group>
          <Badge color="gray">/storage/drop/anime</Badge>
          <Badge color="green">Japanese</Badge>
          <Badge color="yellow">AT-X</Badge>
        </Group>

        {/* Description */}
        <Text size="sm">{book.description}</Text>

        {/* TODO:Placeholder footer */}
        <Text size="xs" color="dimmed">
          Metadata is provided by TheTVDB
        </Text>
      </Stack>
    </Group>
  );
}

export default BookInfo;
