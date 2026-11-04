import { useState, lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router";
import JoinPage from "./pages/JoinPage";
import PageLoader from "./components/PageLoader";
import { getSession } from "./lib/session";

// Lazy-load heavy pages (Stream SDKs) so the join screen loads instantly
const HomePage = lazy(() => import("./pages/HomePage"));
const CallPage = lazy(() => import("./pages/CallPage"));
// The standalone translator needs no account and no Stream SDK
const TranslatorPage = lazy(() => import("./pages/TranslatorPage"));

const App = () => {
  const [session, setSession] = useState(getSession);

  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/translator" element={<TranslatorPage />} />
        {session ? (
          <>
            <Route path="/" element={<HomePage session={session} onLogout={() => setSession(null)} />} />
            <Route path="/call/:id" element={<CallPage session={session} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </>
        ) : (
          <Route path="*" element={<JoinPage onJoin={setSession} />} />
        )}
      </Routes>
    </Suspense>
  );
};

export default App;
