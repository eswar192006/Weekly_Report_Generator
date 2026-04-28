const form = document.getElementById("upload-form");
const reportSummary = document.getElementById("report-summary");
const kpiGrid = document.getElementById("kpi-grid");
const chartsContainer = document.getElementById("charts");
const insightsContainer = document.getElementById("insights");
const resultsSection = document.querySelector(".results");
const toast = document.getElementById("toast");
const htmlLink = document.getElementById("html-link");
const loadSampleButton = document.getElementById("load-sample");
const fileInput = form.querySelector("input[name='file']");
const filePlaceholder = document.getElementById("file-placeholder");
const selectedFileName = document.getElementById("selected-file-name");
const removeFileButton = document.getElementById("remove-file");

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3200);
}

function clearReport() {
  reportSummary.textContent = "";
  kpiGrid.innerHTML = "";
  chartsContainer.innerHTML = "";
  insightsContainer.innerHTML = "";
}

function updateSelectedFileName() {
  const hasFile = fileInput.files.length > 0;
  selectedFileName.textContent = hasFile ? fileInput.files[0].name : "";
  selectedFileName.hidden = !hasFile;
  removeFileButton.hidden = !hasFile;
  filePlaceholder.hidden = hasFile;
}

function clearSelectedFile(event) {
  if (event) {
    event.stopPropagation();
  }
  fileInput.value = "";
  updateSelectedFileName();
}

function populateReport(report) {
  reportSummary.textContent = report.summary || "No summary available.";
  kpiGrid.innerHTML = "";
  Object.entries(report.kpis || {}).forEach(([key, value]) => {
    const card = document.createElement("div");
    card.className = "kpi-card";
    card.innerHTML = `<h3>${key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</h3><p>${value}</p>`;
    kpiGrid.appendChild(card);
  });

  chartsContainer.innerHTML = "";
  (report.charts || []).forEach(chart => {
    const frame = document.createElement("div");
    frame.className = "chart-frame";
    frame.innerHTML = `<h3>${chart.title}</h3><img src="${chart.url}" alt="${chart.title}" />`;
    chartsContainer.appendChild(frame);
  });

  insightsContainer.innerHTML = "";
  (report.insights || []).forEach(insight => {
    const pill = document.createElement("div");
    pill.className = "insight-pill";
    pill.textContent = insight;
    insightsContainer.appendChild(pill);
  });

  htmlLink.href = report.report_url || "#";
  htmlLink.textContent = report.report_url ? "Open HTML Report" : "HTML report not available";
  resultsSection.hidden = false;
}

form.addEventListener("submit", async event => {
  event.preventDefault();

  if (!fileInput.files.length) {
    showToast("Please upload a CSV file first.");
    return;
  }

  clearReport();
  showToast("Generating report — this may take a moment...");

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Upload failed.");
    }

    const report = await response.json();
    populateReport(report);
    showToast("Report generated successfully.");
  } catch (error) {
    showToast(error.message);
  }
});

fileInput.addEventListener("change", updateSelectedFileName);
removeFileButton.addEventListener("click", clearSelectedFile);

loadSampleButton.addEventListener("click", async () => {
  const sampleUrl = "/sample_data/sales_sample.csv";
  try {
    const response = await fetch(sampleUrl);
    if (!response.ok) throw new Error("Cannot load sample file.");
    const blob = await response.blob();
    const file = new File([blob], "sales_sample.csv", { type: "text/csv" });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;
    updateSelectedFileName();
    showToast("Sample dataset loaded. Ready to generate report.");
  } catch (error) {
    showToast(error.message);
  }
});
