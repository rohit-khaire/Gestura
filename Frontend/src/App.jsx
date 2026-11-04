import { useState, lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router";
import JoinPage from "./pages/JoinPage";
import PageLoader from "./components/PageLoader";
import { getSession } from "./lib/session";

// Lazy-load heavy pages (Stream SDKs) so the join screen loads instantly
const HomePage = lazy(() => import("./pages/HomePage"));
const CallPage = lazy(() => import("./pages/CallPage"));

const App = () => {
  const [session, setSession] = useState(getSession);

  if (!session) return <JoinPage onJoin={setSession} />;

  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<HomePage session={session} onLogout={() => setSession(null)} />} />
        <Route path="/call/:id" element={<CallPage session={session} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
};

export default App;
