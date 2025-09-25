import "@mantine/core/styles.css";
import "@mantine/dates/styles.css";
import "@mantine/notifications/styles.css";

import { MantineProvider } from "@mantine/core";
import { ModalsProvider } from "@mantine/modals";
import { BrowserRouter, Route, Routes } from "react-router";

import Layout from "./components/Layout/Layout.tsx";

import NothingFoundBackground from "./notfound/notfound.tsx";

import Library from "./pages/Library.tsx";
import Series from "./pages/Series.tsx";
import Book from "./pages/Book.tsx";
// import Vite from "./Vite.tsx";

function App() {
  return (
    <MantineProvider defaultColorScheme="auto">
      <ModalsProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Library />} />
              <Route path="/series/:groupID" element={<Series />} />
              <Route path="/book/:bookID" element={<Book />} />
              <Route path="*" element={<NothingFoundBackground />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ModalsProvider>
    </MantineProvider>
  );
}

export default App;
