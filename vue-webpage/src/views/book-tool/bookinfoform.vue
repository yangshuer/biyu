<template>
  <div class="container">
    <!-- 添加模态框 -->
    <div class="modal" v-if="showModal" @click.self="closeModal">
      <div class="modal-content">
        <img :src="selectedImage" class="modal-image" />
      </div>
    </div>
    <div class="form-wrapper">
      <!-- 名称输入 -->
      <div class="form-group">
        <label>作品名称</label>
        <input v-model="workName" @blur="workName = trimText(workName)" type="text" class="form-input"
          placeholder="输入作品名称" />
      </div>

      <!-- 封面区域 -->
      <div class="form-group">
        <label>作品封面</label>
        <div class="form-group" style="display: flex">
          <input v-model="coverPrompt" @blur="coverPrompt = trimText(coverPrompt)" type="text" class="form-input"
            placeholder="输入封面生成提示词，例如：仙侠风格，水墨画，主角御剑飞行" />
          <el-button type="primary" class="generate-btn" style="height: 36px; margin-left: 10px" @click="generateCover">
            AI生成封面
          </el-button>
        </div>
        <div class="cover-grid">
          <div class="cover-item" style="outline: 2px solid hsla(160, 100%, 37%, 0.8)">
            <el-image v-if="cover !== ''" :src="cover" class="cover-image" :alt="`封面选项${index + 1}`"
              :preview-src-list="[cover]" :initial-index="0" :zoom-rate="1.2" :max-scale="7" :min-scale="0.2"
              fit="cover" hide-on-click-modal />
            <img v-if="cover === ''" src="../../assets/book-covers.jpeg" class="cover-image"
              :alt="`封面选项${index + 1}`" />
          </div>
          <div v-for="(cover, index) in covers" :key="index" class="cover-item"
            :class="{ selected: selectedCover === index }" @click="selectCover(index)">
            <img v-if="cover.url !== ''" :src="cover.url" class="cover-image" :alt="`封面选项${index + 1}`" />
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100%;
                color: #6b7280;
              " v-if="(cover.url === '') & (coverCreateStatus === 0)">
              尚未生成封面～
            </div>
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100%;
                color: #6b7280;
                font-weight: bold;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
              " v-if="(cover.url === '') & (coverCreateStatus === 1)">
              封面生成中-{{ createvalue }} %
            </div>
          </div>
        </div>
      </div>

      <!-- 标签输入 -->
      <div class="form-group">
        <label>作品标签</label>
        <input v-model="tags" @blur="tags = trimText(tags)" type="text" class="form-input"
          placeholder="输入标签以逗号分隔。例如：玄幻，逆袭……" />
      </div>

      <!-- 简介输入 -->
      <div class="form-group">
        <label>作品简介</label>
        <div class="textarea-wrapper">
          <textarea v-model="description" @blur="description = trimText(description)" rows="6" class="form-textarea"
            placeholder="输入作品简介，需要大于100字。例如：讲述山村少年韩立凭借借助神秘小瓶逆天改命、踏上修仙长生的传奇历程。"></textarea>
          <div class="counter">{{ description.length }}/1000</div>
        </div>
      </div>

      <!-- 设定区域 -->
      <div class="settings-grid">
        <div class="form-group">
          <label>时间设定</label>
          <textarea v-model="timeSetting" @blur="timeSetting = trimText(timeSetting)" rows="4" class="form-textarea"
            placeholder="请输入时间设定。例如：类比中国古代唐宋时期发展水平。"></textarea>
        </div>
        <div class="form-group">
          <label>空间设定</label>
          <textarea v-model="spaceSetting" @blur="spaceSetting = trimText(spaceSetting)" rows="4" class="form-textarea"
            placeholder="请输入空间设定。例如：类比中国西南地区的地理特征。"></textarea>
        </div>
      </div>

      <!-- 底部按钮 -->
      <div class="button-group">
        <button class="cancel-button" @click="cancel">取消</button>
        <button class="save-button" @click="save">保存</button>
      </div>
    </div>
  </div>
