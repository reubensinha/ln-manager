import { Group, Box, Stack, Text } from '@mantine/core';
import type { Release } from '../../api/ApiResponse';
import ReleaseCard from './ReleaseCard';

interface CalendarWeekViewProps {
  weekDays: Date[];
  getReleasesForDate: (date: Date) => Release[];
}

function CalendarWeekView({ weekDays, getReleasesForDate }: CalendarWeekViewProps) {
  return (
    <Box style={{ flex: 1, overflow: 'hidden' }}>
      <Group gap={0} grow style={{ height: '90%' }}>
        {weekDays.map((day, index) => {
          const dayReleases = getReleasesForDate(day);
          const isToday = day.toDateString() === new Date().toDateString();

          return (
            <Box
              key={index}
              style={{
                borderRight: index < 6 ? '1px solid var(--mantine-color-dark-4)' : 'none',
                borderBottom: '1px solid var(--mantine-color-dark-4)',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                minWidth: 0,
              }}
            >
              <Box
                p="md"
                style={{
                  borderBottom: '1px solid var(--mantine-color-dark-4)',
                  backgroundColor: isToday ? 'var(--mantine-color-blue-9)' : undefined,
                }}
              >
                <Text fw={600} size="sm" c={isToday ? 'blue.2' : 'dimmed'}>
                  {day.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase()}
                </Text>
                <Text fw={700} size="xl" c={isToday ? 'blue.2' : undefined}>
                  {day.getDate()}
                </Text>
              </Box>

              <Stack gap="xs" p="xs" style={{ flex: 1, overflow: 'auto' }}>
                {dayReleases.length === 0 ? (
                  <Text c="dimmed" size="xs" ta="center" mt="md">
                    No releases
                  </Text>
                ) : (
                  dayReleases.map((release) => (
                    <ReleaseCard key={release.id} release={release} />
                  ))
                )}
              </Stack>
            </Box>
          );
        })}
      </Group>
    </Box>
  );
}

export default CalendarWeekView;