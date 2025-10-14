import { Group, Box, Text } from '@mantine/core';


// TODO: Once config's are done, make the week start configurable
function WeekdayHeaders() {
  return (
    <Group gap={0} grow style={{ borderBottom: '1px solid var(--mantine-color-dark-4)' }}>
      {['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'].map((day) => (
        <Box key={day} p="sm" ta="center">
          <Text fw={600} size="sm" c="dimmed">
            {day}
          </Text>
        </Box>
      ))}
    </Group>
  );
}

export default WeekdayHeaders;