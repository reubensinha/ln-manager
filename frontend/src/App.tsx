import { Suspense } from "react";

import "@mantine/core/styles.css";
import "@mantine/dates/styles.css";
import "@mantine/notifications/styles.css";
import '@mantine/spotlight/styles.css';

import { MantineProvider } from "@mantine/core";
import { ModalsProvider } from "@mantine/modals";
import { BrowserRouter, Route, Routes } from "react-router";

import Layout from "./components/Layout/Layout.tsx";

import NothingFoundBackground from "./notfound/notfound.tsx";

import Library from "./pages/Library.tsx";
import SeriesPage from "./pages/SeriesPage.tsx";
import BookPage from "./pages/BookPage.tsx";
import Search from "./pages/Search.tsx";
import CalendarPage from "./pages/CalendarPage.tsx";
// import Vite from "./Vite.tsx";

import { pluginManifests } from "./plugin-manifests";

function App() {
  return (
    <MantineProvider defaultColorScheme="auto">
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
