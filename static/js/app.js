/* ============================================================
   Real Estate AI — Front-End JavaScript
   Handles chat (text + voice), filter search, listing cards,
   and the contact-agent modal.
   ============================================================ */

"use strict";

// ---------- DOM refs ----------
const chatHistory   = document.getElementById("chat-history");
const chatInput     = document.getElementById("chat-input");
const sendBtn       = document.getElementById("send-btn");
const micBtn        = document.getElementById("mic-btn");
const micStatus     = document.getElementById("mic-status");
const filterForm    = document.getElementById("filter-form");
const resultsSection= document.getElementById("results-section");
const resultsGrid   = document.getElementById("results-grid");
const contactModal  = document.getElementById("contact-modal");
const contactForm   = document.getElementById("contact-form");
const contactResult = document.getElementById("contact-result");
const modalClose    = document.getElementById("modal-close");
const modalListingInfo = document.getElementById("modal-listing-info");
const contactListingId = document.getElementById("contact-listing-id");

// ---------- Web Speech API ----------
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;
const synth = window.speechSynthesis;
let recognition = null;
let isListening = false;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    micStatus.textContent = "";
    chatInput.value = transcript;
    stopListening();
    sendMessage(transcript);
  };

  recognition.onspeechend = () => stopListening();
  recognition.onerror = (e) => {
    micStatus.textContent = `Mic error: ${e.error}`;
    stopListening();
  };
} else {
  micBtn.title = "Voice input not supported in this browser";
  micBtn.style.opacity = "0.4";
  micBtn.disabled = true;
}

function startListening() {
  if (!recognition) return;
  isListening = true;
  micBtn.classList.add("listening");
  micStatus.textContent = "Listening… speak now";
  recognition.start();
}

function stopListening() {
  isListening = false;
  micBtn.classList.remove("listening");
  micStatus.textContent = "";
  try { recognition.stop(); } catch (_) {}
}

micBtn.addEventListener("click", () => {
  if (isListening) { stopListening(); } else { startListening(); }
});

// ---------- TTS helper ----------
function speak(text) {
  if (!synth) return;
  synth.cancel();
  const utt = new SpeechSynthesisUtterance(text.slice(0, 400));
  utt.rate = 0.95;
  synth.speak(utt);
}

// ---------- Chat ----------
function appendBubble(text, role) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  div.textContent = text;
  chatHistory.appendChild(div);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function sendMessage(text) {
  text = text.trim();
  if (!text) return;
  appendBubble(text, "user");
  chatInput.value = "";
  sendBtn.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    const reply = data.reply || "Sorry, I had trouble understanding that.";
    appendBubble(reply, "bot");
    speak(reply);
    if (data.listings && data.listings.length > 0) {
      renderListings(data.listings);
    }
  } catch (err) {
    appendBubble("Network error. Please try again.", "bot");
  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

sendBtn.addEventListener("click", () => sendMessage(chatInput.value));
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage(chatInput.value);
});

// ---------- Filter form ----------
filterForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const params = new URLSearchParams();
  new FormData(filterForm).forEach((val, key) => {
    if (val) params.append(key, val);
  });

  try {
    const res = await fetch(`/api/search?${params}`);
    const data = await res.json();
    if (data.listings && data.listings.length > 0) {
      renderListings(data.listings);
      appendBubble(
        `Found ${data.count} listing(s) matching your filters.`,
        "bot"
      );
    } else {
      appendBubble("No listings matched your filters. Try broadening your search.", "bot");
      resultsSection.hidden = true;
    }
  } catch (err) {
    appendBubble("Search error. Please try again.", "bot");
  }
});

// ---------- Listing cards ----------
function badge(label, type) {
  return `<span class="badge badge-${type}">${label}</span>`;
}

/** Return true if a listing field is an accepted truthy flag (not false/null/empty). */
function isTruthy(val) {
  return val === true || val === "True" || val === "true";
}

