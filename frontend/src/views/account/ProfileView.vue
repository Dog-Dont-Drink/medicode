<template>
  <div class="max-w-3xl mx-auto space-y-6 animate-fade-in">
    <h1 class="text-2xl font-heading font-bold text-gray-900">个人资料</h1>
    <div class="card space-y-6">
      <div class="flex items-center gap-5">
        <div class="w-20 h-20 bg-gradient-to-br from-primary to-accent rounded-2xl flex items-center justify-center shadow-card">
          <span class="text-2xl font-bold text-white">张</span>
        </div>
        <div>
          <h2 class="text-xl font-semibold text-gray-900">张医生</h2>
          <p class="text-gray-500">zhangdoctor@hospital.com</p>
          <button class="text-sm text-primary hover:underline mt-1 cursor-pointer">更换头像</button>
        </div>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div><label class="block text-sm font-medium text-gray-700 mb-1.5">姓名</label><input type="text" value="张医生" class="input-field" /></div>
        <div><label class="block text-sm font-medium text-gray-700 mb-1.5">邮箱</label><input type="email" value="zhangdoctor@hospital.com" class="input-field" disabled /></div>
        <div><label class="block text-sm font-medium text-gray-700 mb-1.5">所属机构</label><input type="text" value="北京协和医院" class="input-field" /></div>
        <div><label class="block text-sm font-medium text-gray-700 mb-1.5">职称</label><input type="text" value="副主任医师" class="input-field" /></div>
        <div class="md:col-span-2"><label class="block text-sm font-medium text-gray-700 mb-1.5">研究方向</label><input type="text" value="内分泌代谢疾病" class="input-field" /></div>
      </div>
      <div class="flex justify-end"><button class="btn-primary">保存修改</button></div>
    </div>
  </div>
</template>
<script setup lang="ts"></script>
