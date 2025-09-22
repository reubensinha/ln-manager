import "@mantine/core/styles.css";
import "@mantine/dates/styles.css";
import "@mantine/notifications/styles.css";

import { MantineProvider } from "@mantine/core";
import { ModalsProvider } from "@mantine/modals";
import Layout from "./components/Layout/Layout.tsx";

import Vite from "./Vite.tsx";
import { BrowserRouter, Route, Routes } from "react-router";

function App() {
  return (
    <MantineProvider>
      <ModalsProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Vite />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ModalsProvider>
    </MantineProvider>
  );
}

export default App;
