<template>
    <div class="charater">
        <div class="list">
            <!-- 章节列表 -->
            <div class="up-button">
                <el-tooltip class="box-item" effect="dark" content="上一页" placement="top">
                    <el-button  @click="to_on_page"  style="margin: 4px;" type="primary" plain circle>
                        < </el-button>
                </el-tooltip>
            </div>
            <div class="l">
                <div class="c">
                    <el-scrollbar ref="chapterScrollbar">
                        <div style="display: flex; height: 40px;">
                            <el-badge v-if="character_list.length !== 0" v-for="(value, index) in character_list"
                                :value="getStatusText(value.status)" class="item" :offset="[-10, 10]"
                                :type="getStatusType(value.status)">
                                <el-tooltip class="box-item" effect="dark" :content="value.title" placement="top">
                                    <el-button :key="index" :class="{ 'highlight': highlightedButton === index }"
                                        @click="highlightButton(index)">第{{ value.chapter_number }}章-{{ truncateLabel(value.title,4)
                                        }}</el-button>
                                </el-tooltip>
                            </el-badge>
                            <el-badge v-if="character_list.length === 0" :value="'注意⚠️'" class="item" :offset="[-10, 10]">
                                <el-button>您还没有创建章节～</el-button>
                            </el-badge>
                        </div>
                    </el-scrollbar>
                </div>
            </div>
            <div class="down-button">
                <el-tooltip class="box-item" effect="dark" content="下一页" placement="top">
                    <el-button @click="to_down_page" style="margin: 4px;" type="primary" plain circle>></el-button>
                </el-tooltip>
            </div>
        </div>
        <div class="buttons">
            <!-- 操作按钮 -->
            <el-button @click="new_chapter" style="margin: 4px 0px; width: calc((100% / 2) * 0.98);" type="primary">新建章节</el-button>
            <el-button @click="creation_chapter" style="margin: 4px 0 0 4px; width: calc((100% / 2) * 0.98);" type="success">创作章节</el-button>
        </div>
    </div>
    <div class="worker">
        <div class="on-charater">
            <!-- 上一章内容 -->
            <div
                style="height: 30px; width: 100%; border-bottom: #e6e5e5 1px solid; display: flex; align-items: center; padding-left: 5px; position: relative;">
                <el-tooltip class="box-item" effect="dark" :content="up_character_info.title" placement="bottom">
                    <span v-if="up_character_info.title" style="font-weight: 600;margin-left: 2px;">上一章：《{{
                        truncateLabel(`第${up_character_info.chapter_number}章-${up_character_info.title}`, 16) }}》</span>
                    <span v-if="!up_character_info.title" style="font-weight: 600;margin-left: 2px;">上一章：《无》</span>
                </el-tooltip>
                <el-text :type="getStatusType(2)" style="position: absolute; right: 5px; font-weight: 600;">{{
                    getStatusText(up_character_info.status) }}</el-text>
            </div>
            <div style="padding:0 5px; height: calc(100% - 30px);">
                <!-- 内容回显区 -->
                <el-card style="height: 12%;">
                    <template #header><span style="font-weight: 600;">章节概述</span></template>
                    <div style="overflow-y: auto;">
                        <!-- <span></span> -->
                        <el-text style="white-space: pre-line;font-size: 15px;">
                            {{ up_character_info.overview }}
                        </el-text>
                    </div>
                </el-card>
                <el-card style="height: 20%;">
                    <template #header><span style="font-weight: 600;">情节设计</span></template>
                    <div style="overflow-y: auto;">
                        <el-text style="white-space: pre-line;font-size: 15px;">
                            {{ up_character_info.ai_plots_text ? up_character_info.ai_plots_text : up_character_info.plots_text }}
                        </el-text>
                    </div>
                </el-card>
                <el-card style="height: calc(68% - 15px);">
                    <template #header><span style="font-weight: 600;">章节内容</span></template>
                    <div style="overflow-y: auto;">
                        <el-text style="white-space: pre-line;font-size: 15px;">
                            {{ up_character_info.human_creation != "" ?  up_character_info.human_creation : up_character_info.ai_creation}}
                        </el-text>
                    </div>
                </el-card>
            </div>
        </div>
        <div class="self-charater">
            <!-- 本章内容 -->
            <div
                style="height: 30px; width: 100%;background-color: rgb(220,240,255); border-bottom: #e6e5e5 1px solid; display: flex; align-items: center; padding-left: 5px; position: relative;">
                <span v-if="work_character_info.title!=''" style="font-weight: 600;margin-left: 2px;">本章：《{{
                    truncateLabel(`第${work_character_info.chapter_number}章-${work_character_info.title}`,
                        30)
                }}》</span>
                <span v-if="work_character_info.title=='' && this.new_chapter_status && this.highlightedButton == -1" style="font-weight: 600;margin-left: 2px;">本章：《{{
                    truncateLabel(`第${work_character_info.chapter_number}章-${(work_character_info.title != '' ? work_character_info.title :'未命名章节')}`,
                        30)
                }}》</span>
                <span v-if="work_character_info.title=='' && !this.new_chapter_status && this.highlightedButton == -1 && this.character_list.length !== 0" style="font-weight: 600;margin-left: 2px; color: orangered;">请选择要操作的章节</span>
                <span v-if="work_character_info.title=='' && !this.new_chapter_status && this.highlightedButton == -1 && this.character_list.length === 0" style="font-weight: 600;margin-left: 2px; color: orangered;">这本书还没有章节，请新建章节</span>
                <el-button-group style="position: absolute; right: 5px;">
                    <el-button @click="del_chapter" style="height: 20px; margin: 0 2px; border: none;" type="danger">删除</el-button>
                    <el-button @click="save_chapter(0)" style="height: 20px; margin: 0 2px; border: none;" type="primary">保存</el-button>
                    <el-button @click="save_chapter(1)" style="height: 20px; margin: 0 2px; border: none;" type="success">定稿</el-button>
                </el-button-group>

            </div>
            <div v-if="character_list.length === 0 && !new_chapter_status"  style="display: flex; height: calc(100% - 30px);">
                <div class="empty-state"
                    style="color: #909399; display: flex; justify-content: center; align-items: center; height: 90%;">
                    <img src="@/assets/empty-folder.png" alt="空列表" class="empty-image">
                    <p class="empty-text">您还没有创建章节～</p>
                </div>
            </div>
            <div v-if="character_list.length !== 0 || new_chapter_status"  style="display: flex; height: calc(100% - 30px);">
                <div class="outline">
                    <el-card style="height: calc(100% - 7px);">
                        <template #header><span style="font-weight: 600;">章节设计区</span></template>
                        <div style=" height: 100%;">
                            <div style="display: flex;">
                                <div
                                    style="font-size: smaller; width:70px; height: 31px; display: flex;  align-items: center; color: #a8abb2; font-weight: bold;">
                                    第{{ work_character_info.chapter_number }}章
                                </div>
                                <el-input v-model="work_character_info.title" placeholder="请输入章名" />
                            </div>
                            <el-card style="height: 15%; ">
                                <template #header><span style="font-weight: 600;">章节概述</span></template>
                                <MdEditor v-model="work_character_info.overview" :toolbars="[]" :preview="false"
                                    :footers="false" style="height: 100%; border: none;" placeholder="请输入章节概述" />
                            </el-card>
                            <el-card style="height: 35%; ">
                                <template #header><span style="font-weight: 600;">情节设计</span></template>
                                <MdEditor v-model="work_character_info.plots_text" :toolbars="[]" :preview="false"
                                    :footers="false" style="height: 100%; border: none;" placeholder="无情节" />
                            </el-card>
                            <el-card style="height: calc(50% - 43px); position: relative;">
                                <template #header><span style="font-weight: 600;">情节完善</span></template>
                                <el-button @click="generatePlot" color="#626aef" :dark="isDark" plain
                                    style="height: 20px;position: absolute; top: 0; right: 0; margin-top: 3px; margin-right: 3px;">1.AI情节完善</el-button>
                                <MdEditor v-model="work_character_info.ai_plots_text" :toolbars="[]" :preview="false"
                                    :footers="false" style="height: 100%; border: none;" placeholder="未进行情节完善" />
                            </el-card>
                        </div>
                    </el-card>
                </div>
                <div class="creation">
                    <el-card style="height: calc(100% - 7px); position: relative;">
                        <template #header><span style="font-weight: 600;">章节创作区</span></template>
                        <el-button
                            @click="generateChapter"
                            style="height: 20px; position: absolute; top: 0; right: 0; margin-top: 3px; margin-right: 3px;"
                            type="success" plain>2.AI预创作</el-button>
                        <div style="height:100%;">
                            <div style="height:calc(100% - 26px); width: 100%; overflow-y: auto;">
                                <MdEditor v-model="work_character_info.human_creation" :toolbars="[]" :preview="false"
                                    :footers="false" style="height: 100%; border: none;" placeholder="无内容" />
                            </div>
                            <div
                                style="height: 20px; width: 100%; border-top: #e6e5e5 1px solid; position: absolute; bottom: 0;    margin-bottom: 6px;">
                                <span style="font-weight: 600;font-size: 12px; color: orange;">字数:{{
                                    countstrnum(work_character_info.human_creation) }}</span>
                            </div>
                        </div>
                    </el-card>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import {
    Check,
    Delete,
    Edit,
    Message,
    Search,
    Star,
} from '@element-plus/icons-vue'
import { MdEditor } from 'md-editor-v3';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { genFileId } from 'element-plus';
export default {
    components: {
        MdEditor
    },
    data() {
        return {
            character_list: [], // 章节列表'
            new_chapter_status: false, //创作状态
            highlightedButton: -1, // 当前高亮的按钮list索引，工作章节的索引
            // up_character_info:null, // 上一章的全部信息
            up_character_info: {
                "id": null,
                "title": "",
                "chapter_number": null,
                "overview": "",
                "status": null,
                "plots_text": "",
                "ai_plots_text": "",
                "ai_creation": "",
                "human_creation": "",
                "book_id":null
            },
            // work_character_info:null, // 当前编辑章节的信息
            work_character_info: {
                "id": null,
                "title": "",
                "chapter_number": null,
                "overview": "",
                "status": null,
                "plots_text": "",
                "ai_plots_text": "",
                "ai_creation": "",
                "human_creation": "",
                "book_id":null
            },
            current_page: null,
            total_pages: null,
            all_character_num: 0
        }
    },
    methods: {
        async generateChapter() { 
            // 生成章节'
            if(this.work_character_info.ai_plots_text === ''){
                this.$message.error('请进行AI情节完善')
                return;
            }
            // 请求接口
            this.work_character_info.human_creation = '' // 清空AI创作内容
            // 添加loading效果
            const loadingInstance = this.$loading({
                lock: true,
                text: 'AI创作中...',
                background: 'rgba(0, 0, 0, 0.7)',
            });

            const bookId = localStorage.getItem('currentBookId');
            if (!bookId) {
                this.$message.error('请先保存作品信息');
                loadingInstance.close();
                return;
            }

            // 获取AI章节创作内容
            let controller = new AbortController();
            let aiContent = '';
            try{
                await fetchEventSource('/agents/create-chapter', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream',
                    'X-Auth-Token': localStorage.getItem('token')
                },
                body: JSON.stringify({
                    id: this.work_character_info.id,
                    chapter_number: this.work_character_info.chapter_number,
                    book_id: localStorage.getItem('currentBookId'),
                    title: this.work_character_info.title,
                    overview: this.work_character_info.overview,
                    ai_plots_text: this.work_character_info.ai_plots_text
                }),
                signal: controller.signal,
                timeout: 120000,
                retry: false,
                openWhenHidden: true,
                onopen: (e) => {
                    if (e.status !== 200) {
                        controller.abort();
                        if (e.status === 401) {
                            this.$message.error('登录已过期，请重新登录');
                            this.$router.push('/login');
                        }
                        loadingInstance.close();
                    }
                },
                onmessage: (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        // 检查是否有错误信息
                        if (data.mse || data.error) {
                            controller.abort();
                            const errorMsg = data.mse || data.error || '模型服务异常';
                            this.$message.error(errorMsg);
                            return;
                        }
                        // 检查完成标志
                        if (data.content === "[DONE]" || data.context === "[DONE]") {
                            controller.abort();
                            return;
                        }
                        // 处理正常内容，确保context存在且不为null
                        if (data.context !== undefined && data.context !== null && data.context !== "[DONE]") {
                            aiContent += data.context;
                            this.work_character_info.human_creation = aiContent;
                            this.$forceUpdate();
                        }
                    } catch (e) {
                        console.log('SSE parse error:', e);
                        controller.abort();
                        this.$message.error('数据解析失败');
                    }
                },
                onerror: (err) => {
                    controller.abort();
                    throw new Error('模型服务异常，请稍后重试～');
                },
                onclose: () => {
                    controller.abort();
                }
                });
            }catch(error){
                this.$message.error('获取AI章节创作内容失败');
                loadingInstance.close();
                return;
            }finally{
                loadingInstance.close();
            }
        },
        deepCopy(obj) {
            return JSON.parse(JSON.stringify(obj));
        },
        async generatePlot(){
            if(this.work_character_info.title === '' || this.work_character_info.plots_text === '' || this.work_character_info.overview === ''){
                this.$message.error('请填写必要的章节信息:章节名称|章节概述|情节设计')
                return;
            }
            this.work_character_info.ai_plots_text = '' // 清空
            // 添加loading效果
            const loadingInstance = this.$loading({
                lock: true,
                text: '情节设计中...',
                background: 'rgba(0, 0, 0, 0.7)',
            });
            if (this.work_character_info.plots_text === '') {
                this.$message.warning('请先输入情节设计内容');
                loadingInstance.close();
                return;
            }
            const bookId = localStorage.getItem('currentBookId');
            if (!bookId) {
                this.$message.error('请先保存作品信息');
                loadingInstance.close();
                return;
            }

            // 获取AI情节设计内容
            let controller = new AbortController();
            let aiContent = '';
            try{
                await fetchEventSource('/agents/create-plot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream',
                    'X-Auth-Token': localStorage.getItem('token')
                },
                body: JSON.stringify({
                    bookid: localStorage.getItem('currentBookId'),
                    chapterid: this.work_character_info.id,
                    plotinfo: this.work_character_info.plots_text
                }),
                signal: controller.signal,
                timeout: 60000,
                retry: false,
                openWhenHidden: true,
                onopen: (e) => {
                    if (e.status !== 200) {
                    controller.abort();
                    if (e.status === 401) {
                        this.$message.error('登录已过期，请重新登录');
                        this.$router.push('/login');
                    }
                    }
                },
                onmessage: (event) => {
                    try {
                    const data = JSON.parse(event.data);
                    // 检查是否有错误信息
                    if (data.mse || data.error) {
                        controller.abort();
                        const errorMsg = data.mse || data.error || '模型服务异常';
                        this.$message.error(errorMsg);
                        return;
                    }
                    // 检查完成标志
                    if (data.content === "[DONE]" || data.context === "[DONE]") {
                        controller.abort();
                        return;
                    }
                    // 处理正常内容，确保context存在且不为null
                    if (data.context !== undefined && data.context !== null && data.context !== "[DONE]") {
                        aiContent += data.context;
                        this.work_character_info.ai_plots_text = aiContent;
                        this.$forceUpdate();
                    }
                    } catch (e) {
                    console.log('SSE parse error:', e);
                    controller.abort();
                    this.$message.error('数据解析失败');
                    }
                },
                onerror: (err) => {
                    controller.abort();
                    throw new Error('模型服务异常，请稍后重试～');
                },
                onclose: () => {
                    controller.abort();
                }
                });
            }catch(error){
                this.$message.error('获取AI情节设计内容失败');
                loadingInstance.close();
                return;
            }finally{
                loadingInstance.close();
            }
        },
        // 滚动到最右侧的方法
        scrollToRight() {
            this.$nextTick(() => {
                if (this.$refs.chapterScrollbar) {
                    const scrollbarWrap = this.$refs.chapterScrollbar.wrapRef;
                    if (scrollbarWrap) {
                        scrollbarWrap.scrollLeft = scrollbarWrap.scrollWidth;
                    }
                }
            });
        },
        async save_chapter(mode){
            const old_list_length = this.all_character_num; // 获取当前的章节数量
            const old_highlightedButton = this.highlightedButton //获取当前章节选中状态
            const old_current_page = this.current_page
            if(this.work_character_info.title === '' || this.work_character_info.overview === ''){
                this.$message.error('请填写必要的章节信息:章节名称|章节概述|情节设计')
                return;
            }
            // 保存章节处理方法
            this.work_character_info.book_id = localStorage.getItem('currentBookId')
            if (mode === 0){
                if (this.work_character_info.human_creation === ''){
                    this.work_character_info.status = 0
                }else{
                    this.work_character_info.status = 1
                }
            }else if (mode === 1){
                if (this.countstrnum(this.work_character_info.human_creation)>=2000){
                    this.work_character_info.status = 2
                }else{
                    this.$message.error('定稿章节字数必须2000字')
                    return
                }
            }
            try {
                const res = await this.$axios.post('/manages/savechapters', {
                    chaptersinfo: this.work_character_info
                }, {
                    headers: {
                    'X-Auth-Token': localStorage.getItem('token')
                    }
                });
                if (res.data.message) {
                    this.work_character_info.id = res.data.id
                    console.log('章节保存成功', res)
                    this.$message.success('章节保存成功');
                    // 刷新章节列表和数据 -- 需要添加保持操作章节选中的逻辑
                    await this.getvolumeschapters();
                    if (this.character_list.length !== 0){
                        if (old_list_length !== this.all_character_num){
                            console.log('新增',old_list_length,this.character_list.length,this.all_character_num)
                            this.work_character_info = this.character_list[this.character_list.length -1 ]
                            this.highlightedButton = this.character_list.length -1
                            this.getupcharacterinfo()
                        }else{
                            await this.getvolumeschapters(old_current_page)
                            console.log('保存',old_list_length,this.character_list,this.all_character_num)
                            this.work_character_info = this.character_list[old_highlightedButton]
                            this.getupcharacterinfo()
                        }
                    }
                    // 重置新建章节状态
                    this.new_chapter_status = false;
                    // 滚动到最右侧
                    this.scrollToRight();
                }
                }
                catch (error) {
                if (error.response && error.response.status === 401) {
                    this.$message.error('登录已过期，请重新登录');
                    this.$router.push('/login');
                    loadingInstance.close();
                } else {
                    console.error('请求失败:', error);
                    this.$message.error(error.response?.data?.error || '请求失败');
                    loadingInstance.close();
                }
            }
        },
        async del_chapter(){
            // 删除章节处理方法
            await this.$confirm('确定要删除该章节吗？删除后将无法恢复', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
            if (this.work_character_info.id == null){
                this.$message.error('不能删除未保存的章节')
            }else{
                // 删除章节
                const res = await this.$axios.delete('/manages/chapters', {
                    data: {
                        chapter_id: this.work_character_info.id,
                        book_id: localStorage.getItem('currentBookId')
                    },
                     headers: {
                        'X-Auth-Token': localStorage.getItem('token')
                    }
                },);
                if (res.status == 200) {
                    this.$message.success('删除成功');
                    // 刷新章节列表和数据
                    await this.getvolumeschapters();
                    if (this.character_list.length !== 0){
                        this.work_character_info = this.character_list[this.character_list.length -1 ]
                        this.highlightedButton = this.character_list.length -1
                        this.getupcharacterinfo()
                    }else{
                        this.work_character_info = {
                            "id": null,
                            "title": "",
                            "chapter_number": null,
                            "overview": "",
                            "status": null,
                            "plots_text": "",
                            "ai_plots_text": "",
                            "ai_creation": "",
                            "human_creation": "",
                            "book_id":null
                        }
                    }
                    // 重置新建章节状态
                    this.new_chapter_status = false;
                    this.scrollToRight();
                }else{
                    console.log('删除失败', res)
                    this.$message.error('删除失败');
                }
            }
        },
        async creation_chapter(){
            // 创作章节处理方法，默认选中最后一个已完成章节之后的章节
            //loading
            const loadingInstance = this.$loading({
                lock: true,
                text: '加载中...',
                background: 'rgba(0, 0, 0, 0.7)',
            })
            try {
                const res = await this.$axios.get('/manages/get-end-human-creation', {
                params: {
                    bookid: localStorage.getItem('currentBookId'),
                },
                headers: {
                    'X-Auth-Token': localStorage.getItem('token')
                }
                });
                if (res.data.volumeschaptersinfo) {
                    if (res.data.volumeschaptersinfo.length == 0) {
                        this.$message.error('当前书籍没有可创作章节');
                        return;
                    }
                    this.character_list = res.data.volumeschaptersinfo[0].children;
                    this.current_page = res.data.volumeschaptersinfo[0].current_page;
                    this.total_pages = res.data.volumeschaptersinfo[0].total_pages;
                    // 选中要创作的章节
                    const firstNonCompletedIndex = this.findFirstNonCompletedChapter();
                    if (firstNonCompletedIndex !== -1) {
                        this.highlightedButton = firstNonCompletedIndex;
                        // 更新工作区数据 - 使用深拷贝避免修改原始数据
                        this.work_character_info = this.deepCopy(this.character_list[firstNonCompletedIndex]);
                        // 获取上一章数据
                        this.getupcharacterinfo();
                    } else {
                        // 如果没有找到非完成状态的章节，保持当前选择逻辑
                        this.highlightedButton = this.character_list.length - 1;
                        this.work_character_info = this.deepCopy(this.character_list[this.character_list.length - 1]);
                        this.getupcharacterinfo();
                    }
                    // 滚动到最右侧
                    this.scrollToRight();
                }
            } catch (error) {
                if (error.response && error.response.status === 401) {
                this.$message.error('登录已过期，请重新登录');
                this.$router.push('/login');
                } else {
                console.error('获取卷章结构失败:', error);
                this.$message.error(error.response?.data?.error || '获取卷章结构失败');
                }
            } finally {
                loadingInstance.close()
            }
        },
        findFirstNonCompletedChapter() {
            // 过滤出第一个status不是2的元素index
            if (!this.character_list || this.character_list.length === 0) {
                return -1;
            }
            
            for (let i = 0; i < this.character_list.length; i++) {
                if (this.character_list[i].status !== 2) {
                    return i; // 返回第一个状态不是2的章节的索引
                }
            }
            return -1; // 如果没有找到，返回-1
        },
        async new_chapter(){
            //新建章节处理方法
            this.new_chapter_status = true
            this.highlightedButton = -1
            await this.getvolumeschapters();
            if (this.character_list.length !== 0){
                this.work_character_info = {
                    "id": null,
                    "title": "",
                    "chapter_number": this.character_list[this.character_list.length-1].chapter_number + 1,
                    "overview": "",
                    "status": null,
                    "plots_text": "",
                    "ai_plots_text": "",
                    "ai_creation": "",
                    "human_creation": "",
                    "book_id":null
                }
                this.up_character_info = this.deepCopy(this.character_list[this.character_list.length-1]);
            }else{
                this.work_character_info = {
                    "id": null,
                    "title": "",
                    "chapter_number": 1,
                    "overview": "",
                    "status": null,
                    "plots_text": "",
                    "ai_plots_text": "",
                    "ai_creation": "",
                    "human_creation": "",
                    "book_id":null
                }
            }
        },
        async to_on_page(){
            this.current_page = this.current_page - 1;
            if (this.current_page < 1){
                this.current_page = 1
            }else{
                await this.getvolumeschapters(this.current_page);
            }
            this.highlightedButton = -1
            this.new_chapter_status = false
            this.work_character_info = {
                "id": null,
                "title": "",
                "chapter_number": null,
                "overview": "",
                "status": null,
                "plots_text": "",
                "ai_plots_text": "",
                "ai_creation": "",
                "human_creation": "",
                "book_id":null
            }
            this.up_character_info={
                                "id": null,
                "title": "",
                "chapter_number": null,
                "overview": "",
                "status": null,
                "plots_text": "",
                "ai_plots_text": "",
                "ai_creation": "",
                "human_creation": "",
                "book_id":null
            }
        },
        async to_down_page(){
            this.current_page = this.current_page + 1;
            if (this.current_page > this.total_pages){
                this.current_page = this.total_pages
            }else{
                await this.getvolumeschapters(this.current_page);
            }
            this.highlightedButton = -1
            this.new_chapter_status = false
            this.work_character_info = {
                "id": null,
                "title": "",
                "chapter_number": null,
                "overview": "",
                "status": null,
                "plots_text": "",
                "ai_plots_text": "",
                "ai_creation": "",
                "human_creation": "",
                "book_id":null
            }
            this.up_character_info={
                                "id": null,
                "title": "",
                "chapter_number": null,
                "overview": "",
                "status": null,
                "plots_text": "",
                "ai_plots_text": "",
                "ai_creation": "",
                "human_creation": "",
                "book_id":null
            }
        },
        countstrnum(str) {
            // 过滤掉标点符号，只保留字母、数字和空格
            const filteredStr = str.replace(/[^\w\u4e00-\u9fa5\s]/g, '');
            // 返回过滤后字符串的长度
            return filteredStr.length;
        },
        truncateLabel(label, maxLength = 4) {
            return label.length > maxLength ? label.substring(0, maxLength - 1) + '...' : label;
        },
        async highlightButton(index) {
            this.highlightedButton = index;
            // 更新工作区数据 - 使用深拷贝避免修改原始数据
            this.work_character_info = this.deepCopy(this.character_list[index]);
            // 获取上一章数据
            console.log(this.work_character_info)
            this.getupcharacterinfo()
        },
        async getupcharacterinfo(){
            //loading
            const loadingInstance = this.$loading({
                lock: true,
                text: '加载中...',
                background: 'rgba(0, 0, 0, 0.7)',
            })
            console.log(this.work_character_info)
            if ((this.work_character_info.chapter_number - 1) < 1){
                this.up_character_info = {
                    "id": null,
                    "title": "",
                    "chapter_number": null,
                    "overview": "",
                    "status": null,
                    "plots_text": "",
                    "ai_plots_text": "",
                    "ai_creation": "",
                    "human_creation": "",
                    "book_id":null
                }
                loadingInstance.close()
                return;
            }
            try {
                const res = await this.$axios.get('/manages/get-chapter-info', {
                params: {
                    bookid: localStorage.getItem('currentBookId'),
                    chapternumber: this.work_character_info.chapter_number - 1
                },
                headers: {
                    'X-Auth-Token': localStorage.getItem('token')
                }
                });
                if (res.data) {
                    this.up_character_info = res.data;
                }
            } catch (error) {
                if (error.response && error.response.status === 401) {
                this.$message.error('登录已过期，请重新登录');
                this.$router.push('/login');
                } else {
                console.error('获取卷章结构失败:', error);
                this.$message.error(error.response?.data?.error || '获取卷章结构失败');
                }
            } finally {
                loadingInstance.close()
            }
        },
        getStatusText(status) {
            switch (status) {
                case 0: return '未创作';
                case 1: return 'AI创作';
                case 2: return '已完成';
                default: return '未知';
            }
        },
        getStatusType(status) {
            switch (status) {
                case 0: return 'info';
                case 1: return 'warning';
                case 2: return 'success';
                default: return 'info';
            }
        },
        async getvolumeschapters(page = null ) {
            //loading
            const loadingInstance = this.$loading({
                lock: true,
                text: '加载中...',
                background: 'rgba(0, 0, 0, 0.7)',
            })
            try {
                const res = await this.$axios.get('/manages/get-volumes-chapters', {
                params: {
                    bookid: localStorage.getItem('currentBookId'),
                    page:page
                },
                headers: {
                    'X-Auth-Token': localStorage.getItem('token')
                }
                });
                if (res.data.volumeschaptersinfo) {
                    if (res.data.volumeschaptersinfo.length > 0){
                        this.character_list = res.data.volumeschaptersinfo[0].children;
                        this.all_character_num = res.data.volumeschaptersinfo[0].total_chapters;
                        this.current_page = res.data.volumeschaptersinfo[0].current_page;
                        this.total_pages = res.data.volumeschaptersinfo[0].total_pages;
                    }else{
                        this.character_list = []
                    }
                }
            } catch (error) {
                if (error.response && error.response.status === 401) {
                this.$message.error('登录已过期，请重新登录');
                this.$router.push('/login');
                } else {
                console.error('获取卷章结构失败:', error);
                this.$message.error(error.response?.data?.error || '获取卷章结构失败');
                }
            } finally {
                loadingInstance.close()
                console.log(this.character_list)
            }
        },
    },
    watch:{
        highlightedButton(newVal) {
            if (newVal != -1) {
                this.new_chapter_status = false
                // 更新这个章节的数据 - 使用深拷贝避免修改原始数据
                this.work_character_info = this.deepCopy(this.character_list[newVal]);
            }
        },
        character_list: {
            handler() {
                // 当章节列表变化时，自动滚动到最右侧
                this.scrollToRight();
            },
            deep: true
        }
    },
    async mounted() { 
        await this.getvolumeschapters();
        if (this.character_list.length !== 0){
            this.work_character_info = this.deepCopy(this.character_list[this.character_list.length - 1]);
            this.highlightedButton = this.character_list.length -1
            this.getupcharacterinfo()
        }
        // 滚动到最右侧
        this.scrollToRight();
    }
}
</script>

