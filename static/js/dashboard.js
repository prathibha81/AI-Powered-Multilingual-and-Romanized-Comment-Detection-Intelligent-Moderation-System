(function () {
  "use strict";
  const data = window.analysisData;
  if (!data) return;
  const comments = data.comments || [];
  const pageSize = 20;
  let currentFilter = "ALL";
  let currentPage = 1;

  const canvas = document.getElementById("toxicity-chart");
  if (canvas && window.Chart) {
    new Chart(canvas, {
      type: "doughnut",
      data: { labels: ["Toxic", "Non-toxic"], datasets: [{ data: [data.toxic_comments, data.non_toxic_comments], backgroundColor: ["#ef6b5f", "#3fb49b"], borderWidth: 0, hoverOffset: 4 }] },
      options: { responsive: true, cutout: "77%", plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => ` ${context.label}: ${context.raw}` } } } },
    });
  }

  function filteredComments() {
    const query = (document.getElementById("comment-search")?.value || "").toLowerCase().trim();
    return comments.filter((comment) => (currentFilter === "ALL" || comment.label === currentFilter) && comment.text.toLowerCase().includes(query));
  }

  function render() {
    const visible = filteredComments();
    const pages = Math.max(1, Math.ceil(visible.length / pageSize));
    currentPage = Math.min(currentPage, pages);
    const start = (currentPage - 1) * pageSize;
    const rows = visible.slice(start, start + pageSize);
    const body = document.getElementById("comments-body");
    const empty = document.getElementById("comments-empty");
    body.replaceChildren();
    rows.forEach((comment) => {
      const row = document.createElement("tr");
      const commentCell = document.createElement("td");
      commentCell.className = "comment-cell";
      commentCell.textContent = comment.text;
      const labelCell = document.createElement("td");
      const badge = document.createElement("span");
      badge.className = `classification-badge ${comment.label === "TOXIC" ? "toxic-badge" : "safe-badge"}`;
      badge.textContent = comment.label;
      labelCell.appendChild(badge);
      const confidence = document.createElement("td");
      confidence.className = "confidence-cell";
      confidence.textContent = `${Math.round(comment.confidence * 100)}%`;
      const author = document.createElement("td");
      author.className = "author-cell";
      author.textContent = comment.username ? `@${comment.username}` : "—";
      row.append(commentCell, labelCell, confidence, author);
      body.appendChild(row);
    });
    empty.hidden = rows.length > 0;
    renderPagination(pages, visible.length);
  }

  function renderPagination(pages, count) {
    const target = document.getElementById("pagination");
    target.replaceChildren();
    if (count <= pageSize) return;
    const previous = document.createElement("button");
    previous.textContent = "← Previous";
    previous.disabled = currentPage === 1;
    previous.addEventListener("click", () => { currentPage--; render(); });
    target.appendChild(previous);
    for (let page = 1; page <= pages; page += 1) {
      const button = document.createElement("button");
      button.textContent = page;
      button.className = page === currentPage ? "current" : "";
      button.addEventListener("click", () => { currentPage = page; render(); });
      target.appendChild(button);
    }
    const next = document.createElement("button");
    next.textContent = "Next →";
    next.disabled = currentPage === pages;
    next.addEventListener("click", () => { currentPage++; render(); });
    target.appendChild(next);
  }

  document.getElementById("comment-search")?.addEventListener("input", () => { currentPage = 1; render(); });
  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      currentFilter = button.dataset.filter;
      currentPage = 1;
      document.querySelectorAll("[data-filter]").forEach((item) => item.classList.toggle("active", item === button));
      render();
    });
  });
  render();
})();
