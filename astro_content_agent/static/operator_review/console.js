(function () {
  const $ = (id) => document.getElementById(id);

  function showMsg(el, text, type) {
    el.textContent = text;
    el.className = "msg " + (type || "");
    el.hidden = !text;
  }

  function pillReady(ready) {
    const el = $("readinessPill");
    el.textContent = ready ? "Ready (no blocking errors)" : "Not ready";
    el.className = "status-pill " + (ready ? "ready" : "not-ready");
  }

  function renderChecks(checks) {
    const box = $("readinessChecks");
    box.innerHTML = "";
    const blockers = checks.filter((c) => c.status === "error");
    const warns = checks.filter((c) => c.status === "warning");
    const summary = $("readinessSummary");
    summary.textContent =
      blockers.length + " error(s), " + warns.length + " warning(s), " +
      (checks.length - blockers.length - warns.length) + " ok";

    checks.forEach((c) => {
      const div = document.createElement("div");
      div.className = "check " + (c.status === "ok" ? "ok" : c.status === "warning" ? "warning" : "error");
      div.innerHTML =
        '<div class="name">' +
        escapeHtml(c.name) +
        " · " +
        escapeHtml(c.status) +
        "</div>" +
        escapeHtml(c.message) +
        (c.hint ? "<div style='color:var(--muted);font-size:0.8rem;margin-top:0.25rem'>" + escapeHtml(c.hint) + "</div>" : "");
      box.appendChild(div);
    });
  }

  function escapeHtml(s) {
    if (!s) return "";
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function setContent(data) {
    $("outTitle").textContent = data.title || "—";
    $("outHook").textContent = data.hook || "—";
    $("outCaption").textContent = data.caption || "—";
    $("outCta").textContent = data.cta || "—";
    $("outHashtags").textContent = (data.hashtags_preview && data.hashtags_preview.length) ? data.hashtags_preview.join(" ") : "—";
    $("outStatus").textContent = data.status;
    $("outImageUrl").textContent = data.primary_image_public_url || "—";
    $("outStorageKey").textContent = data.primary_asset_storage_key || "—";
    $("outTextFallback").textContent = data.text_fallback || "—";

    pillReady(!!data.publish_readiness_ready);
    renderChecks(data.publish_readiness_checks || []);

    const dry = $("dryRunPre");
    if (data.dry_run) {
      dry.textContent = JSON.stringify(data.dry_run, null, 2);
    } else {
      dry.textContent = "No simulation (add Instagram account id above and reload).";
    }

    $("btnApprove").disabled = false;
    $("btnReject").disabled = false;
    $("lastDraftId").value = data.draft_id;
  }

  async function loadReview() {
    const draftId = $("draftId").value.trim();
    const adminKey = $("adminKey").value;
    const igId = $("igAccountId").value.trim();
    const msg = $("loadMsg");
    showMsg(msg, "", "");

    if (!draftId) {
      showMsg(msg, "Enter a draft id.", "error");
      return;
    }

    let url = "/api/v1/admin/drafts/" + encodeURIComponent(draftId) + "/review";
    if (igId) url += "?instagram_account_id=" + encodeURIComponent(igId);

    const headers = { Accept: "application/json" };
    if (adminKey) headers["X-Admin-Key"] = adminKey;

    $("btnLoad").disabled = true;
    try {
      const r = await fetch(url, { headers });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) {
        showMsg(msg, (body && body.detail) ? (typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)) : r.status + " " + r.statusText, "error");
        return;
      }
      setContent(body);
      showMsg(msg, "Loaded.", "ok");
    } catch (e) {
      showMsg(msg, String(e), "error");
    } finally {
      $("btnLoad").disabled = false;
    }
  }

  async function postJson(path, jsonBody) {
    const opts = { method: "POST", headers: { Accept: "application/json" } };
    if (jsonBody !== undefined && jsonBody !== null) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(jsonBody);
    }
    const r = await fetch(path, opts);
    const body = await r.json().catch(() => ({}));
    return { ok: r.ok, status: r.status, body };
  }

  async function approve() {
    const id = $("lastDraftId").value.trim() || $("draftId").value.trim();
    const msg = $("actionMsg");
    if (!id) {
      showMsg(msg, "Load a draft first.", "error");
      return;
    }
    $("btnApprove").disabled = true;
    const { ok, body } = await postJson("/api/v1/drafts/" + encodeURIComponent(id) + "/approve", undefined);
    if (ok) {
      showMsg(msg, "Approved. Status: " + (body.status || "ok"), "ok");
      await loadReview();
    } else {
      showMsg(msg, (body.detail && String(body.detail)) || "Approve failed", "error");
    }
    $("btnApprove").disabled = false;
  }

  async function reject() {
    const id = $("lastDraftId").value.trim() || $("draftId").value.trim();
    const msg = $("actionMsg");
    const reason = $("rejectReason").value.trim();
    if (!id) {
      showMsg(msg, "Load a draft first.", "error");
      return;
    }
    if (!reason) {
      showMsg(msg, "Enter a rejection reason.", "error");
      return;
    }
    $("btnReject").disabled = true;
    const { ok, body } = await postJson("/api/v1/drafts/" + encodeURIComponent(id) + "/reject", { reason: reason });
    if (ok) {
      showMsg(msg, "Rejected.", "ok");
      await loadReview();
    } else {
      showMsg(msg, (body.detail && String(body.detail)) || "Reject failed", "error");
    }
    $("btnReject").disabled = false;
  }

  document.addEventListener("DOMContentLoaded", function () {
    $("btnLoad").addEventListener("click", loadReview);
    $("btnApprove").addEventListener("click", approve);
    $("btnReject").addEventListener("click", reject);
    $("btnApprove").disabled = true;
    $("btnReject").disabled = true;
  });
})();
