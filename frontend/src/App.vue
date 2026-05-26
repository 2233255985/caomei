<template>
  <div id="app-shell">
    <nav class="nav-bar">
      <div class="nav-title">🍓 草莓检测系统</div>
      <div class="nav-links">
        <router-link to="/">检测</router-link>
        <router-link to="/dashboard">数据仪表盘</router-link>
        <router-link to="/history">历史记录</router-link>
        <router-link to="/settings">设置</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #333; }
#app-shell { min-height: 100vh; display: flex; flex-direction: column; }
.nav-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; height: 56px;
  background: linear-gradient(135deg, #e53935, #c62828);
  color: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.nav-title { font-size: 20px; font-weight: 600; }
.nav-links { display: flex; gap: 20px; }
.nav-links a { color: rgba(255,255,255,0.9); text-decoration: none; font-size: 15px; padding: 6px 12px; border-radius: 4px; transition: background 0.2s; }
.nav-links a:hover { background: rgba(255,255,255,0.15); }
.nav-links a.router-link-active { background: rgba(255,255,255,0.25); font-weight: 500; }
.main-content { flex: 1; padding: 24px; max-width: 1200px; width: 100%; margin: 0 auto; }
</style>
