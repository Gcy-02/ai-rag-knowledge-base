const uploadForm = document.querySelector("#upload-form");
const askForm = document.querySelector("#ask-form");
const uploadStatus = document.querySelector("#upload-status");
const documentList = document.querySelector("#document-list");
const answerBox = document.querySelector("#answer");
const citationsBox = document.querySelector("#citations");
const questionInput = document.querySelector("#question");
const recallList = document.querySelector("#recall-list");
const documentCount = document.querySelector("#document-count");
const chunkCount = document.querySelector("#chunk-count");
const topK = document.querySelector("#top-k");

async function loadDocuments() {
  const response = await fetch("/documents");
  const data = await response.json();
  documentList.innerHTML = "";

  data.documents.forEach((name) => {
    const item = document.createElement("li");
    item.textContent = name;
    documentList.appendChild(item);
  });
}

async function loadStats() {
  const response = await fetch("/stats");
  const data = await response.json();
  documentCount.textContent = data.document_count;
  chunkCount.textContent = data.chunk_count;
  topK.textContent = data.top_k;
}

function renderRecall(contexts) {
  recallList.innerHTML = "";

  if (!contexts.length) {
    recallList.innerHTML = '<div class="empty-state">没有召回到知识块。</div>';
    return;
  }

  contexts.forEach((context) => {
    const item = document.createElement("div");
    item.className = "recall-item";

    const score = Math.max(0, Math.min(1, Number(context.score) || 0));
    const percent = Math.round(score * 100);
    const snippet = context.text.length > 180 ? `${context.text.slice(0, 180)}...` : context.text;

    const head = document.createElement("div");
    head.className = "recall-head";

    const title = document.createElement("strong");
    title.textContent = `#${context.rank} ${context.source}`;

    const meta = document.createElement("span");
    meta.textContent = `${context.location} · ${percent}%`;

    const bar = document.createElement("div");
    bar.className = "score-bar";

    const fill = document.createElement("i");
    fill.style.width = `${percent}%`;

    const text = document.createElement("p");
    text.textContent = snippet;

    head.append(title, meta);
    bar.appendChild(fill);
    item.append(head, bar, text);
    recallList.appendChild(item);
  });
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fileInput = document.querySelector("#pdf-file");
  const file = fileInput.files[0];

  if (!file) {
    uploadStatus.textContent = "请先选择一个 PDF 文件。";
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  uploadStatus.textContent = "正在上传并等待索引刷新...";

  try {
    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "上传失败。");
    }

    uploadStatus.textContent = data.message;
    fileInput.value = "";
    await loadDocuments();
    await loadStats();
  } catch (error) {
    uploadStatus.textContent = error.message;
  }
});

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();

  if (!question) {
    answerBox.textContent = "请先输入问题。";
    return;
  }

  answerBox.textContent = "正在检索知识库并生成回答...";
  citationsBox.innerHTML = "<li>检索中...</li>";
  recallList.innerHTML = '<div class="empty-state">正在计算 Top-K 召回...</div>';

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "问答失败。");
    }

    answerBox.textContent = data.answer;
    citationsBox.innerHTML = "";

    data.citations.forEach((citation) => {
      const item = document.createElement("li");
      item.textContent = `${citation.source} · ${citation.location}`;
      citationsBox.appendChild(item);
    });
    renderRecall(data.contexts);
  } catch (error) {
    answerBox.textContent = error.message;
    citationsBox.innerHTML = "<li>暂无引用来源</li>";
    recallList.innerHTML = '<div class="empty-state">暂无召回结果</div>';
  }
});

loadDocuments();
loadStats();
