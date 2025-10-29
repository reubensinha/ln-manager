import { Suspense, useEffect, useRef } from "react";

import "@mantine/core/styles.css";
import "@mantine/dates/styles.css";
import "@mantine/notifications/styles.css";
import '@mantine/spotlight/styles.css';
import 'mantine-datatable/styles.layer.css';

import { MantineProvider } from "@mantine/core";
import { ModalsProvider } from "@mantine/modals";
import { Notifications } from '@mantine/notifications';
import { BrowserRouter, Route, Routes } from "react-router";

import Layout from "./components/Layout/Layout.tsx";
import { websocketAPI } from "./api/websocket_api.ts";

import NothingFoundBackground from "./notfound/notfound.tsx";

import Library from "./pages/Library.tsx";
import SeriesPage from "./pages/SeriesPage.tsx";
import BookPage from "./pages/BookPage.tsx";
import Search from "./pages/Search.tsx";
import CalendarPage from "./pages/CalendarPage.tsx";
import NotificationsPage from "./pages/System/NotificationsPage.tsx";
import PluginsPage from "./pages/Settings/PluginsPage.tsx";
// import Vite from "./Vite.tsx";

import { pluginManifests } from "./plugin-manifests";

function App() {
  const hasConnected = useRef(false);
  
  useEffect(() => {

    if (!hasConnected.current) {
      hasConnected.current = true;
      websocketAPI.connect();
    }

    return () => {
      websocketAPI.disconnect();
    };
  }, []);


  return (
    <MantineProvider defaultColorScheme="auto">
      <Notifications />
      <ModalsProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              {/* Core Routes */}
              <Route path="/" element={<Library />} />
              <Route path="/series/:groupID" element={<SeriesPage />} />
              <Route path="/book/:bookID" element={<BookPage />} />
              <Route path="/search/:source" element={<Search />} />
              <Route path="/search/:source/:query" element={<Search />} />

              <Route path="/calendar" element={<CalendarPage />} />

              <Route path="/settings/plugins" element={<PluginsPage />} />

              <Route path="/system/notifications" element={<NotificationsPage />} />
              <Route path="*" element={<NothingFoundBackground />} />

              {/* Plugin Routes */}
              {pluginManifests.map((plugin) =>
                plugin.routes?.map((r) => (
                  <Route
                    key={r.path}
                    path={r.path}
                    element={
                      <Suspense fallback={<div>Loading...</div>}>
                        {r.element}
                      </Suspense>
                    }
                  />
                ))
              )}
            </Routes>
          </Layout>
        </BrowserRouter>
      </ModalsProvider>
    </MantineProvider>
  );
}

export default App;
