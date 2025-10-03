async function fetchTasks() {
  const res = await fetch("/api/tasks");
  return (await res.json()).tasks;
}

function render(tasks) {
  const list = document.getElementById("taskList");
  list.innerHTML = "";
  tasks.forEach((t, i) => {
    const div = document.createElement("div");
    div.className = "task" + (t.done ? " done" : "");
    div.innerHTML = `
      <span class="title">${i+1}. ${t.title} — ${t.description || ""}</span>
      <div>
        <button onclick="toggleTask(${i+1})">${t.done ? "未完成" : "完成"}</button>
        <button onclick="editTask(${i+1})">编辑</button>
        <button class="delete" onclick="deleteTask(${i+1})">删除</button>
      </div>
    `;
    list.appendChild(div);
  });
}

async function addTask() {
  const title = document.getElementById("title").value;
  const description = document.getElementById("desc").value;
  const res = await fetch("/api/add", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({title, description})
  });
  const data = await res.json();
  render(data.tasks);
  document.getElementById("title").value = "";
  document.getElementById("desc").value = "";
}

async function deleteTask(pos) {
  const res = await fetch("/api/delete", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({pos})
  });
  const data = await res.json();
  render(data.tasks);
}

async function editTask(pos) {
  const title = prompt("新标题：");
  const description = prompt("新描述：");
  const res = await fetch("/api/update", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({pos, title, description})
  });
  const data = await res.json();
  render(data.tasks);
}

async function toggleTask(pos) {
  const res = await fetch("/api/toggle", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({pos})
  });
  const data = await res.json();
  render(data.tasks);
}
