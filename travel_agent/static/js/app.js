/**
 * 小旅 · 主应用逻辑
 * 管理状态输入、聊天、地图联动
 */
const App = (() => {
  // ── 用户状态 ──
  const state = {
    location: '',
    mood: 6,
    fatigue: 5,
    curiosity: 5,
    budget: '',
    companion: '',
    preferences: [],
  };

  let chatHistory = [];
  let currentPOIs = [];

  // ── DOM 引用 ──
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // ── 初始化 ──
  async function init() {
    // 初始化地图
    try {
      await MapManager.init('map-container');
      $('#map-placeholder').classList.add('hidden');
    } catch (e) {
      console.warn('地图初始化失败:', e);
      // 地图加载失败也不影响核心功能
    }

    bindEvents();
  }

  // ── 事件绑定 ──
  function bindEvents() {
    // 状态面板折叠
    $('#state-toggle').addEventListener('click', () => {
      $('#state-panel').classList.toggle('collapsed');
    });

    // Emoji 选择器
    $$('.emoji-picker').forEach(picker => {
      picker.addEventListener('click', (e) => {
        const btn = e.target.closest('button');
        if (!btn) return;
        picker.querySelectorAll('button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state[picker.dataset.key] = parseInt(btn.dataset.value);
      });
    });

    // 滑块
    $('#slider-fatigue').addEventListener('input', (e) => {
      state.fatigue = parseInt(e.target.value);
    });
    $('#slider-curiosity').addEventListener('input', (e) => {
      state.curiosity = parseInt(e.target.value);
    });

    // Chip 单选
    $$('.chip-group:not(.multi)').forEach(group => {
      group.addEventListener('click', (e) => {
        const btn = e.target.closest('button');
        if (!btn) return;
        group.querySelectorAll('button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state[group.dataset.key] = btn.dataset.value;
      });
    });

    // Chip 多选（偏好）
    $$('.chip-group.multi').forEach(group => {
      group.addEventListener('click', (e) => {
        const btn = e.target.closest('button');
        if (!btn) return;
        btn.classList.toggle('active');
        const selected = group.querySelectorAll('button.active');
        state[group.dataset.key] = Array.from(selected).map(b => b.dataset.value);
      });
    });

    // 位置输入
    $('#input-location').addEventListener('input', (e) => {
      state.location = e.target.value.trim();
    });

    // 自动定位
    $('#btn-locate').addEventListener('click', async () => {
      $('#btn-locate').textContent = '⏳';
      try {
        // 尝试 IP 定位（高德）
        const resp = await fetch('/api/config');
        const cfg = await resp.json();
        const ipUrl = `https://restapi.amap.com/v3/ip?key=${cfg.amap_ws_key}`;
        const data = await (await fetch(ipUrl)).json();
        if (data.status === '1' && data.city) {
          $('#input-location').value = data.city;
          state.location = data.city;
          // 尝试定位到城市中心
          const geo = await MapManager.geocode(data.city, data.city);
          if (geo) {
            MapManager.setUserLocation(geo.lng, geo.lat, geo.name);
            updateHeader(geo.name);
            $('#map-placeholder').classList.add('hidden');
          }
        }
      } catch (e) {
        console.warn('IP定位失败:', e);
      }
      $('#btn-locate').textContent = '📍';
    });

    // 规划按钮
    $('#btn-plan').addEventListener('click', async () => {
      const msg = buildStateMessage();
      if (!msg) {
        alert('请至少输入你的位置 📍');
        return;
      }
      await sendMessage(msg);
      // 折叠状态面板
      $('#state-panel').classList.add('collapsed');
    });

    // 发送按钮
    $('#btn-send').addEventListener('click', () => {
      const input = $('#input-chat');
      const msg = input.value.trim();
      if (!msg) return;
      input.value = '';
      sendMessage(msg);
    });

    // 回车发送
    $('#input-chat').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        $('#btn-send').click();
      }
    });

    // POI 详情关闭
    $('#poi-detail-close').addEventListener('click', () => {
      $('#poi-detail').classList.add('hidden');
    });
  }

  // ── 构建状态消息 ──
  function buildStateMessage() {
    if (!state.location) return '';

    const parts = [`我在${state.location}`];
    parts.push(`心情指数${state.mood}/10`);
    parts.push(`疲惫度${state.fatigue}/10`);
    parts.push(`好奇心${state.curiosity}/10`);

    if (state.companion) parts.push(`和${state.companion}一起`);
    if (state.preferences.length) parts.push(`偏好：${state.preferences.join('、')}`);
    if (state.budget) parts.push(`预算：${state.budget}`);

    return parts.join('，') + '，推荐去哪里？';
  }

  // ── 发送消息 ──
  async function sendMessage(msg) {
    showLoading(true);

    // 显示用户消息
    appendMessage('user', msg);

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: msg,
          history: chatHistory,
          state: {
            location: state.location,
            mood: state.mood,
            fatigue: state.fatigue,
            curiosity: state.curiosity,
            budget: state.budget,
            companion: state.companion,
            preferences: state.preferences.join('、'),
          }
        }),
      });

      if (!resp.ok) {
        const err = await resp.json();
        appendMessage('assistant', `出错了：${err.detail}`);
        return;
      }

      const data = await resp.json();
      chatHistory.push({ role: 'user', content: msg });
      chatHistory.push({ role: 'assistant', content: data.reply });

      // 渲染回复
      appendMessage('assistant', data.reply);

      // 更新地图
      if (data.pois && data.pois.length > 0) {
        currentPOIs = data.pois;
        $('#map-placeholder').classList.add('hidden');

        // 地图上标 POI
        MapManager.setPOIMarkers(data.pois, (poi) => {
          showPOIDetail(poi);
        });

        // 聊天区渲染卡片
        renderPOICards(data.pois);
      }

      if (data.city) {
        updateHeader(data.city);
        // 尝试定位用户城市
        if (!state.location || state.location !== data.city) {
          const geo = await MapManager.geocode(data.city, data.city);
          if (geo) MapManager.setUserLocation(geo.lng, geo.lat, geo.name);
        }
      }

      // 滚动到底部
      $('#chat-messages').scrollIntoView({ behavior: 'smooth', block: 'end' });

    } catch (e) {
      appendMessage('assistant', `网络错误：${e.message}`);
    }

    showLoading(false);
  }

  // ── 渲染推荐卡片 ──
  function renderPOICards(pois) {
    if (pois.length === 0) return;

    const container = document.createElement('div');
    container.className = 'msg-bubble msg-assistant';
    container.style.padding = '0';
    container.style.background = 'transparent';
    container.style.boxShadow = 'none';

    pois.forEach((poi, i) => {
      const card = document.createElement('div');
      card.className = 'poi-card';
      card.innerHTML = `
        <div class="poi-name">${i + 1}. ${poi.name}</div>
        <div class="poi-meta">
          <span>📍 ${poi.address || ''}</span>
          ${poi.rating ? `<span>⭐ ${poi.rating}</span>` : ''}
        </div>
      `;
      card.addEventListener('click', () => {
        MapManager.flyTo(poi.lng, poi.lat);
        showPOIDetail(poi);
      });
      container.appendChild(card);
    });

    $('#chat-messages').appendChild(container);
    container.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }

  // ── POI 详情浮层 ──
  function showPOIDetail(poi) {
    $('#poi-detail-name').textContent = poi.name;
    $('#poi-detail-addr').textContent = '📍 ' + (poi.address || '暂无地址');
    $('#poi-detail-rating').textContent = poi.rating ? '⭐ ' + poi.rating : '';
    $('#poi-detail').classList.remove('hidden');

    // "了解更多" 按钮
    $('#btn-ask-more').onclick = () => {
      $('#poi-detail').classList.add('hidden');
      $('#input-chat').value = `详细介绍一下「${poi.name}」吧，包括游玩建议和周边`;
      $('#btn-send').click();
    };
  }

  // ── Markdown → HTML 渲染 ──
  function renderMarkdown(text) {
    const lines = text.split('\n');
    let html = '';
    let inList = false, listType = '';

    for (let i = 0; i < lines.length; i++) {
      let line = lines[i];

      // 空行：关闭列表
      if (!line.trim()) {
        if (inList) { html += `</${listType}>`; inList = false; }
        html += '<div class="md-spacer"></div>';
        continue;
      }

      // 水平线
      if (/^[-*_]{3,}$/.test(line.trim())) {
        if (inList) { html += `</${listType}>`; inList = false; }
        html += '<div class="md-divider"></div>';
        continue;
      }

      // 标题
      let heading = line.match(/^#{1,3}\s+(.+)/);
      if (heading) {
        if (inList) { html += `</${listType}>`; inList = false; }
        const level = line.match(/^(#{1,3})/)[1].length;
        html += `<h${level+2} class="md-heading">${heading[1]}</h${level+2}>`;
        continue;
      }

      // 无序列表
      let ulItem = line.match(/^[-*]\s+(.+)/);
      if (ulItem) {
        if (!inList || listType !== 'ul') {
          if (inList) html += `</${listType}>`;
          html += '<ul class="md-list">';
          inList = true; listType = 'ul';
        }
        html += `<li>${ulItem[1]}</li>`;
        continue;
      }

      // 有序列表
      let olItem = line.match(/^\d+[.)]\s+(.+)/);
      if (olItem) {
        if (!inList || listType !== 'ol') {
          if (inList) html += `</${listType}>`;
          html += '<ol class="md-list">';
          inList = true; listType = 'ol';
        }
        html += `<li>${olItem[1]}</li>`;
        continue;
      }

      // 引用
      let quote = line.match(/^>\s?(.+)/);
      if (quote) {
        if (inList) { html += `</${listType}>`; inList = false; }
        html += `<blockquote class="md-quote">${quote[1]}</blockquote>`;
        continue;
      }

      // 普通段落
      if (inList) { html += `</${listType}>`; inList = false; }
      html += `<p class="md-p">${line}</p>`;
    }

    if (inList) html += `</${listType}>`;

    // 内联格式
    html = html
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/~~(.+?)~~/g, '<del>$1</del>')
      .replace(/`(.+?)`/g, '<code class="md-code">$1</code>');

    // emoji 大标题行单独处理（行首1-2个emoji + 文字）
    html = html.replace(
      /<p class="md-p">((?:[\u{1F300}-\u{1FAFF}]|[\u{2600}-\u{27BF}]){1,2}\s*.+?)<\/p>/gu,
      '<p class="md-p md-emoji-line">$1</p>'
    );

    return html;
  }

  // ── 添加消息气泡 ──
  function appendMessage(role, text) {
    const bubble = document.createElement('div');
    bubble.className = `msg-bubble msg-${role}`;
    bubble.innerHTML = renderMarkdown(text);
    $('#chat-messages').appendChild(bubble);
    bubble.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }

  // ── 更新顶栏 ──
  function updateHeader(city) {
    if (city) $('#header-location').textContent = '📍 ' + city;
  }

  // ── 加载状态 ──
  function showLoading(show) {
    if (show) {
      $('#loading-overlay').classList.remove('hidden');
    } else {
      $('#loading-overlay').classList.add('hidden');
    }
  }

  // ── 启动 ──
  document.addEventListener('DOMContentLoaded', init);

  return { sendMessage };
})();
