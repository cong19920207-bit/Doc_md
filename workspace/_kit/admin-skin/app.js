/* 可行性 demo 逻辑：现网原页 vs 示例补丁，非真实业务 */
const MOCK_USERS = [
  {
    zid: "10086001",
    xid: "8801001",
    nickname: "Layla",
    photo: "L",
    color: "#1e9fff",
    bio: "hello hayyo",
    room: "R-2031",
    region: "AR",
    regTime: "2026-01-12 14:03:11",
    online: "离线",
    lastLogin: "2026-09-03 22:18:09",
    active7: 6,
    nation: "SA",
    device: "a8f2c91d",
    level: 12,
    noble: 0,
    vip: 1,
    source: "PhoneNumber",
    status: "ok",
    punished: "-",
    banned: "-",
    gameBanEnd: "-",
    demoNote: ""
  },
  {
    zid: "10086002",
    xid: "8801002",
    nickname: "Omar",
    photo: "O",
    color: "#009688",
    bio: "",
    room: "",
    region: "EN",
    regTime: "2025-11-02 09:41:00",
    online: "在线",
    lastLogin: "2026-09-04 10:12:44",
    active7: 1,
    nation: "EG",
    device: "bb10ee77",
    level: 4,
    noble: 1,
    vip: 0,
    source: "Facebook",
    status: "ban",
    punished: "2026-09-01 18:00:00",
    banned: "2026-09-01 18:00:00",
    gameBanEnd: "-",
    demoNote: "低活跃"
  },
  {
    zid: "10086003",
    xid: "8801003",
    nickname: "Nour",
    photo: "N",
    color: "#9c27b0",
    bio: "official",
    room: "R-110",
    region: "TR",
    regTime: "2025-08-20 11:20:33",
    online: "离线",
    lastLogin: "2026-08-28 01:03:12",
    active7: 0,
    nation: "TR",
    device: "cc77aa01",
    level: 20,
    noble: 2,
    vip: 3,
    source: "AppleID",
    status: "gameban",
    punished: "2026-08-28 01:10:00",
    banned: "-",
    gameBanEnd: "2026-09-11 01:10:00",
    demoNote: "示例：游戏封禁用户"
  },
  {
    zid: "10086004",
    xid: "8801004",
    nickname: "Mira",
    photo: "M",
    color: "#ff9800",
    bio: "host",
    room: "R-88",
    region: "AR",
    regTime: "2026-03-01 08:00:00",
    online: "在线",
    lastLogin: "2026-09-04 09:55:02",
    active7: 7,
    nation: "AE",
    device: "d0d0d0d0",
    level: 8,
    noble: 0,
    vip: 2,
    source: "Google",
    status: "frozen",
    punished: "2026-09-02 12:00:00",
    banned: "-",
    gameBanEnd: "-",
    demoNote: ""
  },
  {
    zid: "10086005",
    xid: "8801005",
    nickname: "Sam",
    photo: "S",
    color: "#ff5722",
    bio: "",
    room: "",
    region: "EN",
    regTime: "2026-05-19 16:44:21",
    online: "离线",
    lastLogin: "2026-09-01 03:22:10",
    active7: 2,
    nation: "US",
    device: "ee11ff22",
    level: 1,
    noble: 0,
    vip: 0,
    source: "PhoneNumber",
    status: "block",
    punished: "2026-09-01 03:30:00",
    banned: "2026-09-01 03:30:00",
    gameBanEnd: "-",
    demoNote: ""
  }
];

const STATUS_TEXT = {
  ok: "Unblock",
  block: "Block",
  ban: "Ban",
  frozen: "Frozen",
  gameban: "GameBan"
};

let mode = "after"; // 默认先看改后，便于对比
let toastTimer = 0;

function $(id) {
  return document.getElementById(id);
}

