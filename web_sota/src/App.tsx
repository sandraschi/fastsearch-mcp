import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { Actions } from "@/pages/actions";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import Help from "@/pages/help";
import Logs from "@/pages/logs";
import { Search } from "@/pages/search";
import { Service } from "@/pages/service";
import { Settings } from "@/pages/settings";
import { Tests } from "@/pages/tests";
import { Tools } from "@/pages/tools";
import { TreemapPage } from "@/pages/treemap";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/search" element={<Search />} />
          <Route path="/treemap" element={<TreemapPage />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/service" element={<Service />} />
          <Route path="/tests" element={<Tests />} />
          <Route path="/actions" element={<Actions />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/help" element={<Help />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
