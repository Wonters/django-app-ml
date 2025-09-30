<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- Titre -->
      <el-col :span="24">
        <div class="page-header">
          <h1>Dashboard ML</h1>
          <p>Vue d'ensemble de vos modèles et expériences</p>
        </div>
      </el-col>
    </el-row>

    <!-- Métriques -->
    <el-row :gutter="20" class="metrics-row">
      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-content">
            <div class="metric-icon">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="metric-info">
              <h3>{{ metrics.totalModels }}</h3>
              <p>Modèles</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-content">
            <div class="metric-icon">
              <el-icon><Tools /></el-icon>
            </div>
            <div class="metric-info">
              <h3>{{ metrics.totalExperiments }}</h3>
              <p>Expériences</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-content">
            <div class="metric-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="metric-info">
              <h3>{{ metrics.totalPredictions }}</h3>
              <p>Prédictions</p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="metric-card">
          <div class="metric-content">
            <div class="metric-icon">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="metric-info">
              <h3>{{ metrics.activeTasks }}</h3>
              <p>Tâches actives</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Graphiques -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>Performance des modèles</span>
            </div>
          </template>
          <div class="chart-container">
            <canvas ref="performanceChart"></canvas>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>Expériences récentes</span>
            </div>
          </template>
          <div class="chart-container">
            <canvas ref="experimentsChart"></canvas>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Modèles récents -->
    <el-row :gutter="20" class="recent-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>Modèles récents</span>
              <el-button type="primary" size="small" @click="$router.push('/models')">
                Voir tous
              </el-button>
            </div>
          </template>
          <el-table :data="recentModels" style="width: 100%">
            <el-table-column prop="name" label="Nom" />
            <el-table-column prop="algorithm" label="Algorithme" />
            <el-table-column prop="version" label="Version" />
            <el-table-column prop="accuracy" label="Précision">
              <template #default="scope">
                <el-progress 
                  :percentage="scope.row.accuracy * 100" 
                  :format="(val) => `${(val).toFixed(1)}%`"
                />
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="Créé le">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { DataAnalysis, Tools, TrendCharts, Clock } from '@element-plus/icons-vue'
import Chart from 'chart.js/auto'

export default {
  name: 'Dashboard',
  components: {
    DataAnalysis,
    Tools,
    TrendCharts,
    Clock
  },
  setup() {
    const performanceChart = ref(null)
    const experimentsChart = ref(null)
    
    const metrics = ref({
      totalModels: 12,
      totalExperiments: 45,
      totalPredictions: 1234,
      activeTasks: 3
    })

    const recentModels = ref([
      {
        name: 'Random Forest Classifier',
        algorithm: 'Random Forest',
        version: '1.2.0',
        accuracy: 0.95,
        created_at: '2024-01-15'
      },
      {
        name: 'Neural Network',
        algorithm: 'Deep Learning',
        version: '2.1.0',
        accuracy: 0.92,
        created_at: '2024-01-14'
      },
      {
        name: 'SVM Classifier',
        algorithm: 'Support Vector Machine',
        version: '1.0.0',
        accuracy: 0.88,
        created_at: '2024-01-13'
      }
    ])

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('fr-FR')
    }

    onMounted(() => {
      // Performance Chart
      const performanceCtx = performanceChart.value.getContext('2d')
      new Chart(performanceCtx, {
        type: 'line',
        data: {
          labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun'],
          datasets: [{
            label: 'Précision moyenne',
            data: [0.85, 0.87, 0.89, 0.91, 0.93, 0.95],
            borderColor: '#409EFF',
            backgroundColor: 'rgba(64, 158, 255, 0.1)',
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 1
            }
          }
        }
      })

      // Experiments Chart
      const experimentsCtx = experimentsChart.value.getContext('2d')
      new Chart(experimentsCtx, {
        type: 'doughnut',
        data: {
          labels: ['Succès', 'En cours', 'Échec'],
          datasets: [{
            data: [35, 8, 2],
            backgroundColor: ['#67C23A', '#E6A23C', '#F56C6C']
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      })
    })

    return {
      metrics,
      recentModels,
      performanceChart,
      experimentsChart,
      formatDate
    }
  }
}
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0;
  color: #2c3e50;
  font-size: 2rem;
}

.page-header p {
  margin: 10px 0 0 0;
  color: #7f8c8d;
}

.metrics-row {
  margin-bottom: 30px;
}

.metric-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.metric-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.metric-icon {
  font-size: 2rem;
  color: #409EFF;
}

.metric-info h3 {
  margin: 0;
  font-size: 1.8rem;
  color: #2c3e50;
}

.metric-info p {
  margin: 5px 0 0 0;
  color: #7f8c8d;
}

.charts-row {
  margin-bottom: 30px;
}

.chart-container {
  height: 300px;
  position: relative;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recent-row {
  margin-bottom: 20px;
}
</style> 