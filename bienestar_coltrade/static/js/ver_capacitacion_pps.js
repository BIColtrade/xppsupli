document.addEventListener("DOMContentLoaded", () => {
  const state = document.getElementById("ppsVideoState");
  if (!state) return;

  const progressFill = document.getElementById("progressFill");
  const progressPct = document.getElementById("progressPct");
  const pointsEarned = document.getElementById("pointsEarned");
  const videoError = document.getElementById("videoError");

  const initialPct = Number(state.dataset.initialPct || 0);
  let lastSent = initialPct;

  const csrfToken =
    document.querySelector("#csrfToken input[name=csrfmiddlewaretoken]")?.value || "";
  const updateUrl = state.dataset.updateUrl || "";
  const videoId = state.dataset.videoId || "";

  const updateUI = (pct, points) => {
    if (typeof pct === "number") {
      const safePct = Math.max(0, Math.min(100, Math.floor(pct)));
      if (progressPct) progressPct.textContent = `${safePct}%`;
      if (progressFill) progressFill.style.width = `${safePct}%`;
    }
    if (typeof points === "number" && pointsEarned) {
      pointsEarned.textContent = points;
    }
  };

  const sendProgress = (pct) => {
    if (!updateUrl || pct <= lastSent) return;
    lastSent = pct;

    const body = new URLSearchParams();
    body.append("progreso", pct);

    fetch(updateUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": csrfToken,
      },
      body: body.toString(),
    })
      .then((resp) => resp.json())
      .then((data) => {
        if (data && typeof data.progreso_pct === "number") {
          updateUI(data.progreso_pct, data.puntos_otorgados);
        }
      })
      .catch(() => {});
  };

  let player;
  let progressTimer = null;
  let maxWatchedTime = 0;
  let lastVideoTime = 0;
  let lastWallTime = null;

  const checkProgress = () => {
    if (!player || typeof player.getDuration !== "function") return;
    const duration = player.getDuration();
    if (!duration) return;

    const current = player.getCurrentTime();
    const now = Date.now();
    const dt = lastWallTime ? (now - lastWallTime) / 1000 : 0;
    lastWallTime = now;
    const allowAhead = Math.max(2.5, dt + 2);

    if (maxWatchedTime > 0 && current > maxWatchedTime + allowAhead) {
      player.seekTo(maxWatchedTime, true);
      lastVideoTime = maxWatchedTime;
      lastWallTime = Date.now();
      return;
    }

    if (current > maxWatchedTime) {
      maxWatchedTime = current;
    }
    lastVideoTime = current;

    const pct = Math.min(100, Math.floor((maxWatchedTime / duration) * 100));
    updateUI(pct);
    sendProgress(pct);
  };

  const startTracking = () => {
    if (!progressTimer) {
      lastWallTime = Date.now();
      if (player && typeof player.getCurrentTime === "function") {
        lastVideoTime = player.getCurrentTime();
        if (lastVideoTime > maxWatchedTime) {
          maxWatchedTime = lastVideoTime;
        }
      }
      checkProgress();
      progressTimer = setInterval(checkProgress, 5000);
    }
  };

  const stopTracking = () => {
    if (progressTimer) {
      clearInterval(progressTimer);
      progressTimer = null;
      lastWallTime = null;
    }
  };

  const onPlayerStateChange = (event) => {
    if (event.data === window.YT?.PlayerState?.PLAYING) {
      startTracking();
    } else if (event.data === window.YT?.PlayerState?.ENDED) {
      checkProgress();
      stopTracking();
    } else {
      stopTracking();
    }
  };

  const onPlayerReady = () => {
    const duration = player?.getDuration?.();
    if (duration) {
      maxWatchedTime = Math.max(0, Math.min(duration, (initialPct / 100) * duration));
      lastVideoTime = maxWatchedTime;
    }
  };

  const onPlayerError = () => {
    if (videoError) {
      videoError.style.display = "block";
    }
  };

  const createPlayer = () => {
    if (!videoId || !window.YT || !window.YT.Player) return;
    player = new window.YT.Player("player", {
      videoId,
      playerVars: { rel: 0, origin: window.location.origin, disablekb: 1 },
      events: {
        onReady: onPlayerReady,
        onStateChange: onPlayerStateChange,
        onError: onPlayerError,
      },
    });
  };

  window.onYouTubeIframeAPIReady = createPlayer;
  if (window.YT && window.YT.Player) {
    createPlayer();
  }

  updateUI(initialPct);
});