function toast(msg) {
  const el = $("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 1600);
}

function currentFilters() {
  return {
    zid: $("FAccountId").value.trim(),
    xid: $("FPrettyId").value.trim(),
    room: $("FRoomIdx").value.trim(),
    status: $("FStatus").value
  };
}

function filteredUsers() {
  const f = currentFilters();
  return MOCK_USERS.filter((u) => {
    if (f.zid && u.zid !== f.zid) return false;
    if (f.xid && u.xid !== f.xid) return false;
    if (f.room && u.room !== f.room) return false;
    if (f.status && u.status !== f.status) return false;
    return true;
  });
}

function statusHtml(status) {
  return `<span class="status ${status}">${STATUS_TEXT[status] || status}</span>`;
}

function opsHtml(user) {
  const links = [
    `<a data-act="block" data-zid="${user.zid}">Block</a>`,
    `<a data-act="ban" data-zid="${user.zid}">Ban</a>`,
    `<a data-act="modify" data-zid="${user.zid}">Modify</a>`,
    `<a data-act="reset" data-zid="${user.zid}">Reset</a>`
  ];
  if (mode === "live") {
    links.push(`<a data-act="gameban" data-zid="${user.zid}">GameBan</a>`);
  } else {
    links.push(`<a class="danger" data-act="demo" data-zid="${user.zid}">Demo</a>`);
  }
  return `<div class="ops">${links.join("")}</div>`;
}

function renderStatusOptions() {
  const keep = $("FStatus").value;
  const liveOpts = [
    ["", "--status--"],
    ["block", "Block"],
    ["ban", "Ban"],
    ["frozen", "Frozen"],
    ["gameban", "GameBan"]
  ];
  const afterOpts = liveOpts.filter((x) => x[0] !== "gameban");
  const opts = mode === "live" ? liveOpts : afterOpts;
  $("FStatus").innerHTML = opts
    .map(([v, t]) => `<option value="${v}">${t}</option>`)
    .join("");
  const allowed = opts.map((x) => x[0]);
  $("FStatus").value = allowed.includes(keep) ? keep : "";
  $("FStatus").classList.toggle("changed", mode === "after");
}

function renderTable() {
  const rows = filteredUsers();
  const showGameBan = mode === "live";
  const showDemoCol = mode === "after";
  const head = [
    "User ID",
    "Pretty ID",
    "Nickname",
    "Photo",
    "Bio",
    "Room",
    "Region",
    "Registration Time",
    "在线状态",
    "最近登录时间",
    "近7天活跃天数",
    "Nationality",
    "Device Number",
    "Level",
    "Noble Level",
    "VIP Level",
    "RegisterSource",
    "Account Status",
    "Last Punished Time",
    "Last Banned Time",
    showGameBan ? "Endtime of GameBan" : "",
    showDemoCol ? "Demo备注" : "",
    "Operation"
  ].filter(Boolean);

  $("thead").innerHTML = `<tr>${head
    .map((name) => {
      const mark =
        mode === "after" &&
        (name === "Demo备注" || name === "近7天活跃天数" || name === "Operation");
      return `<th class="${mark ? "changed" : ""}">${name}</th>`;
    })
    .join("")}</tr>`;

  $("tbody").innerHTML = rows
    .map((u) => {
      const activeCls =
        mode === "after" && u.active7 < 2 ? "alert-cell changed" : "";
      const tds = [
        u.zid,
        u.xid,
        u.nickname,
        `<span class="avatar" style="background:${u.color}">${u.photo}</span>`,
        u.bio || "-",
        u.room || "-",
        u.region,
        u.regTime,
        u.online,
        u.lastLogin,
        `<span class="${activeCls}">${u.active7}</span>`,
        u.nation,
        u.device,
        u.level,
        u.noble,
        u.vip,
        u.source,
        statusHtml(u.status),
        u.punished,
        u.banned
      ];
      if (showGameBan) tds.push(u.gameBanEnd);
      if (showDemoCol) tds.push(`<span class="changed">${u.demoNote || "-"}</span>`);
      tds.push(opsHtml(u));
      return `<tr>${tds
        .map((x, i) => {
          const isOps = mode === "after" && i === tds.length - 1;
          return `<td class="${isOps ? "changed" : ""}">${x}</td>`;
        })
        .join("")}</tr>`;
    })
    .join("");

  $("pager").textContent = `Display 1 to ${rows.length} Total ${rows.length} records`;
}

function setMode(next) {
  mode = next;
  document.querySelectorAll(".mode-switch button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.mode === next);
  });
  const log = $("changelog");
  if (log) log.classList.toggle("show", next === "after");
  renderStatusOptions();
  renderTable();
}

function openDialog(title, bodyHtml) {
  $("dlgTitle").textContent = title;
  $("dlgBody").innerHTML = bodyHtml;
  $("mask").classList.add("show");
}

function closeDialog() {
  $("mask").classList.remove("show");
}

function onOpClick(event) {
  const link = event.target.closest("a[data-act]");
  if (!link) return;
  const user = MOCK_USERS.find((u) => u.zid === link.dataset.zid);
  const act = link.dataset.act;
  if (act === "demo") {
    openDialog("Demo处理（非真实业务）", `
      <div class="row"><label>用户ID</label><div>${user.zid} / ${user.nickname}</div></div>
      <div class="row"><label>示例动作</label>
        <select><option>仅演示可加入口</option><option>不写真实处罚</option></select>
      </div>
      <p style="color:#999;margin:0;">这条弹窗用来验证：改已有页时，可以在原 Operation 上加入口，而不重做整页。</p>
    `);
    return;
  }
  openDialog(`${act.toUpperCase()} 账号`, `
    <div class="row"><label>用户ID</label><input value="${user.zid}" disabled></div>
    <div class="row"><label>Time</label><input placeholder="日:时:分"></div>
    <div class="row"><label>Reason</label>
      <select>
        <option>辱骂</option>
        <option>作弊</option>
        <option>其它</option>
      </select>
    </div>
    <p style="color:#999;margin:0;">弹窗字段按现网/PRD 常见结构示意，提交不落真实数据。</p>
  `);
}

function bind() {
  document.querySelectorAll(".mode-switch button").forEach((btn) => {
    btn.addEventListener("click", () => setMode(btn.dataset.mode));
  });
  $("Search").addEventListener("click", (e) => {
    e.preventDefault();
    renderTable();
  });
  $("SearchForm").addEventListener("submit", (e) => {
    e.preventDefault();
    renderTable();
  });
  $("tbody").addEventListener("click", onOpClick);
  $("dlgCancel").addEventListener("click", closeDialog);
  $("dlgOk").addEventListener("click", () => {
    closeDialog();
    toast("demo 不提交真实业务");
  });
  $("mask").addEventListener("click", (e) => {
    if (e.target.id === "mask") closeDialog();
  });
  document.querySelectorAll("[data-dead]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      toast("可行性 demo 只实现 User list");
    });
  });
}

bind();
setMode(document.body.classList.contains("gold") ? "live" : "after");
