import { Group, Box, Stack, Text } from '@mantine/core';
import type { Release } from '../../api/ApiResponse';
import ReleaseCard from './ReleaseCard';

interface CalendarMonthViewProps {
  weeks: Date[][];
  currentDate: Date;
  getReleasesForDate: (date: Date) => Release[];
}

function CalendarMonthView({ weeks, currentDate, getReleasesForDate }: CalendarMonthViewProps) {
  return (
    <Box style={{ flex: 1, overflow: 'auto' }}>
      <Stack gap={0} style={{ height: '100%' }}>
        {weeks.map((week, weekIndex) => (
          <Group key={weekIndex} gap={0} grow style={{ flex: 1, minHeight: 0 }}>
            {week.map((day, dayIndex) => {
              const dayReleases = getReleasesForDate(day);
              const isToday = day.toDateString() === new Date().toDateString();
              const isCurrentMonth = day.getMonth() === currentDate.getMonth();

              return (
                <Box
                  key={dayIndex}
                  style={{
                    border: '1px solid var(--mantine-color-dark-4)',
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    minWidth: 0,
                    backgroundColor: !isCurrentMonth ? 'var(--mantine-color-dark-8)' : undefined,
                  }}
                >
                  <Box
                    p="xs"
                    style={{
                      backgroundColor: isToday ? 'var(--mantine-color-blue-9)' : undefined,
                      flexShrink: 0,
                    }}
                  >
                    <Text
                      fw={700}
                      size="sm"
                      c={isToday ? 'blue.2' : !isCurrentMonth ? 'dimmed' : undefined}
                    >
                      {day.getDate()}
                    </Text>
                  </Box>

                  <Stack 
                    gap={4} 
                    p={4} 
                    style={{ 
                      flex: 1, 
                      overflow: 'auto',
                      minHeight: 0,
                    }}
                  >
                    {dayReleases.map((release) => (
                      <ReleaseCard key={release.id} release={release} compact />
                    ))}
                  </Stack>
                </Box>
              );
            })}
          </Group>
        ))}
      </Stack>
    </Box>
  );
}

export default CalendarMonthView;