import { Title, Text, Group, Box, ActionIcon, Flex, SegmentedControl } from '@mantine/core';
import { TbChevronLeft, TbChevronRight } from "react-icons/tb";

type ViewMode = 'month' | 'week';

interface CalendarHeaderProps {
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  title: string;
  onNavigate: (direction: 'prev' | 'next') => void;
  onToday: () => void;
}

function CalendarHeader({ viewMode, onViewModeChange, title, onNavigate, onToday }: CalendarHeaderProps) {
  return (
    <Box p="md" style={{ borderBottom: '1px solid var(--mantine-color-dark-4)' }}>
      <Flex justify="space-between" align="center">
        <Title order={2}>{title}</Title>
        <Group>
          <SegmentedControl
            value={viewMode}
            onChange={(value) => onViewModeChange(value as ViewMode)}
            data={[
              { label: 'Month', value: 'month' },
              { label: 'Week', value: 'week' },
            ]}
          />
          <ActionIcon variant="default" onClick={() => onNavigate('prev')} size="lg">
            <TbChevronLeft size={18} />
          </ActionIcon>
          <ActionIcon variant="filled" onClick={onToday} size="lg">
            <Text size="xs" fw={600}>Today</Text>
          </ActionIcon>
          <ActionIcon variant="default" onClick={() => onNavigate('next')} size="lg">
            <TbChevronRight size={18} />
          </ActionIcon>
        </Group>
      </Flex>
    </Box>
  );
}


export default CalendarHeader;