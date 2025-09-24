import "@mantine/core/styles.css";
import "@mantine/dates/styles.css";
import "@mantine/notifications/styles.css";

import { MantineProvider } from "@mantine/core";
import { ModalsProvider } from "@mantine/modals";
import { BrowserRouter, Route, Routes } from "react-router";

import Layout from "./components/Layout/Layout.tsx";

import Library from "./pages/Library.tsx";
// import Vite from "./Vite.tsx";

function App() {
  return (
    <MantineProvider defaultColorScheme="auto">
      <ModalsProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Library />} />
              <Route path="/series/:id" element={<div>Series Detail Page - To Be Implemented</div>} />
              <Route path="/book/:id" element={<div>Book Detail Page - To Be Implemented</div>} />
              <Route path="*" element={<div>404 Not Found</div>} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ModalsProvider>
    </MantineProvider>
  );
}

export default App;
