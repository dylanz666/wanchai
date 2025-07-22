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
document.getElementById('btnReload').addEventListener('click', handleReload);
document.getElementById('btnInit').addEventListener('click', handleInit);
document.getElementById('skuSelect').addEventListener('change', e => { currentSku = e.target.value; renderTable(); });
document.getElementById('btnAddSuffix').addEventListener('click', addSuffixToCurrentSku);
document.getElementById('btnAddSuffixes').addEventListener('click', addSuffixToAllSkus);
document.getElementById('btnBackspace').addEventListener('click', backspaceSkuSuffix);
document.getElementById('btnPrevSku').addEventListener('click', gotoPrevSku);
document.getElementById('btnNextSku').addEventListener('click', gotoNextSku);
document.getElementById('btnClearSearch').addEventListener('click', () => { searchTerm = ""; document.getElementById('searchInput').value = ""; renderTable(); });
document.getElementById('searchInput').addEventListener('input', e => { searchTerm = e.target.value.toLowerCase(); renderTable(); });
document.getElementById('btnUpdateDate').addEventListener('click', updateExportDate);

// 2. 解析INI文件
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  iniFileName = file.name;
  document.getElementById('fileName').textContent = file.name;
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
  const tbody = document.getElementById('testTable').querySelector('tbody');
  tbody.innerHTML = '';
  let rows = allRowsWithSku.filter(item => item.sku === currentSku);
  if (searchTerm) {
    rows = rows.filter(item => item.row.some(v => String(v).toLowerCase().includes(searchTerm)));
  }
  rows.forEach(item => {
    const tr = document.createElement('tr');
    item.row.forEach((v, i) => {
      const td = document.createElement('td');
      td.textContent = v;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  document.getElementById('skuCount').textContent = rows.length + " items";
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

// 8. 其它功能（批量操作、导出、编辑弹窗、右键菜单、拖拽排序等）
// ... 这里建议分模块补充

// 9. 导出INI
function handleExport() {
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
  a.download = iniFileName.replace(/\.ini$/, '') + '_export.ini';
  a.click();
}

// 10. 其它事件处理（重载、初始化、日期更新等）
function handleReload() { if (iniContent) parseIniContent(iniContent); renderSkuSelect(); renderTable(); renderInfo(); }
function handleInit() { iniFileName = ""; iniContent = ""; infoSection = { UnitCount: "", ExportDate: "" }; skuList = []; allRowsWithSku = []; currentSku = ""; renderSkuSelect(); renderTable(); renderInfo(); }
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
  if (!suffix) {
    alert('Suffix cannot be empty!');
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
function backspaceSkuSuffix() { /* 预留：实现SKU后缀回退 */ }
function gotoPrevSku() {
  const idx = skuList.indexOf(currentSku);
  if (idx > 0) { currentSku = skuList[idx - 1]; document.getElementById('skuSelect').value = currentSku; renderTable(); }
}
function gotoNextSku() {
  const idx = skuList.indexOf(currentSku);
  if (idx >= 0 && idx < skuList.length - 1) { currentSku = skuList[idx + 1]; document.getElementById('skuSelect').value = currentSku; renderTable(); }
}

// 12. 编辑弹窗、右键菜单、拖拽排序、剪贴板等
// ... 这里建议分模块补充 

// 扩展 renderTable 支持多选高亮
const _orig_renderTable = renderTable;
renderTable = function () {
  const tbody = document.getElementById('testTable').querySelector('tbody');
  tbody.innerHTML = '';
  let rows = allRowsWithSku.filter(item => item.sku === currentSku);
  if (searchTerm) {
    rows = rows.filter(item => item.row.some(v => String(v).toLowerCase().includes(searchTerm)));
  }
  rows.forEach((item, idx) => {
    const tr = document.createElement('tr');
    tr.setAttribute('data-row-index', idx);
    if (selectedRowIndices.includes(idx)) tr.classList.add('selected');
    item.row.forEach((v, i) => {
      const td = document.createElement('td');
      td.textContent = v;
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
      renderTable();
      return;
    }
    renderTable();
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
    menu.innerHTML = `
      <li data-action="edit">Edit</li>
      <li data-action="batch-edit">批量编辑</li>
      <li data-action="copy">Copy</li>
      <li data-action="delete">Delete</li>
    `;
    document.body.appendChild(menu);
  }
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
    } else if (action === 'batch-edit') {
      if (selectedRowIndices.length > 1) showBatchEditDialog(selectedRowIndices);
    } else if (action === 'copy') {
      // 可实现复制到剪贴板
      copySelectedRowsToClipboard();
    } else if (action === 'delete') {
      deleteSelectedRows();
    }
    menu.style.display = 'none';
  });
}

// 编辑弹窗
function showEditDialog(rowIndex) {
  let rows = allRowsWithSku.filter(item => item.sku === currentSku);
  if (rowIndex < 0 || rowIndex >= rows.length) return;
  let rowObj = rows[rowIndex];
  let row = rowObj.row;
  let dialog = document.createElement('div');
  dialog.className = 'modal fade';
  dialog.tabIndex = -1;
  dialog.innerHTML = `
    <div class="modal-dialog modal-lg modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Edit Test Item</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <form id="editTestItemForm">
            ${testColumns.map((col, i) => `
              <div class="mb-3 row">
                <label class="col-sm-3 col-form-label">${col}:</label>
                <div class="col-sm-9">
                  ${col === 'Index'
      ? `<input type="text" class="form-control" name="${col}" value="${row[i] || ''}" readonly>`
      : col === 'Parameters'
        ? `<textarea class="form-control" name="${col}" rows="3">${row[i] || ''}</textarea>`
        : `<input type="text" class="form-control" name="${col}" value="${row[i] || ''}">`
    }
                </div>
              </div>
            `).join('')}
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-primary" id="editTestItemSaveBtn">Save</button>
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
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
    let err = validateTestItem(newRow);
    if (err) {
      alert(err);
      return;
    }
    let globalIdx = allRowsWithSku.findIndex(item =>
      item.sku === currentSku && item.row[0] === row[0]
    );
    if (globalIdx !== -1) {
      allRowsWithSku[globalIdx].row = newRow;
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
  let lines = selectedRowIndices.map(idx => rows[idx]?.row?.join('\t')).filter(Boolean);
  if (lines.length) {
    navigator.clipboard.writeText(lines.join('\n'));    
    showAutoDismissMessage('Copied to clipboard');
  }
}
// 删除
function deleteSelectedRows() {
  let rows = allRowsWithSku.filter(item => item.sku === currentSku);
  let indices = selectedRowIndices.map(idx => rows[idx]?.row[0]);
  allRowsWithSku = allRowsWithSku.filter(item => !(item.sku === currentSku && indices.includes(item.row[0])));
  selectedRowIndices = [];
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