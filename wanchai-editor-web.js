// wanchai-editor-web.js
// 主流程：INI 文件选择/解析、Info 渲染、SKU 下拉、表格渲染、导出、重载、初始化、日期更新、搜索

let iniFileName = "";
let iniContent = "";
let infoSection = { UnitCount: "", ExportDate: "" };
let skuList = [];
let allRowsWithSku = []; // [{row:[], sku:""}]
let testColumns = ["Index","Identifier","TestID","Description","Enabled","StringLimit","LowLimit","HighLimit","LimitType","Unit","Parameters"];
let currentSku = "";
let searchTerm = "";

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
document.getElementById('btnClearSearch').addEventListener('click', ()=>{searchTerm="";document.getElementById('searchInput').value="";renderTable();});
document.getElementById('searchInput').addEventListener('input', e=>{searchTerm=e.target.value.toLowerCase();renderTable();});
document.getElementById('btnUpdateDate').addEventListener('click', updateExportDate);

// 2. 解析INI文件
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  iniFileName = file.name;
  document.getElementById('fileName').textContent = file.name;
  const reader = new FileReader();
  reader.onload = function(evt) {
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
    infoSection.UnitCount = (info.match(/UnitCount\s*=\s*(.+)/)||[])[1]||"";
    infoSection.ExportDate = (info.match(/Export Date\s*=\s*(.+)/)||[])[1]||"";
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
    const rowRegex = /^\s*(\d+)\s*=\s*\(([^)]*)\)\s*VALUES\s*\(([^)]*)\)/gm;
    let rowMatch;
    while ((rowMatch = rowRegex.exec(sectionContent)) !== null) {
      const idx = rowMatch[1];
      // const header = rowMatch[2].split(',').map(s=>s.trim());
      const values = parseRowValues(rowMatch[3]);
      let row = [idx, ...values];
      allRowsWithSku.push({row, sku: sectionName});
    }
  }
  currentSku = skuList[0] || "";
}

// 4. 渲染SKU下拉
function renderSkuSelect() {
  const sel = document.getElementById('skuSelect');
  sel.innerHTML = skuList.map(sku=>`<option value="${sku}">${sku}</option>`).join('');
  sel.value = currentSku;
}

// 5. 渲染表格
function renderTable() {
  const tbody = document.getElementById('testTable').querySelector('tbody');
  tbody.innerHTML = '';
  let rows = allRowsWithSku.filter(item=>item.sku===currentSku);
  if (searchTerm) {
    rows = rows.filter(item=>item.row.some(v=>String(v).toLowerCase().includes(searchTerm)));
  }
  rows.forEach(item=>{
    const tr = document.createElement('tr');
    item.row.forEach((v,i)=>{
      const td = document.createElement('td');
      td.textContent = v;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  document.getElementById('skuCount').textContent = rows.length + " items";
  // 移除 overlay 相关逻辑
}

// 6. 渲染Info
function renderInfo() {
  document.getElementById('unitCount').value = infoSection.UnitCount;
  document.getElementById('exportDate').value = infoSection.ExportDate;
}

// 7. 解析行数据
function parseRowValues(str) {
  // 支持引号、逗号等复杂情况
  let arr = [];
  let cur = '', inQuote = false;
  for (let i=0; i<str.length; ++i) {
    let c = str[i];
    if (c === "'") inQuote = !inQuote;
    else if (c === ',' && !inQuote) { arr.push(cur.trim().replace(/^'|'$/g,'')); cur=''; continue; }
    cur += c;
  }
  if (cur) arr.push(cur.trim().replace(/^'|'$/g,''));
  return arr;
}

// 8. 其它功能（批量操作、导出、编辑弹窗、右键菜单、拖拽排序等）
// ... 这里建议分模块补充

// 9. 导出INI
function handleExport() {
  // 重新组装INI内容
  let content = `[Info]\nUnitCount=${document.getElementById('unitCount').value}\nExport Date=${document.getElementById('exportDate').value}\n\n`;
  skuList.forEach(sku=>{
    let rows = allRowsWithSku.filter(item=>item.sku===sku);
    content += `[${sku}]\nCount=${rows.length}\n`;
    rows.forEach((item,i)=>{
      let row = item.row.slice(1); // 去掉Index
      let rowStr = row.map((v,j)=>j===2 && (v==="0"||v==="1") ? v : `'${v}'`).join(',');
      content += `${i+1}=(Identifier,TestID,Description,Enabled,StringLimit,LowLimit,HighLimit,LimitType,Unit,Parameters) VALUES (${rowStr})\n`;
    });
    content += '\n';
  });
  // 下载
  const blob = new Blob([content], {type:'text/plain'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = iniFileName.replace(/\.ini$/,'') + '_export.ini';
  a.click();
}

// 10. 其它事件处理（重载、初始化、日期更新等）
function handleReload() { if (iniContent) parseIniContent(iniContent); renderSkuSelect(); renderTable(); renderInfo(); }
function handleInit() { iniFileName=""; iniContent=""; infoSection={UnitCount:"",ExportDate:""}; skuList=[]; allRowsWithSku=[]; currentSku=""; renderSkuSelect(); renderTable(); renderInfo(); }
function updateExportDate() {
  const now = new Date();
  const dateStr = `${now.getMonth()+1}/${now.getDate()}/${now.getFullYear()} ${now.toLocaleTimeString('en-US')}`;
  document.getElementById('exportDate').value = dateStr;
}

// 11. SKU相关批量操作
function addSuffixToCurrentSku() { /* 预留：实现单SKU后缀添加 */ }
function addSuffixToAllSkus() { /* 预留：实现所有SKU批量后缀添加 */ }
function backspaceSkuSuffix() { /* 预留：实现SKU后缀回退 */ }
function gotoPrevSku() {
  const idx = skuList.indexOf(currentSku);
  if (idx > 0) { currentSku = skuList[idx-1]; document.getElementById('skuSelect').value = currentSku; renderTable(); }
}
function gotoNextSku() {
  const idx = skuList.indexOf(currentSku);
  if (idx >= 0 && idx < skuList.length-1) { currentSku = skuList[idx+1]; document.getElementById('skuSelect').value = currentSku; renderTable(); }
}

// 12. 编辑弹窗、右键菜单、拖拽排序、剪贴板等
// ... 这里建议分模块补充 