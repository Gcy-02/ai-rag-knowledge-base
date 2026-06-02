const uploadForm = document.querySelector("#upload-form");
const askForm = document.querySelector("#ask-form");
const uploadStatus = document.querySelector("#upload-status");
const documentList = document.querySelector("#document-list");
const answerBox = document.querySelector("#answer");
const citationsBox = document.querySelector("#citations");
const questionInput = document.querySelector("#question");

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
  } catch (error) {
    answerBox.textContent = error.message;
    citationsBox.innerHTML = "<li>暂无引用来源</li>";
  }
});

loadDocuments();
