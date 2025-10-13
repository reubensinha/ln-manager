import { Group, Box, Stack, Text, Card, Badge } from '@mantine/core';
import type { Release } from '../../api/ApiResponse';

interface CalendarWeekViewProps {
  weekDays: Date[];
  getReleasesForDate: (date: Date) => Release[];
}

function CalendarWeekView({ weekDays, getReleasesForDate }: CalendarWeekViewProps) {
  return (
    <Box style={{ flex: 1, overflow: 'hidden' }}>
      <Group gap={0} grow style={{ height: '100%' }}>
        {weekDays.map((day, index) => {
          const dayReleases = getReleasesForDate(day);
          const isToday = day.toDateString() === new Date().toDateString();

          return (
            <Box
              key={index}
              style={{
                borderRight: index < 6 ? '1px solid var(--mantine-color-dark-4)' : 'none',
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
                    <Card
                      key={release.id}
                      padding="xs"
                      withBorder
                      style={{
                        cursor: 'pointer',
                        borderLeft: '3px solid var(--mantine-color-blue-6)',
                      }}
                    >
                      <Stack gap={4}>
                        <Text size="sm" fw={600} lineClamp={2}>
                          {release.title}
                        </Text>
                        {release.romaji && (
                          <Text size="xs" c="dimmed" lineClamp={1}>
                            {release.romaji}
                          </Text>
                        )}
                        {release.book?.img_url && (
                          <Box>
                            <img 
                              src={release.book.img_url} 
                              alt={release.title}
                              style={{ 
                                width: '100%', 
                                height: 'auto',
                                borderRadius: '4px',
                                marginTop: '4px'
                              }}
                            />
                          </Box>
                        )}
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