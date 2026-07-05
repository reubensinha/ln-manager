import { useMemo, useState } from 'react';
import { Box, Loader, Center, Group, Button } from '@mantine/core';
import { useLocalStorage } from '@mantine/hooks';
import { useReleases } from '../api/hooks/series';
import {
  TriStateSelect,
  keysWith,
  type TriStateValue,
} from '../components/common/TriStateSelect';
import CalendarMonthView from '../components/Calendar/CalendarMonthView';
import CalendarWeekView from '../components/Calendar/CalendarWeekView';
import CalendarHeader from '../components/Calendar/CalendarHeader';
import WeekdayHeaders from '../components/Calendar/WeekdayHeaders';

type ViewMode = 'month' | 'week';

const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

function CalendarPage() {
  const { data: releases = [], isLoading: loading } = useReleases();
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [viewMode, setViewMode] = useState<ViewMode>('month');

  // Persisted to localStorage so filter preferences survive refreshes.
  const [formatFilter, setFormatFilter] = useLocalStorage<TriStateValue>({
    key: 'calendar:formatFilter',
    defaultValue: {},
    getInitialValueInEffect: false,
  });
  const [languageFilter, setLanguageFilter] = useLocalStorage<TriStateValue>({
    key: 'calendar:languageFilter',
    defaultValue: {},
    getInitialValueInEffect: false,
  });

  const availableFormats = useMemo(
    () =>
      Array.from(
        new Set(releases.map((r) => r.format).filter((f): f is string => !!f))
      ).sort(),
    [releases]
  );
  const availableLanguages = useMemo(
    () =>
      Array.from(
        new Set(releases.map((r) => r.language).filter((l): l is string => !!l))
      ).sort(),
    [releases]
  );

  const filteredReleases = useMemo(() => {
    const fmtInclude = keysWith(formatFilter, 'include');
    const fmtExclude = keysWith(formatFilter, 'exclude');
    const langInclude = keysWith(languageFilter, 'include');
    const langExclude = keysWith(languageFilter, 'exclude');

    return releases.filter((r) => {
      const fmt = r.format ?? '';
      if (fmtInclude.length && !fmtInclude.includes(fmt)) return false;
      if (fmtExclude.includes(fmt)) return false;

      const lang = r.language ?? '';
      if (langInclude.length && !langInclude.includes(lang)) return false;
      if (langExclude.includes(lang)) return false;

      return true;
    });
  }, [releases, formatFilter, languageFilter]);

  const hasActiveFilters =
    Object.keys(formatFilter).length > 0 || Object.keys(languageFilter).length > 0;
  const clearFilters = () => {
    setFormatFilter({});
    setLanguageFilter({});
  };

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
    return filteredReleases.filter(r =>
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

  const showFilters =
    availableFormats.length > 0 || availableLanguages.length > 0;

  return (
    <Box style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <CalendarHeader
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        title={title}
        onNavigate={navigate}
        onToday={() => setCurrentDate(new Date())}
      />

      {showFilters && (
        <Box
          px="md"
          py="xs"
          style={{ borderBottom: '1px solid var(--mantine-color-dark-4)' }}
        >
          <Group align="flex-end" gap="md" wrap="wrap">
            {availableFormats.length > 0 && (
              <TriStateSelect
                label="Format"
                width={150}
                options={availableFormats.map((f) => ({
                  value: f,
                  label: capitalize(f),
                }))}
                value={formatFilter}
                onChange={setFormatFilter}
              />
            )}
            {availableLanguages.length > 0 && (
              <TriStateSelect
                label="Language"
                width={140}
                options={availableLanguages.map((l) => ({
                  value: l,
                  label: l.toUpperCase(),
                }))}
                value={languageFilter}
                onChange={setLanguageFilter}
              />
            )}
            {hasActiveFilters && (
              <Button variant="subtle" onClick={clearFilters} mb={4}>
                Clear filters
              </Button>
            )}
          </Group>
        </Box>
      )}

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
