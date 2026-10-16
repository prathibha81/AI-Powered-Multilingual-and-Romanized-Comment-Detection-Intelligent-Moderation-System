(function () {
  "use strict";

  const toastRegion = document.getElementById("toast-region");
  const loading = document.getElementById("analysis-loading");
  const errorBox = document.getElementById("analysis-error");
  const form = document.getElementById("analyze-form-element");

  function showToast(message, kind) {
    if (!toastRegion) return;
    const toast = document.createElement("div");
    toast.className = `toast ${kind || ""}`;
    toast.textContent = message;
    toastRegion.appendChild(toast);
    window.setTimeout(() => toast.remove(), 4000);
  }

  async function runAnalysis(endpoint, body) {
    if (loading) loading.hidden = false;
    if (errorBox) errorBox.hidden = true;
    const buttons = document.querySelectorAll("button");
    buttons.forEach((button) => (button.disabled = true));
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {}),
      });
      const payload = await response.json();
      if (!response.ok || !payload.success) throw new Error(payload.error || "Analysis failed.");
      window.location.assign(payload.detail_url);
    } catch (error) {
      if (errorBox) {
        errorBox.textContent = error.message;
        errorBox.hidden = false;
      } else {
        showToast(error.message, "error");
      }
    } finally {
      if (loading) loading.hidden = true;
      buttons.forEach((button) => (button.disabled = false));
    }
  }

  if (form) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const input = document.getElementById("instagram-url");
      const value = input.value.trim();
      if (!/^https?:\/\/(www\.)?(m\.)?instagram\.com\/.+/i.test(value)) {
        errorBox.textContent = "Enter a valid public Instagram post or reel URL.";
        errorBox.hidden = false;
        input.focus();
        return;
      }
      runAnalysis("/api/analyze", { url: value });
    });
  }

  document.querySelectorAll("[data-demo-button]").forEach((button) => {
    button.addEventListener("click", () => runAnalysis("/api/demo"));
  });

  document.querySelectorAll("[data-delete-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = button.dataset.deleteId;
      if (!window.confirm("Delete this saved analysis?")) return;
      const response = await fetch(`/api/analysis/${id}`, { method: "DELETE" });
      if (response.ok) {
        button.closest(".history-row").remove();
        showToast("Analysis deleted.");
      } else {
        showToast("Could not delete this analysis.", "error");
      }
    });
  });
})();