<style lang="scss" scoped>
:deep(.el-timeline-item__tail) {
    border-left: none;
    border-top: 2px solid #e4e7ed;
    width: 100%;
    position: absolute;
    top: 5px;
}

:deep(.el-card__header) {
    padding: 1px;
}

:deep(.el-card.is-always-shadow, .el-card.is-hover-shadow:focus, .el-card.is-hover-shadow:hover) {
    box-shadow: none;
    margin-right: 4px;
    margin-top: 4px;
}

:deep(.cm-focused) {
    outline: none;
}

:deep(.el-card__body) {
    padding: 4px;
    height: calc(100% - 25px);
    overflow-y: auto;
}

:deep(.el-card.is-always-shadow) {
    margin-right: 0;
}

:deep(.el-timeline-item__wrapper) {
    padding-left: 0;
    position: absolute;
    top: 10px;
    transform: translateX(-50%);
    text-align: center;
}

:deep(.el-timeline-item__timestamp) {
    font-size: 10px;
}

.highlight {
    background-color: #409eff !important;
    /* 示例颜色 */
    color: white;
}

.item {
    margin: 4px 0;
    margin-right: 30px;
}

.timeline {
    display: flex;
    width: 100%;
    margin-bottom: 100px;

    .lineitem {
        width: 50%;
    }
}

