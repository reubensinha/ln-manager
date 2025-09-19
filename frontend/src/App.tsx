import { Routes, Route } from "react-router";
import Test from "./pages/test_page.tsx";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Test />} />
      {/* Add more routes as needed */}
    </Routes>
  );
}

export default App;