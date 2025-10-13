import { useState, useEffect } from 'react';
import { Title, Text, Group, Box, ActionIcon, Flex, SegmentedControl, Loader, Center } from '@mantine/core';
import { TbChevronLeft, TbChevronRight } from "react-icons/tb";
import { getReleases } from '../api/api';
import type { Release } from '../api/ApiResponse';
import CalendarMonthView from '../components/Calendar/CalendarMonthView';
import CalendarWeekView from '../components/Calendar/CalendarWeekView';

type ViewMode = 'month' | 'week';

function CalendarPage() {
  const [releases, setReleases] = useState<Release[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [viewMode, setViewMode] = useState<ViewMode>('month');

  useEffect(() => {
    const fetchReleases = async () => {
      setLoading(true);
      const data = await getReleases();
      setReleases(data);
      setLoading(false);
    };

    fetchReleases();
  }, []);

  // Get all weeks in the month
  const getMonthWeeks = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    
    const startDate = new Date(firstDay);
    startDate.setDate(firstDay.getDate() - firstDay.getDay());
    
    const endDate = new Date(lastDay);
    endDate.setDate(lastDay.getDate() + (6 - lastDay.getDay()));
    
    const weeks = [];
    const currentWeekStart = new Date(startDate);
    
    while (currentWeekStart <= endDate) {
      const week = [];
      for (let i = 0; i < 7; i++) {
        const day = new Date(currentWeekStart);
        day.setDate(currentWeekStart.getDate() + i);
        week.push(day);
      }
      weeks.push(week);
      currentWeekStart.setDate(currentWeekStart.getDate() + 7);
    }
    
    return weeks;
  };

  // Get start of week (Sunday)
  const getWeekStart = (date: Date) => {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day;
    return new Date(d.setDate(diff));
  };

  // Get 7 days starting from week start
  const getWeekDays = () => {
    const weekStart = getWeekStart(currentDate);
    return Array.from({ length: 7 }, (_, i) => {
      const day = new Date(weekStart);
      day.setDate(weekStart.getDate() + i);
      return day;
    });
  };

  // Get releases for a specific date
  const getReleasesForDate = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0];
    return releases.filter(r => 
      r.release_date && r.release_date.startsWith(dateStr)
    );
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() + (direction === 'next' ? 1 : -1));
    setCurrentDate(newDate);
  };

  const navigateWeek = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7));
    setCurrentDate(newDate);
  };

  const navigate = (direction: 'prev' | 'next') => {
    if (viewMode === 'month') {
      navigateMonth(direction);
    } else {
      navigateWeek(direction);
    }
  };

  const weeks = getMonthWeeks();
  const weekDays = getWeekDays();
  const monthName = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const weekStart = weekDays[0];
  const weekEnd = weekDays[6];

  if (loading) {
    return (
      <Center style={{ height: '100vh' }}>
        <Loader size="xl" />
      </Center>
    );
  }

  return (
    <Box style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box p="md" style={{ borderBottom: '1px solid var(--mantine-color-dark-4)' }}>
        <Flex justify="space-between" align="center">
          <Title order={2}>
            {viewMode === 'month' 
              ? monthName
              : `${weekStart.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })} - ${weekEnd.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}`
            }
          </Title>
          <Group>
            <SegmentedControl
              value={viewMode}
              onChange={(value) => setViewMode(value as ViewMode)}
              data={[
                { label: 'Month', value: 'month' },
                { label: 'Week', value: 'week' },
              ]}
            />
            <ActionIcon variant="default" onClick={() => navigate('prev')} size="lg">
              <TbChevronLeft size={18} />
            </ActionIcon>
            <ActionIcon variant="filled" onClick={() => setCurrentDate(new Date())} size="lg">
              <Text size="xs" fw={600}>Today</Text>
            </ActionIcon>
            <ActionIcon variant="default" onClick={() => navigate('next')} size="lg">
              <TbChevronRight size={18} />
            </ActionIcon>
          </Group>
        </Flex>
      </Box>

      {/* Weekday Headers - Only for month view */}
      {viewMode === 'month' && (
        <Group gap={0} grow style={{ borderBottom: '1px solid var(--mantine-color-dark-4)' }}>
          {['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'].map((day) => (
            <Box key={day} p="sm" ta="center">
              <Text fw={600} size="sm" c="dimmed">
                {day}
              </Text>
            </Box>
          ))}
        </Group>
      )}

      {/* Calendar Grid */}
      {viewMode === 'month' ? (
        <CalendarMonthView 
          weeks={weeks}
          currentDate={currentDate}
          getReleasesForDate={getReleasesForDate}
        />
      ) : (
        <CalendarWeekView 
          weekDays={weekDays}
          getReleasesForDate={getReleasesForDate}
        />
      )}
    </Box>
  );
}

export default CalendarPage;