// wanchai-editor-web.js
// 主流程：INI 文件选择/解析、Info 渲染、SKU 下拉、表格渲染、导出、重载、初始化、日期更新、搜索

let iniFileName = "";
let iniContent = "";
let infoSection = { UnitCount: "", ExportDate: "" };
let skuList = [];
let allRowsWithSku = []; // [{row:[], sku:""}]
let testColumns = ["Index", "Identifier", "TestID", "Description", "Enabled", "StringLimit", "LowLimit", "HighLimit", "LimitType", "Unit", "Parameters"];
let currentSku = "";
let searchTerm = "";

// ========== 高级功能：多选、右键菜单、批量编辑、字段校验 ==========

let selectedRowIndices = [];

// 1. 绑定事件
document.getElementById('fileInput').addEventListener('change', handleFileSelect);
document.getElementById('btnExport').addEventListener('click', handleExport);
document.getElementById('btnReload').addEventListener('click', confirmReload);
document.getElementById('btnInit').addEventListener('click', confirmInitialize);
document.getElementById('skuSelect').addEventListener('change', e => { currentSku = e.target.value; renderTable(); });
document.getElementById('btnAddSuffix').addEventListener('click', addSuffixToCurrentSku);
document.getElementById('btnAddSuffixes').addEventListener('click', addSuffixToAllSkus);
document.getElementById('btnBackspace').addEventListener('click', backspaceSkuSuffix);
document.getElementById('btnPrevSku').addEventListener('click', gotoPrevSku);
document.getElementById('btnNextSku').addEventListener('click', gotoNextSku);
document.getElementById('btnClearSearch').addEventListener('click', () => {
  searchTerm = "";
  document.getElementById('searchInput').value = "";
  selectedRowIndices = [];
  renderTable();
});
document.getElementById('searchInput').addEventListener('input', e => {
  searchTerm = e.target.value.toLowerCase();
  selectedRowIndices = [];
  renderTable();
});
document.getElementById('btnUpdateDate').addEventListener('click', updateExportDate);

