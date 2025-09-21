import {
  IconAdjustments,
  IconCalendarStats,
  IconFileAnalytics,
  IconGauge,
  IconLock,
  IconNotes,
  IconPresentationAnalytics,
} from '@tabler/icons-react';
import { Code, Group, ScrollArea, Box, Card } from '@mantine/core';
import AuthorityCheck from '@/route/AuthorityCheck';
import Views from '@/components/Layout/Views';
import UserPopOver from '@/components/UserPopOver/UserPopOver';
import { MantineLogo } from '@mantinex/mantine-logo';
// import {} from '../NavbarLinksGroup/NavbarLinksGroup';
// import { UserButton } from '../UserButton/UserButton';
// import { Logo } from './Logo';
import navigationConfig from '@/configs/navigation.config';
import { useAppSelector } from '@/store';
import { LinksGroup } from '@/components/Layout/LinksGroup';
import { Link, useNavigate } from 'react-router-dom';
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import classes from './NavbarNested.module.css';

// const mockdata = [
//   { label: 'Dashboard', icon: IconGauge },
//   {
//     label: 'Market news',
//     icon: IconNotes,
//     initiallyOpened: true,
//     links: [ 
//       { label: 'Overview', link: '/' },
//       { label: 'Forecasts', link: '/' },
//       { label: 'Outlook', link: '/' },
//       { label: 'Real time', link: '/' },
//     ],
//   },
//   {
//     label: 'Releases',
//     icon: IconCalendarStats,
//     links: [
//       { label: 'Upcoming releases', link: '/' },
//       { label: 'Previous releases', link: '/' },
//       { label: 'Releases schedule', link: '/' },
//     ],
//   },
//   { label: 'Analytics', icon: IconPresentationAnalytics },
//   { label: 'Contracts', icon: IconFileAnalytics },
//   { label: 'Settings', icon: IconAdjustments },
//   {
//     label: 'Security',
//     icon: IconLock,
//     links: [
//       { label: 'Enable 2FA', link: '/' },
//       { label: 'Change password', link: '/' },
//       { label: 'Recovery codes', link: '/' },
//     ],
//   },
// ];

function Navbar() {
  const userAuthority = useAppSelector((state) => state.auth.user.role);
  const [active, setActive] = useState('');
  const navigate = useNavigate();
  const { t } = useTranslation();

  const links = navigationConfig.map((item, index) => {
    let links = [];

    if (item.subMenu && item.subMenu.length > 0) {
      links = item.subMenu.map((i) => ({
        label: i.title,
        link: i.path,
        authority: i.authority,
      }));
      const isAnyLinkActive = links.some((link) => location.pathname.includes(link.link));

      return (
        <AuthorityCheck userAuthority={userAuthority || []} authority={item.authority} key={index}>
          <LinksGroup
            initiallyOpened={isAnyLinkActive}
            icon={item.icon}
            label={item.title}
            links={links}
          />
        </AuthorityCheck>
      );
    } else {
      return (
        <AuthorityCheck userAuthority={userAuthority || []} authority={item.authority} key={index}>
          <LinksGroup
            icon={item.icon}
            label={item.title}
            initiallyOpened={false}
            links={[{ label: item.title, link: item.path }]}
          />
        </AuthorityCheck>
      );
    }
  });

  return (
    <nav className={classes.navbar}>
      <div className={classes.header}>
        <Group justify="space-between">
          <MantineLogo size={28} />
          <Code fw={700}>v3.1.2</Code>
        </Group>
      </div>

      <ScrollArea className={classes.links}>
        <div className={classes.linksInner}>{links}</div>
      </ScrollArea>

      <div className={classes.footer}>
        <UserPopOver />
      </div>
    </nav>
  );
}

export default function NavbarNested() {
  return (
    <div
      style={{
        overflow: 'hidden',
        backgroundColor: 'rgb(236,236,236)',
        display: 'flex',
        flex: '1 1 auto',
        height: '100vh',
      }}
    >
      <Navbar />
      <div
        style={{
          padding: '2rem',
          backgroundColor: '#ffffff',
          flex: 1,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
        }}
      >
        <Card
          style={{
            overflowY: 'auto',
            maxHeight: '100%',
            width: '100%',
            flex: 1,
          }}
          radius={15}
          withBorder
          p={40}
        >
          <Views />
        </Card>
      </div>
    </div>
  );
}
