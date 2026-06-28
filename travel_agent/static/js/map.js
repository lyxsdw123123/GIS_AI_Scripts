/**
 * 高德地图管理模块
 * 负责地图初始化、标记、交互
 */
const MapManager = (() => {
  let map = null;
  let markers = [];
  let userMarker = null;
  let onMarkerClick = null; // 回调：点击 POI 标记时触发

  let amapConfig = {};

  async function init(containerId) {
    // 从后端获取 Amap key
    const resp = await fetch('/api/config');
    amapConfig = await resp.json();
    const jsKey = amapConfig.amap_js_key;

    // 动态加载高德 JS API
    try {
      await new Promise((resolve, reject) => {
        if (window.AMap) return resolve();
        const script = document.createElement('script');
        script.src = `https://webapi.amap.com/maps?v=2.0&key=${jsKey}`;
        script.onload = () => {
          if (!window.AMap) return reject(new Error('AMap 未定义'));
          resolve();
        };
        script.onerror = () => reject(new Error('地图服务加载失败，请确认 Amap Key 已开通 Web端(JS API) 服务'));
        document.head.appendChild(script);
      });
    } catch (e) {
      const ph = document.getElementById('map-placeholder');
      if (ph) {
        ph.innerHTML = `<div class="placeholder-icon">⚠️</div><p>${e.message}</p><p style="font-size:12px;margin-top:4px;">👉 去 <a href="https://console.amap.com/dev/key/app/" target="_blank">高德控制台</a> 开通 Web端(JS API)</p>`;
        ph.classList.remove('hidden');
      }
      throw e;
    }

    map = new AMap.Map(containerId, {
      zoom: 13,
      center: [116.397428, 39.90923], // 默认北京
      mapStyle: 'amap://styles/whitesmoke',
      resizeEnable: true,
      touchZoom: true,
      dragEnable: true,
    });

    // 添加地图控件
    map.addControl(new AMap.Scale({ position: 'LB' }));
    map.addControl(new AMap.ToolBar({ position: 'RT', liteStyle: true }));

    // 点击 POI 标记的回调
    map.on('click', (e) => {
      // 检查是否点击了 marker
      const features = map.getAllOverlays('marker');
      // 点击空白处不做处理
    });

    return map;
  }

  /** 设置用户位置 */
  function setUserLocation(lng, lat, name) {
    if (!map) return;
    if (userMarker) { map.remove(userMarker); }

    userMarker = new AMap.Marker({
      position: [lng, lat],
      icon: new AMap.Icon({
        size: new AMap.Size(32, 44),
        image: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',
        imageSize: new AMap.Size(32, 44),
      }),
      title: name || '我的位置',
      zIndex: 100,
    });
    map.add(userMarker);
    map.setCenter([lng, lat]);
    map.setZoom(14);
  }

  /** 批量添加 POI 标记 */
  function setPOIMarkers(pois, clickCallback) {
    if (!map) return;
    clearPOIMarkers();
    onMarkerClick = clickCallback;

    pois.forEach((poi, i) => {
      const marker = new AMap.Marker({
        position: [poi.lng, poi.lat],
        icon: new AMap.Icon({
          size: new AMap.Size(28, 36),
          image: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png',
          imageSize: new AMap.Size(28, 36),
        }),
        title: poi.name,
        label: {
          content: `<span style="background:#f97316;color:#fff;padding:2px 6px;border-radius:8px;font-size:11px;white-space:nowrap;">${i+1}.${poi.name}</span>`,
          direction: 'top',
          offset: new AMap.Pixel(0, -10),
        },
        extData: poi,
        zIndex: 90,
      });

      marker.on('click', () => {
        if (onMarkerClick) onMarkerClick(poi);
      });

      map.add(marker);
      markers.push(marker);
    });

    // 自动调整视野包含所有点
    if (pois.length > 0) {
      map.setFitView(null, false, [60, 60, 60, 60]);
    }
  }

  /** 定位到某个 POI */
  function flyTo(lng, lat) {
    if (!map) return;
    map.setZoomAndCenter(16, [lng, lat]);
  }

  /** 清除所有 POI 标记 */
  function clearPOIMarkers() {
    markers.forEach(m => map && map.remove(m));
    markers = [];
  }

  /** 通过地理编码搜索位置（使用 Web Service Key） */
  async function geocode(address, city) {
    const url = new URL('https://restapi.amap.com/v3/geocode/geo');
    url.searchParams.set('key', amapConfig.amap_ws_key || amapConfig.amap_js_key);
    url.searchParams.set('address', address);
    if (city) url.searchParams.set('city', city);
    const data = await (await fetch(url)).json();
    if (data.status === '1' && data.geocodes.length > 0) {
      const loc = data.geocodes[0].location.split(',');
      return { lng: parseFloat(loc[0]), lat: parseFloat(loc[1]), name: data.geocodes[0].formatted_address };
    }
    return null;
  }

  return { init, setUserLocation, setPOIMarkers, flyTo, clearPOIMarkers, geocode };
})();
