import { useState, useEffect } from 'react';
import { Box, Loader, Center } from '@mantine/core';
import { getReleases } from '../api/api';
import type { Release } from '../api/ApiResponse';
import CalendarMonthView from '../components/Calendar/CalendarMonthView';
import CalendarWeekView from '../components/Calendar/CalendarWeekView';
import CalendarHeader from '../components/Calendar/CalendarHeader';
import WeekdayHeaders from '../components/Calendar/WeekdayHeaders';

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

  const getWeekStart = (date: Date) => {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day;
    return new Date(d.setDate(diff));
  };

  const getWeekDays = () => {
    const weekStart = getWeekStart(currentDate);
    return Array.from({ length: 7 }, (_, i) => {
      const day = new Date(weekStart);
      day.setDate(weekStart.getDate() + i);
      return day;
    });
  };

  const getReleasesForDate = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0];
    return releases.filter(r => 
      r.release_date && r.release_date.startsWith(dateStr)
    );
  };

  const navigate = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    if (viewMode === 'month') {
      newDate.setMonth(newDate.getMonth() + (direction === 'next' ? 1 : -1));
    } else {
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7));
    }
    setCurrentDate(newDate);
  };

  const weeks = getMonthWeeks();
  const weekDays = getWeekDays();
  const monthName = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const weekStart = weekDays[0];
  const weekEnd = weekDays[6];

  const title = viewMode === 'month' 
    ? monthName
    : `${weekStart.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })} - ${weekEnd.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}`;

  if (loading) {
    return (
      <Center style={{ height: '100vh' }}>
        <Loader size="xl" />
      </Center>
    );
  }

  return (
    <Box style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <CalendarHeader
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        title={title}
        onNavigate={navigate}
        onToday={() => setCurrentDate(new Date())}
      />

      {viewMode === 'month' && <WeekdayHeaders />}

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