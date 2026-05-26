<template>
  <div class="history-table">
    <div v-if="items.length === 0" class="empty">暂无检测记录</div>
    <table v-else class="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>图片</th>
          <th>草莓数</th>
          <th>平均置信度</th>
          <th>后端</th>
          <th>时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>{{ item.id }}</td>
          <td><img :src="item.image_url" class="thumb" @click="$emit('view-detail', item)" /></td>
          <td>{{ item.count }}</td>
          <td>{{ (item.avg_confidence * 100).toFixed(1) }}%</td>
          <td>{{ item.backend === 'local' ? '本地' : 'Atlas' }}</td>
          <td>{{ item.created_at?.slice(0, 19) }}</td>
          <td><button class="btn-delete" @click="$emit('delete', item.id)">删除</button></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({ items: { type: Array, default: () => [] } })
defineEmits(['view-detail', 'delete'])
</script>

<style scoped>
.empty { padding: 40px; text-align: center; color: #888; }
.table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; font-size: 14px; }
th { background: #f5f5f5; color: #666; font-weight: 500; }
.thumb { width: 60px; height: 60px; object-fit: cover; border-radius: 4px; cursor: pointer; }
.btn-delete { padding: 4px 12px; background: #fff0f0; color: #e53935; border: 1px solid #ffcdd2; border-radius: 4px; cursor: pointer; font-size: 13px; }
.btn-delete:hover { background: #e53935; color: #fff; }
</style>