/** Return utility string if included, or empty string. */
function utilitiesLabel(val) {
  if (!val || val === false || val === "false" || val === "None" || val === "") return "";
  if (val === true || val === "true" || val === "True") return "";
  return "✓ Utilities: " + val;
}

function renderListings(listings) {
  resultsGrid.innerHTML = "";
  listings.forEach((l) => {
    const badges = [];
    if (isTruthy(l.section8_accepted))  badges.push(badge("Section 8", "green"));
    if (isTruthy(l.hud_approved))       badges.push(badge("HUD Approved", "blue"));
    if (isTruthy(l.low_income_eligible))badges.push(badge("Low Income", "purple"));
    if (isTruthy(l.nearby_transit))     badges.push(badge("🚌 Transit", "orange"));

    const card = document.createElement("div");
    card.className = "listing-card";
    card.innerHTML = `
      <div class="price">$${Number(l.monthly_rent).toLocaleString()}<span style="font-size:0.85rem;font-weight:400">/mo</span></div>
      <div class="address">${l.address}<br/>${l.city}, ${l.state} ${l.zip_code}</div>
      <div style="font-size:0.82rem;color:#4a5568;margin:0.25rem 0">
        ${l.bedrooms} bd · ${l.bathrooms} ba · ${l.sqft || "—"} sqft · ${l.property_type}
      </div>
      <div class="badges">${badges.join("")}</div>
      <div style="font-size:0.82rem;color:#4a5568">
        Languages: ${l.languages_spoken || "English"}<br/>
        ${utilitiesLabel(l.utilities_included)}
      </div>
      <div class="agent-info">
        Agent: ${l.agent_name}<br/>
        <a href="tel:${l.agent_phone}">${l.agent_phone}</a> ·
        <a href="mailto:${l.agent_email}">${l.agent_email}</a>
      </div>
      <button
        class="btn btn-primary contact-btn"
        data-id="${l.id}"
        data-address="${l.address}, ${l.city}"
        data-agent="${l.agent_name}"
      >Contact Agent</button>
    `;
    resultsGrid.appendChild(card);
  });

  resultsSection.hidden = false;
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

  // Bind contact buttons
  resultsGrid.querySelectorAll(".contact-btn").forEach((btn) => {
    btn.addEventListener("click", () => openContactModal(
      btn.dataset.id,
      btn.dataset.address,
      btn.dataset.agent
    ));
  });
}

// ---------- Contact modal ----------
function openContactModal(listingId, address, agentName) {
  contactListingId.value = listingId;
  modalListingInfo.textContent =
    `Property: ${address} · Agent: ${agentName}`;
  contactResult.textContent = "";
  contactResult.className = "contact-result";
  contactModal.hidden = false;
  document.getElementById("contact-name").focus();
}

modalClose.addEventListener("click", () => { contactModal.hidden = true; });
contactModal.addEventListener("click", (e) => {
  if (e.target === contactModal) contactModal.hidden = true;
});

contactForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    listing_id: contactListingId.value,
    user_name: document.getElementById("contact-name").value,
    user_phone: document.getElementById("contact-phone").value,
    user_email: document.getElementById("contact-email").value,
    language: document.getElementById("contact-language").value,
    method: document.getElementById("contact-method").value,
  };

  try {
    const res = await fetch("/api/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.success) {
      contactResult.textContent =
        "✓ Agent has been contacted! They will reach out to you soon.";
      contactResult.className = "contact-result success";
    } else {
      contactResult.textContent =
        `Note: ${data.error || "Could not reach the agent automatically."} ` +
        "Please contact them directly using the phone/email shown on the listing.";
      contactResult.className = "contact-result error";
    }
  } catch (err) {
    contactResult.textContent = "Network error. Please try again.";
    contactResult.className = "contact-result error";
  }
});

// ---------- Initial welcome ----------
appendBubble(
  "Hi! I'm your Real Estate AI Assistant. I help immigrants and minorities find affordable housing. " +
  "Tell me what you're looking for — budget, location, bedrooms, special needs, or preferred language.",
  "bot"
);
