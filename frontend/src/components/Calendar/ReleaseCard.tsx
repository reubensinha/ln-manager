import { Card, Stack, Text, Group, Badge } from '@mantine/core';
import type { Release } from '../../api/ApiResponse';

interface ReleaseCardProps {
  release: Release;
  compact?: boolean;
}

function ReleaseCard({ release, compact = false }: ReleaseCardProps) {
  if (compact) {
    return (
      <Card
        padding={4}
        withBorder
        style={{
          cursor: 'pointer',
          borderLeft: '3px solid var(--mantine-color-blue-6)',
        }}
      >
        <Group gap={4} wrap="nowrap">
          {release.format && (
            <Badge size="xs" variant="light" style={{ flexShrink: 0 }}>
              {release.format}
            </Badge>
          )}
          {release.language && (
            <Badge size="xs" variant="outline" style={{ flexShrink: 0 }}>
              {release.language}
            </Badge>
          )}
          <Text size="xs" fw={600} lineClamp={1} style={{ flex: 1, minWidth: 0 }}>
            {release.title}
          </Text>
        </Group>
      </Card>
    );
  }

  return (
    <Card
      padding="xs"
      withBorder
      style={{
        cursor: 'pointer',
        borderLeft: '3px solid var(--mantine-color-blue-6)',
      }}
    >
      <Stack gap={4}>
        <Text size="sm" fw={600} lineClamp={2}>
          {release.romaji || release.title}
        </Text>
        <Group gap={4}>
          {release.format && (
            <Badge size="xs" variant="light">
              {release.format}
            </Badge>
          )}
          {release.language && (
            <Badge size="xs" variant="outline">
              {release.language}
            </Badge>
          )}
        </Group>
      </Stack>
    </Card>
  );
}

export default ReleaseCard;