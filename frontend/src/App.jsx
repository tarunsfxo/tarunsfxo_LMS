import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import ProblemList from "./components/ProblemList";
import Workspace from "./components/Workspace";
import AdminDashboard from "./components/AdminDashboard";
import Login from "./components/Login";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/coding" element={<ProblemList />} />
        <Route path="/coding/problem/:slug" element={<Workspace />} />
        <Route path="/admin/coding" element={<AdminDashboard />} />
        <Route path="*" element={<Navigate to="/coding" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
