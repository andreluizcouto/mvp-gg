import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import Layout                from "./components/Layout"
import SearchScreen          from "./screens/SearchScreen"
import SummonerProfileScreen from "./screens/SummonerProfileScreen"
import ResultsScreen         from "./screens/ResultsScreen"
import TierlistScreen        from "./screens/TierlistScreen"
import LeaderboardScreen     from "./screens/LeaderboardScreen"
import HowItWorksScreen      from "./screens/HowItWorksScreen"
import DownloadScreen        from "./screens/DownloadScreen"
import TermsScreen           from "./screens/TermsScreen"
import PrivacyScreen         from "./screens/PrivacyScreen"
import LoginScreen           from "./screens/LoginScreen"
import DashboardScreen       from "./screens/DashboardScreen"
import { getSession }        from "./services/auth"

function RequireAuth({ children }) {
  const session = getSession()
  if (!session?.access_token) {
    return <Navigate to="/login" replace />
  }
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginScreen />} />
        <Route element={<Layout />}>
          <Route path="/"                    element={<SearchScreen />} />
          <Route path="/summoner/:name/:tag" element={<SummonerProfileScreen />} />
          <Route path="/match/:matchId"      element={<ResultsScreen />} />
          <Route path="/tierlist"            element={<TierlistScreen />} />
          <Route path="/leaderboard"         element={<LeaderboardScreen />} />
          <Route path="/how-it-works"        element={<HowItWorksScreen />} />
          <Route path="/download"            element={<DownloadScreen />} />
          <Route path="/terms"               element={<TermsScreen />} />
          <Route path="/privacy"             element={<PrivacyScreen />} />
          <Route path="/dashboard"           element={<RequireAuth><DashboardScreen /></RequireAuth>} />
          <Route path="*"                    element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
