import { AppShell, Burger, Group } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { NavbarNested } from "../Navbar/NavbarNested";
import SpotlightSearch from "../SpotlightSearch";
// import SearchBar from "../SearchBar";

interface LayoutProps {
    children: React.ReactNode;
}

function Layout({ children }: LayoutProps) {
  const [opened, { toggle }] = useDisclosure();

  return (
    <AppShell
      padding="md"
      header={{ height: 60 }}
      navbar={{
        width: 300,
        breakpoint: "sm",
        collapsed: { mobile: !opened },
      }}
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <div>Logo</div>
          </Group>
          <Group>
            {/* <SearchBar /> */}
            <SpotlightSearch />
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar>
        <NavbarNested />
      </AppShell.Navbar>

      <AppShell.Main>
        {children}
      </AppShell.Main>
    </AppShell>
  );
}

export default Layout;