// 自定义 confirm 弹窗（带过渡动画）
function customConfirm(message, onConfirm) {
  // 移除已有弹窗
  let old = document.getElementById('customConfirmModal');
  if (old) old.remove();
  // 创建弹窗
  const modal = document.createElement('div');
  modal.id = 'customConfirmModal';
  modal.style.position = 'fixed';
  modal.style.left = '0';
  modal.style.top = '0';
  modal.style.width = '100vw';
  modal.style.height = '100vh';
  modal.style.background = 'rgba(0,0,0,0.25)';
  modal.style.zIndex = 99999;
  modal.style.opacity = '0';
  modal.style.transition = 'opacity 0.25s';

  // 弹窗内容带淡入淡出
  modal.innerHTML = `
    <div id="customConfirmBox" style="position:absolute;left:50%;top:30%;transform:translate(-50%,-50%);background:#fff;padding:32px 32px 24px 32px;border-radius:10px;box-shadow:0 4px 24px #0002;min-width:340px;max-width:90vw;opacity:0;transition:opacity 0.25s;">
      <div style="font-size:18px;font-weight:bold;margin-bottom:12px;">Confirm</div>
      <div style="margin-bottom:24px;white-space:pre-line;">${message}</div>
      <div style="text-align:right;">        
        <button id="customConfirmOk" class="btn btn-primary">OK</button>
        <button id="customConfirmCancel" class="btn btn-secondary me-2">Cancel</button>
        <span id="customConfirmResult"></span>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  // 触发淡入
  setTimeout(() => {
    modal.style.opacity = '1';
    const box = document.getElementById('customConfirmBox');
    if (box) box.style.opacity = '1';
  }, 10);

  function closeModal() {
    // 淡出动画
    modal.style.opacity = '0';
    const box = document.getElementById('customConfirmBox');
    if (box) box.style.opacity = '0';
    setTimeout(() => {
      if (modal.parentNode) modal.parentNode.removeChild(modal);
    }, 250);
  }

  document.getElementById('customConfirmCancel').onclick = function () {
    closeModal();
  };
  document.getElementById('customConfirmOk').onclick = function () {
    closeModal();
    if (onConfirm) onConfirm();
  };

  // 支持ESC关闭
  setTimeout(() => {
    modal.focus();
    window.addEventListener('keydown', escHandler);
  }, 20);
  function escHandler(e) {
    if (e.key === "Escape") {
      closeModal();
      window.removeEventListener('keydown', escHandler);
    }
  }
  // 点击遮罩关闭
  modal.addEventListener('mousedown', function (e) {
    if (e.target === modal) {
      closeModal();
    }
  });
}

// Reload 二次确认
function confirmReload(e) {
  if(!iniFileName){
    return
  }
  const msg = 'Reload will overwrite all unsaved changes. This action cannot be undone.\nAre you sure you want to proceed?';
  customConfirm(msg, handleReload);
}
// Initialize 二次确认
function confirmInitialize(e) {
  if(!iniFileName){
    return
  }
  const msg = 'This will clear all loaded data and reset the application to its initial state.\nAre you sure you want to proceed?';
  // fixme
  customConfirm(msg, handleInit);
}

// 2. 解析INI文件
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) {
    return;
  }
  iniFileName = file.name;
  document.getElementById('fileName').textContent = iniFileName;
  const reader = new FileReader();
  reader.onload = function (evt) {
    iniContent = evt.target.result;
    parseIniContent(iniContent);
    renderSkuSelect();
    renderTable();
    renderInfo();
  };
  reader.readAsText(file, 'utf-8');
}

// 3. 解析INI内容
function parseIniContent(content) {
  // 解析Info
  const infoMatch = content.match(/\[Info\][\s\S]*?(?=\n\[|$)/);
  if (infoMatch) {
    const info = infoMatch[0];
    infoSection.UnitCount = (info.match(/UnitCount\s*=\s*(.+)/) || [])[1] || "";
    infoSection.ExportDate = (info.match(/Export Date\s*=\s*(.+)/) || [])[1] || "";
  }
  // 解析Test Items
  skuList = [];
  allRowsWithSku = [];
  const sectionRegex = /\[([^\]]+)\][\s\S]*?(?=\n\[|$)/g;
  let m;
  while ((m = sectionRegex.exec(content)) !== null) {
    const sectionName = m[1];
    if (sectionName === "Info") continue;
    skuList.push(sectionName);
    const sectionContent = m[0];
    // 解析每一行
    // 修复: 支持括号内有嵌套括号或引号的情况
    // 用正则找到每一行的 idx, header, values 字符串
    const rowRegex = /^\s*(\d+)\s*=\s*\(([^)]*)\)\s*VALUES\s*\(([\s\S]*?)\)\s*$/gm;
    let rowMatch;
    while ((rowMatch = rowRegex.exec(sectionContent)) !== null) {
      const idx = rowMatch[1];
      // const header = rowMatch[2].split(',').map(s=>s.trim());
      // 这里 rowMatch[3] 是 values 字符串，可能包含逗号、引号、括号等
      const values = parseRowValues(rowMatch[3]);
      let row = [idx, ...values];
      allRowsWithSku.push({ row, sku: sectionName });
    }
  }
  currentSku = skuList[0] || "";
}

// 4. 渲染SKU下拉
function renderSkuSelect() {
  const sel = document.getElementById('skuSelect');
  sel.innerHTML = skuList.map(sku => `<option value="${sku}">${sku}</option>`).join('');
  sel.value = currentSku;
}

// 5. 渲染表格
function renderTable() {
  const table = document.getElementById('testTable');
  const tbody = table.querySelector('tbody');
  tbody.innerHTML = '';
  // 兼容搜索过滤，rows为当前可见行
  let rows = allRowsWithSku.filter(item => item.sku === currentSku);
  if (searchTerm) {
    rows = rows.filter(item => item.row.some(v => String(v).toLowerCase().includes(searchTerm)));
  }
  // 设置 th/td 宽度为 auto
  const ths = table.querySelectorAll('th');
  ths.forEach(th => th.style.width = 'auto');
  rows.forEach((item, idx) => {
    const tr = document.createElement('tr');
    tr.setAttribute('data-row-index', idx);
    if (selectedRowIndices.includes(idx)) tr.classList.add('selected');
    item.row.forEach((v, i) => {
      const td = document.createElement('td');
      td.textContent = v;
      td.style.width = 'auto';
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  document.getElementById('skuCount').textContent = rows.length + " items";
  enableResizableTable();
}

// 6. 渲染Info
function renderInfo() {
  document.getElementById('unitCount').value = infoSection.UnitCount;
  document.getElementById('exportDate').value = infoSection.ExportDate;
}

// 7. 解析行数据
function parseRowValues(str) {
  const result = [];
  let cur = '';
  let quoteChar = null;
  let i = 0;

  while (i < str.length) {
    let c = str[i];

    if (c === "'" || c === '"') {
      if (!quoteChar) {
        quoteChar = c; // 开始引号
        cur += c;
      } else if (c === quoteChar) {
        cur += c; // 结束引号
        // 检查下一个字符是否是同类型引号（嵌套引号），如 '' 或 ""
        if (i + 1 < str.length && str[i + 1] === quoteChar) {
          // 嵌套引号，视为内容
          i++;
          cur += quoteChar; // 添加嵌套引号
        } else {
          quoteChar = null; // 结束引号
        }
      } else {
        cur += c; // 其他引号
      }
    } else if (c === ',' && !quoteChar) {
      result.push(stripQuotes(cur.trim())); // 添加当前字段
      cur = ''; // 清空当前字段
    } else {
      cur += c; // 添加当前字符
    }
    i++;
  }

  if (cur.length > 0) result.push(stripQuotes(cur.trim())); // 添加最后一个字段

  // 确保结果数组长度为10，不足的填充空字符串
  while (result.length < 10) result.push('');

  return result;
}

function stripQuotes(s) {
  // 只去除首尾一对引号，且内容长度大于1
  if (s.length > 1 && ((s[0] === "'" && s[s.length - 1] === "'") || (s[0] === '"' && s[s.length - 1] === '"'))) {
    return s.substring(1, s.length - 1);
  }
  return s;
}

// 9. 导出INI
function handleExport() {
  if (!iniFileName) {
    showAutoDismissMessage("Please select an ini file first.");
    return
  }
  // 重新组装INI内容
  let content = `[Info]\nUnitCount=${document.getElementById('unitCount').value}\nExport Date=${document.getElementById('exportDate').value}\n\n`;
  skuList.forEach(sku => {
    let rows = allRowsWithSku.filter(item => item.sku === sku);
    content += `[${sku}]\nCount=${rows.length}\n`;
    rows.forEach((item, i) => {
      let row = item.row.slice(1); // 去掉Index
      let rowStr = row.map((v, j) => j === 2 && (v === "0" || v === "1") ? v : `'${v}'`).join(',');
      content += `${i + 1}=(Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters) VALUES (${rowStr})\n`;
    });
    content += '\n';
  });
  // 下载
  const blob = new Blob([content], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = iniFileName.replace(/\[[^\]]*\]/g, '[]').replace(/\.ini$/, '') + '.ini';
  a.click();
}

// 10. 其它事件处理（重载、初始化、日期更新等）
function handleReload() {
  if (iniContent) parseIniContent(iniContent);
  selectedRowIndices = [];
  renderSkuSelect();
  renderTable();
  renderInfo();
}
function handleInit() {
  iniFileName = "";
  iniContent = "";
  infoSection = { UnitCount: "", ExportDate: "" }; skuList = []; allRowsWithSku = []; currentSku = "";
  selectedRowIndices = [];
  renderSkuSelect();
  renderTable();
  renderInfo();
  // 恢复 fileInput,searchInput,skuSuffix 为初始状态
  const fileInput = document.getElementById('fileInput');
  if (fileInput) fileInput.value = '';
  const searchInput = document.getElementById('searchInput');
  if (searchInput) searchInput.value = '';
  const skuSuffix = document.getElementById('skuSuffix');
  if (skuSuffix) skuSuffix.value = '_GRC';
}
function updateExportDate() {
  const now = new Date();
  const dateStr = `${now.getMonth() + 1}/${now.getDate()}/${now.getFullYear()} ${now.toLocaleTimeString('en-US')}`;
  document.getElementById('exportDate').value = dateStr;
}

// 11. SKU相关批量操作
// Add suffix: 只对当前选中 SKU 添加后缀
function addSuffixToCurrentSku() {
  const suffix = document.getElementById('skuSuffix').value;
  const sku = document.getElementById('skuSelect').value;
  if (!sku || !suffix) {
    alert('SKU and Suffix cannot be empty!');
    return;
  }
  const newSku = sku + suffix;
  if (skuList.includes(newSku)) {
    alert('Target SKU name is duplicated with another SKU, please check.');
    return;
  }
  // 更新 skuList
  const idx = skuList.indexOf(sku);
  if (idx !== -1) skuList[idx] = newSku;
  // 更新所有 test item 的 Identifier 字段
  allRowsWithSku.forEach(item => {
    if (item.sku === sku) {
      item.sku = newSku;
      if (item.row[1] === sku) item.row[1] = newSku;
    }
  });
  // 刷新下拉框、选中、表格
  renderSkuSelect();
  document.getElementById('skuSelect').value = newSku;
  currentSku = newSku;
  renderTable();
}
// Add suffixes: 所有 SKU 批量添加后缀
function addSuffixToAllSkus() {
  const suffix = document.getElementById('skuSuffix').value;
  const sku = document.getElementById('skuSelect').value;
  if (!sku || !suffix) {
    alert('SKU and Suffix cannot be empty!');
    return;
  }
  const newSkuList = skuList.map(sku => sku + suffix);
  const skuMap = {};
  skuList.forEach((oldSku, i) => skuMap[oldSku] = newSkuList[i]);
  // 更新所有 test item 的 Identifier 字段
  allRowsWithSku.forEach(item => {
    const newSku = skuMap[item.sku];
    if (newSku) {
      item.sku = newSku;
      if (item.row[1] === item.sku) item.row[1] = newSku;
      else item.row[1] = newSku;
    }
  });
  skuList = newSkuList;
  renderSkuSelect();
  currentSku = skuList[0] || '';
  document.getElementById('skuSelect').value = currentSku;
  renderTable();
}
function backspaceSkuSuffix() {
  const sku = document.getElementById('skuSelect').value;
  if (!sku || sku.length <= 1) return;
  const newSku = sku.slice(0, -1);
  if (skuList.includes(newSku)) {
    alert('Target SKU name is duplicated with another SKU, please check.');
    return;
  }
  // 更新 skuList
  const idx = skuList.indexOf(sku);
  if (idx !== -1) skuList[idx] = newSku;
  // 更新所有 test item 的 Identifier 字段
  allRowsWithSku.forEach(item => {
    if (item.sku === sku) {
      item.sku = newSku;
      if (item.row[1] === sku) item.row[1] = newSku;
    }
  });
  // 刷新下拉框、选中、表格
  renderSkuSelect();
  document.getElementById('skuSelect').value = newSku;
  currentSku = newSku;
  renderTable();
}
function gotoPrevSku() {
  const idx = skuList.indexOf(currentSku);
  if (idx > 0) {
    currentSku = skuList[idx - 1];
    document.getElementById('skuSelect').value = currentSku;
    selectedRowIndices = [];
    renderTable();
  } else {
    showAutoDismissMessage('This is the first SKU!');
  }
}
function gotoNextSku() {
  const idx = skuList.indexOf(currentSku);
  if (idx >= 0 && idx < skuList.length - 1) {
    currentSku = skuList[idx + 1];
    document.getElementById('skuSelect').value = currentSku;
    selectedRowIndices = [];
    renderTable();
  } else {
    showAutoDismissMessage('This is the last SKU!');
  }
}

// 12. 编辑弹窗、右键菜单、拖拽排序、剪贴板等
// ... 这里建议分模块补充 

// 扩展 renderTable 支持多选高亮
const _orig_renderTable = renderTable;
renderTable = function () {
  const table = document.getElementById('testTable');
  const tbody = table.querySelector('tbody');
  tbody.innerHTML = '';
  // 兼容搜索过滤，rows为当前可见行
  let rows = allRowsWithSku.filter(item => item.sku === currentSku);
  if (searchTerm) {
    rows = rows.filter(item => item.row.some(v => String(v).toLowerCase().includes(searchTerm)));
  }
  // 设置 th/td 宽度为 auto
  const ths = table.querySelectorAll('th');
  ths.forEach(th => th.style.width = 'auto');
  rows.forEach((item, idx) => {
    const tr = document.createElement('tr');
    tr.setAttribute('data-row-index', idx);
    if (selectedRowIndices.includes(idx)) tr.classList.add('selected');
    item.row.forEach((v, i) => {
      const td = document.createElement('td');
      td.textContent = v;
      td.style.width = 'auto';
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  document.getElementById('skuCount').textContent = rows.length + " items";
};

// 多选与高亮
function enableRowEditAndHighlight() {
  const table = document.getElementById('testTable');
  if (!table) return;
  table.addEventListener('click', function (e) {
    let tr = e.target;
    while (tr && tr.tagName !== 'TR') tr = tr.parentElement;
    if (!tr) return;
    if (tr.parentElement.tagName !== 'TBODY') return;
    let rowIndex = Number(tr.getAttribute('data-row-index'));
    if (e.ctrlKey || e.metaKey) {
      // 多选
      if (selectedRowIndices.includes(rowIndex)) {
        selectedRowIndices = selectedRowIndices.filter(i => i !== rowIndex);
      } else {
        selectedRowIndices.push(rowIndex);
      }
    } else if (e.shiftKey && selectedRowIndices.length > 0) {
      // 区间多选
      let last = selectedRowIndices[selectedRowIndices.length - 1];
      let [start, end] = [Math.min(last, rowIndex), Math.max(last, rowIndex)];
      selectedRowIndices = [];
      for (let i = start; i <= end; ++i) selectedRowIndices.push(i);
    } else {
      // 单选
      selectedRowIndices = [rowIndex];
    }
    // 只更新高亮，不刷新表格
    const tbody = table.querySelector('tbody');
    Array.from(tbody.children).forEach((row, i) => {
      if (selectedRowIndices.includes(i)) row.classList.add('selected');
      else row.classList.remove('selected');
    });
  });
  // 新增：双击行打开编辑窗口
  table.addEventListener('dblclick', function (e) {
    let tr = e.target;
    while (tr && tr.tagName !== 'TR') tr = tr.parentElement;
    if (!tr) return;
    if (tr.parentElement.tagName !== 'TBODY') return;
    let rowIndex = Number(tr.getAttribute('data-row-index'));
    showEditDialog(rowIndex, 'edit');
  });
  // 新增：Ctrl+C/Ctrl+V/Ctrl+X 复制、粘贴、剪切（全局监听，表格聚焦或页面内都可用）
  document.addEventListener('keydown', async function (e) {
    // 仅在主表格tab激活时生效
    const table = document.getElementById('testTable');
    const isTableTab = document.getElementById('tests').classList.contains('active');
    if (!isTableTab) return;
    // 兼容搜索过滤，rows为当前可见行
    let rows = allRowsWithSku.filter(item => item.sku === currentSku);
    if (searchTerm) {
      rows = rows.filter(item => item.row.some(v => String(v).toLowerCase().includes(searchTerm)));
    }
    // 复制
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'c') {
      let selectedRows = selectedRowIndices.map(idx => rows[idx]).filter(Boolean);
      if (!selectedRows.length) return;
      // 导出格式
      const header = "(Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters)";
      let lines = selectedRows.map(item => {
        let exportRow = item.row.slice(1);
        let formatted = exportRow.map((v, i) => (i === 2 && (v === "0" || v === "1")) ? v : `'${v}'`).join(",");
        return `${item.row[0]}=${header} VALUES (${formatted})`;
      });
      try { await navigator.clipboard.writeText(lines.join('\n')); showAutoDismissMessage(selectedRows.length == 1 ? 'Item is copied!' : 'Items are copied!'); } catch { }
      e.preventDefault();
    }
    // 粘贴
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'v') {
      try {
        let text = await navigator.clipboard.readText();
        // 支持 INI 导出格式
        let pastedRows = [];
        text.split(/\r?\n/).forEach(line => {
          let m = line.match(/^\s*(\d+)\s*=\s*\(Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters\)\s*VALUES\s*\((.*)\)\s*$/);
          if (m) {
            let idx = m[1];
            let values = parseRowValues(m[2]);
            pastedRows.push([idx, ...values]);
          }
        });
        if (!pastedRows.length) return;
        // 粘贴到当前可见区块最后一行的下一个位置
        let maxIdx = Math.max(...selectedRowIndices, -1);
        let insertAt = maxIdx + 1;
        // 找到 allRowsWithSku 中对应的全局插入点
        let visibleRows = allRowsWithSku
          .map((item, i) => ({ item, i }))
          .filter(({ item }) => item.sku === currentSku && (!searchTerm || item.row.some(v => String(v).toLowerCase().includes(searchTerm))));
        let globalInsertAt = visibleRows[insertAt]?.i ?? allRowsWithSku.length;
        pastedRows.forEach(row => {
          let newRow = ["TMP", ...row.slice(1)];
          allRowsWithSku.splice(globalInsertAt, 0, { row: newRow, sku: currentSku });
          globalInsertAt++;
        });
        // 重新编号当前 SKU 下所有行的 Index
        let newSkuRows = allRowsWithSku.filter(item => item.sku === currentSku);
        newSkuRows.forEach((item, idx) => { item.row[0] = (idx + 1).toString(); });
        renderTable();
        showAutoDismissMessage(pastedRows.length == 1 ? 'Item is pasted!' : 'Items are pasted!');
      } catch { }
      e.preventDefault();
    }
    // 剪切
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'x') {
      let selectedRows = selectedRowIndices.map(idx => rows[idx]).filter(Boolean);
      if (!selectedRows.length) return;
      // 导出格式
      const header = "(Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters)";
      let lines = selectedRows.map(item => {
        let exportRow = item.row.slice(1);
        let formatted = exportRow.map((v, i) => (i === 2 && (v === "0" || v === "1")) ? v : `'${v}'`).join(",");
        return `${item.row[0]}=${header} VALUES (${formatted})`;
      });
      try { await navigator.clipboard.writeText(lines.join('\n')); showAutoDismissMessage(selectedRows.length == 1 ? 'Item is cut!' : 'Items are cut!'); } catch { }
      // 删除选中行
      let indices = selectedRowIndices.map(idx => rows[idx]?.row[0]);
      // 只删除当前可见（过滤后）rows中选中的行
      let toDelete = new Set(indices);
      allRowsWithSku = allRowsWithSku.filter(item => !(item.sku === currentSku && toDelete.has(item.row[0]) && (!searchTerm || item.row.some(v => String(v).toLowerCase().includes(searchTerm)))));
      // 重新编号当前 SKU 下所有行的 Index
      let newSkuRows = allRowsWithSku.filter(item => item.sku === currentSku);
      newSkuRows.forEach((item, idx) => { item.row[0] = (idx + 1).toString(); });
      selectedRowIndices = [];
      renderTable();
      e.preventDefault();
    }
  });
}

// 右键菜单
function enableContextMenu() {
  const table = document.getElementById('testTable');
  let menu = document.getElementById('contextMenu');
  if (!menu) {
    menu = document.createElement('ul');
    menu.id = 'contextMenu';
    menu.className = 'context-menu';
    menu.style.display = 'none';
    menu.style.position = 'absolute';
    menu.style.zIndex = 9999;
    document.body.appendChild(menu);
  }
  menu.innerHTML = `
    <li data-action="edit">Edit</li>
    <li data-action="insert-before">Insert Before</li>
    <li data-action="insert-after">Insert After</li>
    <li data-action="copy">Copy</li>
    <li data-action="copy-to-all">Copy To Other SKUs</li>
    <li data-action="delete">Delete</li>
  `;

  table.addEventListener('contextmenu', function (e) {
    e.preventDefault();
    let tr = e.target;
    while (tr && tr.tagName !== 'TR') tr = tr.parentElement;
    if (!tr || tr.parentElement.tagName !== 'TBODY') return;
    let rowIndex = Number(tr.getAttribute('data-row-index'));
    if (!selectedRowIndices.includes(rowIndex)) {
      selectedRowIndices = [rowIndex];
      renderTable();
    }
    menu.style.display = 'block';
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
  });

  document.addEventListener('click', () => { menu.style.display = 'none'; });

  menu.addEventListener('click', function (e) {
    const action = e.target.getAttribute('data-action');
    if (action === 'edit') {
      if (selectedRowIndices.length === 1) showEditDialog(selectedRowIndices[0]);
    } else if (action === 'insert-before') {
      if (selectedRowIndices.length === 1) insertTestItem(selectedRowIndices[0], true);
    } else if (action === 'insert-after') {
      if (selectedRowIndices.length === 1) insertTestItem(selectedRowIndices[0], false);
    } else if (action === 'copy') {
      copySelectedRowsToClipboard();
    } else if (action === 'copy-to-all') {
      copyToAllSkus(selectedRowIndices);
    } else if (action === 'delete') {
      deleteSelectedRows();
    }
    menu.style.display = 'none';
  });
}

// 插入新 test item
function insertTestItem(rowIndex, before = true) {
  let rows = allRowsWithSku.filter(item => item.sku === currentSku);
  let insertAt = before ? rowIndex : rowIndex + 1;
  // 修正：如果是 after 且插入点超出当前 SKU 行数，插入到末尾
  if (!before && insertAt >= rows.length) {
    insertAt = rows.length;
  }
  // 构造空行
  let newRow = [
    (insertAt + 1).toString(), // Index
    currentSku, '', '', '', '', '', '', '', '', ''
  ];
  // 插入到 allRowsWithSku
  let globalIdx = 0, count = 0;
  for (let i = 0; i < allRowsWithSku.length; ++i) {
    if (allRowsWithSku[i].sku === currentSku) {
      if (count === insertAt) { globalIdx = i; break; }
      count++;
    }
  }
  // 如果插入点超出所有当前 SKU 行，则插入到最后
  if (insertAt === rows.length) {
    // 找到最后一个当前 SKU 的 globalIdx
    for (let i = allRowsWithSku.length - 1; i >= 0; --i) {
      if (allRowsWithSku[i].sku === currentSku) {
        globalIdx = i + 1;
        break;
      }
    }
  }
  allRowsWithSku.splice(globalIdx, 0, { row: newRow.slice(), sku: currentSku });
  // 重新编号
  let skuRows = allRowsWithSku.filter(item => item.sku === currentSku);
  skuRows.forEach((item, idx) => { item.row[0] = (idx + 1).toString(); });
  renderTable();
  // 弹出编辑
  let idxInSku = insertAt;
  showEditDialog(idxInSku, before ? 'insert-before' : 'insert-after');
}

// 复制到所有 SKU
function copyToAllSkus(rowIndices) {
  let rows = allRowsWithSku.filter(item => item.sku === currentSku);
  let selectedRows = rowIndices.map(idx => rows[idx]);
  let otherSkus = skuList.filter(sku => sku !== currentSku);
  otherSkus.forEach(sku => {
    let skuRows = allRowsWithSku.filter(item => item.sku === sku);
    rowIndices.forEach((selIdx, offset) => {
      // 插入到相同 index 下方
      let insertAt = selIdx + 1;
      // 找到 allRowsWithSku 中对应的全局插入点
      let skuIndices = allRowsWithSku.map((item, i) => item.sku === sku ? i : -1).filter(i => i !== -1);
      let globalInsertAt = skuIndices[insertAt] !== undefined ? skuIndices[insertAt] : allRowsWithSku.length;
      let sel = selectedRows[offset];
      let newRow = ["TMP", sku, ...sel.row.slice(2)];
      allRowsWithSku.splice(globalInsertAt, 0, { row: newRow, sku });
    });
    // 重新编号该 SKU 下所有行的 Index
    let newSkuRows = allRowsWithSku.filter(item => item.sku === sku);
    newSkuRows.forEach((item, idx) => { item.row[0] = (idx + 1).toString(); });
  });
  renderTable();
  showAutoDismissMessage('Copied to other SKUs!');
}

// 编辑弹窗
function showEditDialog(rowIndex, type = 'edit') {
  let rows = allRowsWithSku.filter(item => item.sku === currentSku);
  if (rowIndex < 0 || rowIndex >= rows.length) return;
  let rowObj = rows[rowIndex];
  let row = rowObj.row;
  let dialog = document.createElement('div');
  dialog.className = 'modal fade';
  dialog.tabIndex = -1;
  let title = 'Edit Test Item';
  if (type === 'insert-before') title = 'Insert Test Item (Before)';
  if (type === 'insert-after') title = 'Insert Test Item (After)';
  dialog.innerHTML = `
    <div class="modal-dialog modal-lg" style="max-width:700px;">
      <div class="modal-content" style="font-size:14px;">
        <div class="modal-header" style="padding:8px 14px;">
          <h5 class="modal-title" style="font-size:16px;">${title}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" style="width:20px;height:20px;"></button>
        </div>
        <div class="modal-body" style="padding:10px 14px;">
          <form id="editTestItemForm">
            ${testColumns.map((col, i) => `
              <div class="mb-1 row" style="margin-bottom:4px !important;">
                <label class="col-sm-4 col-form-label" style="font-size:15px;padding-right:4px;">${col}:</label>
                <div class="col-sm-8">
                  ${col === 'Index'
      ? `<input type="text" class="form-control form-control-sm" name="${col}" value="${row[i] || ''}" readonly style="font-size:14px;">`
      : col === 'Parameters'
        ? `<textarea class="form-control form-control-sm" name="${col}" rows="2" style="font-size:14px;">${row[i] || ''}</textarea>`
        : `<input type="text" class="form-control form-control-sm" name="${col}" value="${row[i] || ''}" style="font-size:14px;">`
    }
                </div>
              </div>
            `).join('')}
            ${(type === 'edit') ? `<div class="mb-1" id="applyChangeToOptions" style="margin-bottom:6px !important;">
              <div style="font-weight:bold;font-size:16px;margin-bottom:2px;">Apply Change To:</div>
              <div>
                <label style="margin-bottom:2px;"><input type="radio" name="applyTo" value="all_by_field" checked> All SKUs + Exact field ---> Handle modified fields which have same original value.</label><br>
                <label style="margin-bottom:2px;"><input type="radio" name="applyTo" value="all"> All SKUs + Any fields ---> Handle any fields which have same original value.</label><br>
                <label style="margin-bottom:2px;"><input type="radio" name="applyTo" value="sku_by_field"> Current SKU only + Exact fields ---> Handle modified fields which have same original value.</label><br>
                <label style="margin-bottom:2px;"><input type="radio" name="applyTo" value="sku_only"> Current SKU only + Any fields ---> Handle any fields which have same original value.</label><br>
                <label style="margin-bottom:2px;"><input type="radio" name="applyTo" value="current"> Current item only</label>
              </div>
            </div>` : ''}
          </form>
        </div>
        <div class="modal-footer" style="padding:8px 14px;">
          <button type="button" class="btn btn-primary btn-sm" id="editTestItemSaveBtn">Save</button>
          <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Cancel</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(dialog);
  let modal = new bootstrap.Modal(dialog);
  modal.show();
  dialog.querySelector('#editTestItemSaveBtn').onclick = function () {
    let form = dialog.querySelector('#editTestItemForm');
    let newRow = testColumns.map(col => form.elements[col].value);
    if (type !== 'edit') {
      // 只改当前行
      let globalIdx = allRowsWithSku.findIndex(item =>
        item.sku === currentSku && item.row[0] === row[0]
      );
      if (globalIdx !== -1) {
        allRowsWithSku[globalIdx].row = newRow;
      }
    } else {
      let applyTo = dialog.querySelector('input[name="applyTo"]:checked').value;
      let oldRow = row.slice();
      let columns = testColumns;
      function getFieldDiffs(oldRow, newRow) {
        let diffs = [];
        for (let i = 1; i < columns.length; ++i) {
          if ((oldRow[i] ?? '') !== (newRow[i] ?? '')) {
            diffs.push({ col: columns[i], oldVal: oldRow[i], newVal: newRow[i], idx: i });
          }
        }
        return diffs;
      }
      let diffs = getFieldDiffs(oldRow, newRow);
      if (applyTo === 'all_by_field') {
        allRowsWithSku.forEach(item => {
          diffs.forEach(d => {
            if (item.row[d.idx] === d.oldVal) item.row[d.idx] = d.newVal;
          });
        });
      } else if (applyTo === 'all') {
        allRowsWithSku.forEach(item => {
          diffs.forEach(d => {
            for (let j = 1; j < columns.length; ++j) {
              if (item.row[j] === d.oldVal) item.row[j] = d.newVal;
            }
          });
        });
      } else if (applyTo === 'sku_by_field') {
        allRowsWithSku.forEach(item => {
          if (item.sku === currentSku) {
            diffs.forEach(d => {
              if (item.row[d.idx] === d.oldVal) item.row[d.idx] = d.newVal;
            });
          }
        });
      } else if (applyTo === 'sku_only') {
        allRowsWithSku.forEach(item => {
          if (item.sku === currentSku) {
            diffs.forEach(d => {
              for (let j = 1; j < columns.length; ++j) {
                if (item.row[j] === d.oldVal) item.row[j] = d.newVal;
              }
            });
          }
        });
      } else if (applyTo === 'current') {
        let globalIdx = allRowsWithSku.findIndex(item =>
          item.sku === currentSku && item.row[0] === row[0]
        );
        if (globalIdx !== -1) {
          allRowsWithSku[globalIdx].row = newRow;
        }
      }
    }
    renderTable();
    modal.hide();
    setTimeout(() => dialog.remove(), 300);
  };
  dialog.addEventListener('hidden.bs.modal', () => dialog.remove());
}