.charater {
    height: 40px;
    // border: red 1px solid;
    margin-left: 15px;
    display: flex;
}

.list {
    // border: blue 1px solid;
    height: 100%;
    width: 85%;
    display: flex;
}

.buttons {
    display: flex;
    height: 100%;
    width: 15%;
}

.worker {
    height: calc(100% - 40px);
    margin-left: 15px;
    // border: green 1px solid;
    display: flex;
}

.on-charater {
    height: calc(100% - 5px);
    width: 30%;
    border: #e6e5e5 1px solid;
    margin-top: 5px;
    border-radius: 5px;
}

.self-charater {
    height: calc(100% - 5px);
    width: 70%;
    border: #e6e5e5 1px solid;
    margin-top: 5px;
    margin-left: 5px;
    border-radius: 5px;

}

.outline {
    height: 100%;
    width: 49%;
    padding-left: 4px;
}

.creation {
    height: 100%;
    width: 51%;
    padding-left: 4px;
}

.l {
    width: calc(100% - 80px);
    height: 40px;
    text-align: center;

    // border: red 1px solid;
    .c {
        // width:calc(100% - 80px);
        margin: 0 auto;
        // overflow-y: auto;
        height: 40px;
    }
}

.up-button {
    width: 40px;
    height: 40px;
}

.down-button {
    width: 40px;
    height: 40px;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  margin-left: calc((100% - 200px) / 2);
}

.empty-image {
  width: 200px;
  height: 200px;
  margin-bottom: 20px;
}

.empty-text {
  color: #999;
  font-size: 16px;
}
</style>