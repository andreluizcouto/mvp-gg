import { useEffect, useState } from "react"
import { fetchLiveGame } from "./api"

const POLL_MS = 60_000

// Consulta a partida ao vivo ao abrir o perfil e de novo a cada minuto enquanto a aba está visível.
export function useLiveGame(nick) {
  const [live, setLive] = useState(null)

  useEffect(() => {
    let alive = true
    setLive(null)

    function check() {
      if (document.visibilityState === "hidden") return
      fetchLiveGame(nick)
        .then(data => { if (alive) setLive(data?.in_game ? data : null) })
        .catch(() => {})
    }

    check()
    const timer = setInterval(check, POLL_MS)
    document.addEventListener("visibilitychange", check)
    return () => {
      alive = false
      clearInterval(timer)
      document.removeEventListener("visibilitychange", check)
    }
  }, [nick])

  return live
}
