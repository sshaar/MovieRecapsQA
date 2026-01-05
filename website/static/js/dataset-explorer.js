// -------------------------------
// 2. Helper: Local video path builder
// -------------------------------
function buildLocalVideoPath(videoId, start, end) {
  return {
    src: `static/data/videos/${videoId}.mp4`,
    start: start || 0,
    end: end || null
  };
}

function stripSRT(srtText) {
  return srtText
    // Remove pure index lines (1, 2, 3…)
    .replace(/^\s*\d+\s*$/gm, "")
    // Remove timestamp lines
    .replace(/\d{2}:\d{2}:\d{2},\d{3}.*$/gm, "")
    // Remove leftover leading numbers before text (e.g., "1 Why…")
    .replace(/^\s*\d+\s+(?=[A-Za-z])/gm, "")
    // Collapse extra blank lines
    .replace(/\n{2,}/g, "\n")
    .trim();
}


// -------------------------------
// 3. Render Example List
// -------------------------------
function renderVideoList(listEl, videos) {
  listEl.innerHTML = "";
  videos.forEach((vid, idx) => {
    const li = document.createElement("li");

    const btn = document.createElement("button");
    btn.textContent = `${idx + 1}. ${vid.movie}`;
    btn.dataset.videoId = vid.id;

    li.appendChild(btn);
    listEl.appendChild(li);
  });
}


// -------------------------------
// 4. Render Example Detail
// -------------------------------
function renderVideoDetail(containerEl, video, activeQuestionIdx = 0) {
  if (!video) {
    containerEl.innerHTML = "<p>Select a video from the left panel.</p>";
    return;
  }

  const q = video.questions[activeQuestionIdx];

  const videoInfo = buildLocalVideoPath(
    video.videoId,
    video.startTime,
    video.endTime
  );

  // Question tabs
  const tabsHtml = video.questions
    .map(
      (qv, i) => `
      <button class="mrq-qtab ${i === activeQuestionIdx ? "active" : ""}"
              data-qindex="${i}">${i + 1}</button>
    `
    )
    .join("");

  // Facts stay constant for the video
  const factsHtml = video.facts
    .map((f, idx) => {
      const isUsed = (q.factsUsed || []).includes(idx);
      return `<li class="${isUsed ? "mrq-fact-used" : ""}">${f}</li>`;
    })
    .join("");


  // Model answers
  const modelRows = q.modelAnswers
    .map(
      m => `
        <tr>
          <td><strong>${m.model}</strong></td>
          <td>${m.answer}</td>
          <td>${m.scores?.factuality ?? "—"}</td>
          <td>${m.scores?.relevance ?? "—"}</td>
        </tr>
      `
    )
    .join("");

  // Human row
  const humanRow = `
    <tr class="mrq-human-row">
      <td><strong>Human</strong></td>
      <td>${q.humanAnswer?.answer ?? ""}</td>
      <td>${q.humanAnswer?.scores?.factuality ?? "—"}</td>
      <td>${q.humanAnswer?.scores?.relevance ?? "—"}</td>
    </tr>
  `;



  // Render with new strict ordering
  containerEl.innerHTML = `
    <h3 class="title is-4">${video.movie}</h3>

    <!-- Question Tabs -->
    <div class="mrq-question-tabs">${tabsHtml}</div>

    <div class="mrq-section-title">Recap Video & Dialogue</div>
      <div class="mrq-video-dialogue-grid">

          <!-- LEFT: Video -->
          <div class="mrq-video-frame">
              <video id="mrq-video-player" width="100%" height="360" controls>
                  <source src="${videoInfo.src}" type="video/mp4">
                  Your browser does not support the video tag.
              </video>
          </div>

          <!-- RIGHT: Dialogue -->
          <div class="mrq-dialogue-box">
              <div class="mrq-dialogue-title">Dialogue</div>
              <div class="mrq-dialogue-list">
                  ${(video.srt || q.srt)
      ? stripSRT(video.srt || q.srt)
        .split("\n")
        .filter(line => line.trim() !== "")
        .map(line => `<div class="mrq-dialogue-bubble">${line}</div>`)
        .join("")
      : "<p>No dialogue available.</p>"
    }
              </div>
          </div>

      </div>
    </div>



   <!-- Question + Dataset Answer Row -->
    <div class="mrq-qa-row">
      <div class="mrq-qa-block">
        <h4>Question</h4>
        <p>${q.question}</p>
      </div>

      <div class="mrq-qa-block">
        <h4>Dataset Answer</h4>
        <p>${q.datasetAnswer}</p>
      </div>
    </div>



    <!-- 2. Facts -->
    <div class="mrq-section-title">Facts</div>
    <ul class="mrq-facts-list">
      ${factsHtml}
    </ul>

    <!-- 6. Model Answers -->
    <div class="mrq-section-title">Model Answers</div>
    <table class="mrq-model-table">
      <thead>
        <tr>
          <th>Model</th>
          <th>Answer</th>
          <th>Factuality</th>
          <th>Relevance</th>
        </tr>
      </thead>
      <tbody>
        ${humanRow}
        ${modelRows}
      </tbody>
    </table>
  `;
  
  // Set up video player with start/end times
  setTimeout(() => {
    const videoPlayer = document.getElementById("mrq-video-player");
    if (videoPlayer) {
      videoPlayer.currentTime = videoInfo.start;
      
      if (videoInfo.end) {
        videoPlayer.addEventListener("timeupdate", function checkEndTime() {
          if (videoPlayer.currentTime >= videoInfo.end) {
            videoPlayer.pause();
            videoPlayer.removeEventListener("timeupdate", checkEndTime);
          }
        });
      }
    }
  }, 0);
}



// -------------------------------
// 5. Initialize the Explorer
// -------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const listEl = document.getElementById("mrq-example-list");
  const detailEl = document.getElementById("mrq-example-detail");

  renderVideoList(listEl, mrqVideos);

  // Auto-select first video
  window.currentVideoId = mrqVideos[0].id;
  renderVideoDetail(detailEl, mrqVideos[0], 0);

  // click handlers (left column)
  listEl.addEventListener("click", evt => {
    const btn = evt.target.closest("button");
    if (!btn) return;

    window.currentVideoId = btn.dataset.videoId;

    const video = mrqVideos.find(v => v.id === window.currentVideoId);
    renderVideoDetail(detailEl, video, 0);

    listEl.querySelectorAll("button").forEach(b => b.classList.remove("mrq-active"));
    btn.classList.add("mrq-active");
  });
});

document.addEventListener("click", evt => {
  const tab = evt.target.closest(".mrq-qtab");
  if (!tab) return;

  const video = mrqVideos.find(v => v.id === window.currentVideoId);
  const qIdx = parseInt(tab.dataset.qindex);

  // Only question-specific sections rerender
  renderVideoDetail(
    document.getElementById("mrq-example-detail"),
    video,
    qIdx
  );
});