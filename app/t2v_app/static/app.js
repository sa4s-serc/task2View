// Reload a progress page when the job has moved on.
const progress = document.querySelector("[data-poll]");
if (progress) {
  setInterval(async () => {
    const reply = await fetch(progress.dataset.poll).then(r => r.json()).catch(() => null);
    if (reply && String(reply.version) !== progress.dataset.version) location.reload();
  }, 3000);
}

// "Add another question" on the questions page.
const concerns = document.getElementById("concerns");
const add = document.getElementById("add-concern");
if (concerns && add) {
  add.addEventListener("click", () => {
    const index = concerns.dataset.next++;
    const html = document.getElementById("concern-template").innerHTML.replaceAll("__i__", index);
    concerns.insertAdjacentHTML("beforeend", html);
    concerns.lastElementChild.querySelector("input[type=text]").focus();
  });
}

// "Edit" on a field the agent filled in: show its input instead of the value.
for (const button of document.querySelectorAll(".field .edit")) {
  button.addEventListener("click", () => button.closest(".field").classList.add("open"));
}