</template>

<script>
import { fetchEventSource } from '@microsoft/fetch-event-source'
export default {
  data() {
    return {
      bookid: null,
      workName: '',
      coverPrompt: '',
      selectedCover: null,
      tags: '',
      description: '',
      timeSetting: '',
      spaceSetting: '',
      cover: '',
      coverCreateStatus: 0, //生成状态 0-未在进行；1-在进行
      createvalue: 0, //生成进度
      covers: [{ url: '' }, { url: '' }, { url: '' }, { url: '' }],
      showModal: false, // 新增
      selectedImage: '', // 新增
    }
  },
  async created() {
    // 在进入页面的时候从localStorage获取当前作业 作品 ID「currentBookId」 复制给this.bookid 如果获取不到则赋值为 null
    this.bookid = localStorage.getItem('currentBookId') || null
    // 如果this.bookid 不是 null 则查询书籍信息，回显到当前页面
    if (this.bookid) {
      const loadingInstance = this.$loading({
        lock: true,
        text: '加载中...',
        background: 'rgba(0, 0, 0, 0.7)',
      })
      try {
        const response = await this.$axios.get('/manages/bookinfo', {
          params: {
            id: this.bookid,
          },
          headers: {
            'X-Auth-Token': localStorage.getItem('token'),
          },
        })

        if (response.data) {
          this.workName = response.data.title || ''
          this.tags = response.data.tags || ''
          this.description = response.data.summary || ''
          this.cover = response.data.surface_plot || ''
          // console.log('=====',response.data.surface_plot)
          this.spaceSetting = response.data.space_setting || ''
          this.timeSetting = response.data.time_setting || ''
        }
      } catch (error) {
        console.error('获取书籍信息失败:', error)
        this.$message.error('获取书籍信息失败')
      } finally {
        loadingInstance.close()
      }
    }
  },
  methods: {
    async generateCover() {
      if (this.workName === '') {
        this.$message.error('请输入作品名称')
        return
      }
      if (this.coverPrompt === '') {
        this.$message.error('请输入封面生成提示词')
        return
      }

      // 重置状态
      this.coverCreateStatus = 1
      this.createvalue = 0
      this.selectedCover = null
      this.covers = Array(4)
        .fill()
        .map(() => ({ url: '' }))

      const controller = new AbortController()
      try {
        await fetchEventSource('/agents/create-covers', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'text/event-stream',
            'X-Auth-Token': localStorage.getItem('token'),
          },
          body: JSON.stringify({
            prompt: this.coverPrompt,
            book_name: this.workName,
            book_author: JSON.parse(localStorage.getItem('userInfo'))?.username || '',
          }),
          openWhenHidden: true, // 防止挂起重试！！！！避免重复请求后端
          signal: controller.signal,
          onopen: async (response) => {
            if (response.status !== 200) {
              controller.abort()
              if (response.status === 401) {
                this.$message.error('登录已过期，请重新登录')
                this.$router.push('/login')
              } else {
                this.$message.error('封面生成服务异常')
              }
              this.coverCreateStatus = 0
            }
          },
          onmessage: (event) => {
            try {
              const data = JSON.parse(event.data)

              if (data.error) {
                this.$message.error(data.error)
                this.coverCreateStatus = 0
                controller.abort()
                return
              }

              if (data.status === '[DONE]') {
                this.coverCreateStatus = 0
                this.$message.success('封面生成完成')
                return
              }

              if (data.progress) {
                this.createvalue = data.progress
              }

              if (data.cover) {
                const newCovers = [...this.covers]
                const currentIndex =
                  newCovers.findIndex((c) => c.url === '') !== -1
                    ? newCovers.findIndex((c) => c.url === '')
                    : newCovers.length - 1
                newCovers[currentIndex] = { url: `data:image/png;base64,${data.cover}` }
                this.covers = newCovers // 直接替换整个数组
              }
            } catch (e) {
              console.error('解析封面数据失败', e)
            }
          },
          onerror: (err) => {
            this.$message.error('封面生成失败')
            this.coverCreateStatus = 0
            controller.abort()
          },
          onclose: () => {
            this.coverCreateStatus = 0
          },
        })
      } catch (err) {
        this.$message.error('封面生成请求失败')
        this.coverCreateStatus = 0
      }
    },
    trimText(text) {
      if (typeof text !== 'string') return text
      // 去除前后空格
      let trimmed = text.trim()
      // 检查是否仅包含空格
      if (trimmed === '') return ''
      return trimmed
    },
    selectCover(index) {
      // 封面选择
      if (this.covers[index].url === '') {
        return
      }
      this.selectedCover = index
      this.cover = this.covers[index].url
    },
    show() {
      this.showModal = true // 显示模态框
      this.selectedImage = this.cover // 设置选中图片
    },
    closeModal() {
      this.showModal = false // 关闭模态框
    },
    cancel() {
      this.workName = ''
      this.selectedCover = 0
      this.tags = ''
      this.description = ''
      this.timeSetting = ''
      this.spaceSetting = ''
    },
    async save() {
      this.$loading({
        lock: true,
        text: '保存中...',
        background: 'rgba(0, 0, 0, 0.7)',
      })
      let cover_url
      let param
      try {
        cover_url = await this.coversaveoss()
      } catch (error) {
        this.$message.error('资源上传失败')
      }
      // 校验待提交数据是否为空
      if (!this.workName) {
        this.$message.error('作品名称不能为空')
        this.$loading().close()
        return
      }
      if (!this.tags) {
        this.$message.error('标签不能为空')
        this.$loading().close()
        return
      }
      if (!this.description) {
        this.$message.error('作品简介不能为空')
        this.$loading().close()
        return
      }
      if (!this.timeSetting) {
        this.$message.error('时间设定不能为空')
        this.$loading().close()
        return
      }
      if (!this.spaceSetting) {
        this.$message.error('空间设定不能为空')
        this.$loading().close()
        return
      }
      // 调接口保存作品
      if (this.bookid) {
        param = {
          userid: JSON.parse(localStorage.getItem('userInfo'))?.userId,
          bookid: this.bookid,
          name: this.workName,
          covers: cover_url,
          tag: this.tags,
          introduction: this.description,
          timeSetting: this.timeSetting,
          spaceSetting: this.spaceSetting,
        }
      } else {
        param = {
          userid: JSON.parse(localStorage.getItem('userInfo'))?.userId,
          name: this.workName,
          covers: cover_url,
          tag: this.tags,
          introduction: this.description,
          timeSetting: this.timeSetting,
          spaceSetting: this.spaceSetting,
        }
      }
      // 打印提交数据
      // console.log(param);
      try {
        const res = await this.$axios.post('/manages/savebook', param, {
          headers: {
            'X-Auth-Token': localStorage.getItem('token'),
          },
        })

        if (res.data.message) {
          if (this.bookid === null) {
            this.bookid = res.data.book_id
            console.log(res)
          }
          this.$message.success(res.data.message)
          // 保存成功后将localStorage当前作业 作品 ID「currentBookId」修改为res.data.book_id
          localStorage.setItem('currentBookId', res.data.book_id)
        }
      } catch (error) {
        if (error.response) {
          if (error.response.status === 401) {
            this.$message.error('登录已过期，请重新登录')
            this.$router.push('/login')
          } else {
            this.$message.error(error.response.data.error || '保存失败')
          }
        } else {
          this.$message.error('网络错误，请稍后重试')
        }
        console.error('保存失败:', error)
      }
      this.$loading().close() //关闭loading
    },
    async coversaveoss() {
      // 将图片存储到oss
      if (this.cover === '') {
        return ''
      }
      // 如果this.cover就是一个url 非 base64则直接返回地址
      if (this.cover !== '' && !this.cover.startsWith('data:image')) {
        return this.cover
      }
      // 1. 获取预签名地址
      try {
        const response = await this.$axios.get('/manages/oss_put_url', {
          headers: {
            'X-Auth-Token': localStorage.getItem('token'),
          },
          params: {
            key: `${JSON.parse(localStorage.getItem('userInfo'))?.userId || ''}_${Date.now()}.jpg`, // 使用用户ID+时间戳作为文件名
          },
        })
        const presignedUrl = response.data.url
        // 2. 将图片base64转为二进制
        const base64Data = this.cover.replace(/^data:image\/\w+;base64,/, '') //从base64字符串中提取数据部分
        const binaryString = atob(base64Data) // 将base64字符串转换为二进制数据
        const len = binaryString.length
        const bytes = new Uint8Array(len)
        for (let i = 0; i < len; i++) {
          bytes[i] = binaryString.charCodeAt(i)
        }
        const fileData = bytes.buffer
        // 3. 将图片存储到oss，并返回oss文件地址，供save方法保存数据使用
        const put_res = await this.$axios.put(presignedUrl, fileData, {
          headers: {
            'Content-Type': null,
          },
        })
        // console.log('put res:',put_res)
        if (put_res.status === 200) {
          return presignedUrl.split('?')[0] // 返回资源地址
        } else {
          throw new Error(`${put_res}`)
        }
      } catch (error) {
        if (error.response.status === 401) {
          this.$message.error('登录已过期，请重新登录')
          this.$router.push('/login')
          return
        }
        console.log('OSS错误:', error)
        throw error
      }
    },
  },
  watch: {
    coverCreateStatus(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.$forceUpdate()
      }
    },
    createvalue(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.$forceUpdate()
      }
    },
  },
}
</script>

