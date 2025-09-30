<template>
  <div id="app">
    <el-container class="app-container">
      <!-- Header -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="logo">
            <el-icon><DataAnalysis /></el-icon>
            <span>Django ML App</span>
          </div>
          <el-menu
            mode="horizontal"
            :router="true"
            class="nav-menu"
            background-color="transparent"
            text-color="#fff"
            active-text-color="#409EFF"
          >
            <el-menu-item index="/">Dashboard</el-menu-item>
            <el-menu-item index="/models">Modèles</el-menu-item>
            <el-menu-item index="/experiments">Expériences</el-menu-item>
            <el-menu-item index="/predictions">Prédictions</el-menu-item>
            <el-menu-item index="/tasks">Tâches</el-menu-item>
          </el-menu>
          <div class="user-menu">
            <el-dropdown>
              <el-avatar :size="32" icon="UserFilled" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>Profil</el-dropdown-item>
                  <el-dropdown-item>Paramètres</el-dropdown-item>
                  <el-dropdown-item divided>Déconnexion</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <!-- Main Content -->
      <el-main class="app-main">
        <router-view />
      </el-main>

      <!-- Footer -->
      <el-footer class="app-footer">
        <p>&copy; 2024 Django ML App. Tous droits réservés.</p>
      </el-footer>
    </el-container>
  </div>
</template>

<script>
import { DataAnalysis } from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    DataAnalysis
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  font-size: 1.5rem;
  font-weight: bold;
  gap: 8px;
}

.nav-menu {
  border: none;
}

.nav-menu .el-menu-item {
  color: white;
  font-weight: 500;
}

.nav-menu .el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.nav-menu .el-menu-item.is-active {
  background-color: rgba(255, 255, 255, 0.2);
}

.user-menu {
  display: flex;
  align-items: center;
}

.app-main {
  background-color: #f5f7fa;
  padding: 20px;
}

.app-footer {
  background-color: #2c3e50;
  color: white;
  text-align: center;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style> 