// 批量编辑弹窗
function showBatchEditDialog(rowIndices) {
  let rows = allRowsWithSku.filter(item => item.sku === currentSku);
  let fields = testColumns.slice(1); // 不含Index
  let dialog = document.createElement('div');
  dialog.className = 'modal fade';
  dialog.tabIndex = -1;
  dialog.innerHTML = `
    <div class="modal-dialog modal-lg modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Batch Edit Test Items</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <form id="batchEditForm">
            ${fields.map(col => `
              <div class="mb-3 row">
                <label class="col-sm-3 col-form-label">${col}:</label>
                <div class="col-sm-9">
                  ${col === 'Parameters'
      ? `<textarea class="form-control" name="${col}" rows="3"></textarea>`
      : `<input type="text" class="form-control" name="${col}" value="">`
    }
                  <div class="form-text text-muted">留空则不修改该字段</div>
                </div>
              </div>
            `).join('')}
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-primary" id="batchEditSaveBtn">Save</button>
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(dialog);
  let modal = new bootstrap.Modal(dialog);
  modal.show();
  dialog.querySelector('#batchEditSaveBtn').onclick = function () {
    let form = dialog.querySelector('#batchEditForm');
    let updates = {};
    fields.forEach(col => {
      let val = form.elements[col].value;
      if (val !== '') updates[col] = val;
    });
    rowIndices.forEach(idx => {
      let globalIdx = allRowsWithSku.findIndex(item =>
        item.sku === currentSku && item.row[0] === rows[idx].row[0]
      );
      if (globalIdx !== -1) {
        fields.forEach((col, i) => {
          if (updates[col] !== undefined) {
            allRowsWithSku[globalIdx].row[i + 1] = updates[col];
          }
        });
      }
    });
    renderTable();
    modal.hide();
    setTimeout(() => dialog.remove(), 300);
  };
  dialog.addEventListener('hidden.bs.modal', () => dialog.remove());
}

// 字段校验
function validateTestItem(row) {
  if (!row[1]) return 'Identifier 不能为空';
  if (!row[2]) return 'TestID 不能为空';
  if (row[4] && isNaN(Number(row[4]))) return 'StringLimit 必须为数字';
  // 可扩展更多校验
  return null;
}

// 自动消失的 message，支持传入 text
function showAutoDismissMessage(text) {
  let msg = document.createElement('div');
  msg.textContent = text;
  msg.style.position = 'fixed';
  msg.style.top = '20px';
  msg.style.left = '50%';
  msg.style.transform = 'translateX(-50%)';
  msg.style.background = '#333';
  msg.style.color = '#fff';
  msg.style.padding = '10px 24px';
  msg.style.borderRadius = '6px';
  msg.style.zIndex = 99999;
  msg.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
  document.body.appendChild(msg);
  setTimeout(() => {
    msg.style.transition = 'opacity 0.5s';
    msg.style.opacity = '0';
    setTimeout(() => msg.remove(), 500);
  }, 1200);
}

// 复制
function copySelectedRowsToClipboard() {
  let rows = allRowsWithSku.filter(item => item.sku === currentSku);
  let selectedRows = selectedRowIndices.map(idx => rows[idx]).filter(Boolean);
  if (!selectedRows.length) return;
  // 1. 复制到剪贴板（导出格式）
  const header = "(Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters)";
  let lines = selectedRows.map(item => {
    let exportRow = item.row.slice(1);
    let formatted = exportRow.map((v, i) => (i === 2 && (v === "0" || v === "1")) ? v : `'${v}'`).join(",");
    return `${item.row[0]}=${header} VALUES (${formatted})`;
  });
  navigator.clipboard.writeText(lines.join('\n'));
  // 2. 粘贴到选中行的最后一行的下一个位置
  let skuRows = allRowsWithSku.filter(item => item.sku === currentSku);
  // 找到选中区块的最大 index
  let maxIdx = Math.max(...selectedRowIndices.map(idx => Number(skuRows[idx]?.row[0] || 0)), 0);
  // 插入点应为最大 index + 1
  let insertAt = maxIdx;
  // 找到 allRowsWithSku 中对应的全局插入点
  let skuIndices = allRowsWithSku.map((item, i) => item.sku === currentSku ? i : -1).filter(i => i !== -1);
  let globalInsertAt = skuIndices[insertAt] !== undefined ? skuIndices[insertAt] : allRowsWithSku.length;
  selectedRows.forEach(item => {
    let newRow = ["TMP", ...item.row.slice(1)];
    allRowsWithSku.splice(globalInsertAt, 0, { row: newRow, sku: currentSku });
    globalInsertAt++;
  });
  // 3. 重新编号当前 SKU 下所有行的 Index，保证连续
  let newSkuRows = allRowsWithSku.filter(item => item.sku === currentSku);
  newSkuRows.forEach((item, idx) => { item.row[0] = (idx + 1).toString(); });
  renderTable();
  showAutoDismissMessage('Copied and pasted!');
}
// 删除
function deleteSelectedRows() {
  let rows = allRowsWithSku.filter(item => item.sku === currentSku);
  let indices = selectedRowIndices.map(idx => rows[idx]?.row[0]);
  // 只删除当前可见（过滤后）rows中选中的行
  let toDelete = new Set(indices);
  allRowsWithSku = allRowsWithSku.filter(item => !(item.sku === currentSku && toDelete.has(item.row[0]) && (!searchTerm || item.row.some(v => String(v).toLowerCase().includes(searchTerm)))));
  selectedRowIndices = [];
  // 重新编号当前 SKU 下所有行的 Index，保证连续
  let newSkuRows = allRowsWithSku.filter(item => item.sku === currentSku);
  newSkuRows.forEach((item, idx) => { item.row[0] = (idx + 1).toString(); });
  renderTable();
}

// 初始化绑定
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    enableRowEditAndHighlight();
    enableContextMenu();
  });
} else {
  enableRowEditAndHighlight();
  enableContextMenu();
}

function enableResizableTable() {
  const table = document.getElementById('testTable');
  if (!table) return;
  const ths = table.querySelectorAll('th');
  let colWidths = JSON.parse(localStorage.getItem('wanchai_col_widths') || '[]');
  ths.forEach((th, i) => {
    if (colWidths[i]) th.style.width = colWidths[i];
  });
  ths.forEach((th, i) => {
    if (th.querySelector('.col-resize-handle')) return;
    const handle = document.createElement('div');
    handle.className = 'col-resize-handle';
    handle.style.background = '#e6eaf2';
    handle.style.width = '12px';
    handle.style.right = '-6px';
    handle.style.borderRadius = '6px';
    handle.style.opacity = '0.7';
    th.appendChild(handle);
    let startX, startWidth;
    handle.onmousedown = function (e) {
      startX = e.pageX;
      startWidth = th.offsetWidth;
      document.body.style.cursor = 'col-resize';
      document.onmousemove = function (e2) {
        let newWidth = startWidth + (e2.pageX - startX);
        if (newWidth > 30) {
          th.style.width = newWidth + 'px';
          // 设置所有 td
          table.querySelectorAll('tr').forEach(row => {
            let cell = row.children[i];
            if (cell) cell.style.width = newWidth + 'px';
          });
        }
      };
      document.onmouseup = function () {
        document.body.style.cursor = '';
        document.onmousemove = null;
        document.onmouseup = null;
        // 记忆列宽
        let ths2 = table.querySelectorAll('th');
        let widths = Array.from(ths2).map(th => th.style.width || '');
        localStorage.setItem('wanchai_col_widths', JSON.stringify(widths));
      };
      e.preventDefault();
      e.stopPropagation();
    };
    // 双击自适应内容宽度
    handle.ondblclick = function (e) {
      // 仅在拖动柄上双击才自适应宽度
      let max = th.scrollWidth;
      table.querySelectorAll('tr').forEach(row => {
        let cell = row.children[i];
        if (cell) max = Math.max(max, cell.scrollWidth);
      });
      th.style.width = (max + 16) + 'px';
      table.querySelectorAll('tr').forEach(row => {
        let cell = row.children[i];
        if (cell) cell.style.width = (max + 16) + 'px';
      });
      // 记忆列宽
      let ths2 = table.querySelectorAll('th');
      let widths = Array.from(ths2).map(th => th.style.width || '');
      localStorage.setItem('wanchai_col_widths', JSON.stringify(widths));
      e.preventDefault();
      e.stopPropagation();
    };
  });
}