<style>
.save-button:hover {
  background-color: #79bbff;
}

/* 新增模态框样式 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  max-width: 80%;
  max-height: 80%;
}

.modal-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
}

.container {
  min-height: 100vh;
  background-color: white;
  /* width: 100%; */
}

.form-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  padding-left: 15px;
  padding-right: 15px;
}

.form-group {
  margin-bottom: 2rem;
}

label {
  display: block;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
  /* margin-bottom: 0.5rem; */
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 0.5rem 1rem;
  border: 1px solid #e7e7e7;
  border-radius: 0.5rem;
  font-size: 1rem;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
}

.form-textarea {
  resize: none;
  min-height: 9rem;
}

.cover-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 1rem;
}

.cover-item {
  position: relative;
  aspect-ratio: 4/5;
  background-color: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  overflow: hidden;
}

.cover-item.selected {
  outline: 2px solid #3b82f6;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: fill;
}

.ai-tag {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background-color: #3b82f6;
  color: white;
  font-size: 0.75rem;
  /* padding: 0.25rem 0.5rem; */
  border-radius: 0.25rem;
}

.textarea-wrapper {
  position: relative;
}

.counter {
  position: absolute;
  bottom: 0.5rem;
  right: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.5rem;
  /* margin-bottom: 2rem; */
}

.button-group {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.cancel-button,
.save-button {
  padding: 0.5rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  white-space: nowrap;
}

.cancel-button {
  border: 1px solid #d1d5db;
  color: #374151;
  background-color: white;
}

.cancel-button:hover {
  background-color: #f9fafb;
}

.save-button {
  background-color: #409eff;
  color: white;
  border: none;
}

.save-button:hover {
  background-color: #79bbff;
}

/* 滚动条样式 */
textarea::-webkit-scrollbar {
  width: 6px;
}

textarea::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

textarea::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

textarea::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* 数字输入框样式 */
input[type='number']::-webkit-inner-spin-button,
input[type='number']::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
</style>
