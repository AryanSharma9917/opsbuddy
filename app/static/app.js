const form = document.querySelector("#analysis-form");
const details = document.querySelector("#details");
const characterCount = document.querySelector("#character-count");
const submitButton = document.querySelector("#submit-button");
const formMessage = document.querySelector("#form-message");
const result = document.querySelector("#result");
const resultContent = document.querySelector("#result-content");

details.addEventListener("input", () => {
  characterCount.textContent = `${details.value.length.toLocaleString()} / 12,000`;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  formMessage.textContent = "";
  result.hidden = true;
  submitButton.disabled = true;
  submitButton.querySelector("span:first-child").textContent = "Taking a look…";

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        issue_type: document.querySelector("#issue-type").value,
        details: details.value,
      }),
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.detail || "The analysis could not be completed.");
    }

    renderResult(payload);
    result.hidden = false;
    result.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    formMessage.textContent = error.message;
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector("span:first-child").textContent = "Help me understand this";
  }
});

function renderResult(analysis) {
  resultContent.replaceChildren();
  resultContent.append(
    makeSection("In brief", [analysis.summary]),
    makeSection("Possible causes", analysis.likely_causes),
    makeSection("What to check next", analysis.next_steps),
    makeSection("Commands to review", analysis.commands, true),
    makeSection("A note on safety", [analysis.safety_note]),
  );
}

function makeSection(title, items, isCode = false) {
  const section = document.createElement("section");
  section.className = "answer-section";
  const heading = document.createElement("h3");
  heading.textContent = title;
  section.append(heading);

  const list = document.createElement("ul");
  for (const item of items) {
    const row = document.createElement("li");
    if (isCode) {
      const code = document.createElement("code");
      code.textContent = item;
      row.append(code);
    } else {
      row.textContent = item;
    }
    list.append(row);
  }
  section.append(list);
  return section;
}
