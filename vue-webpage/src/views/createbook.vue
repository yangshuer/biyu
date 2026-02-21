<template>
    <div class="createbook-container">
        <el-container class="chat-panel">
            <el-header class="chat-header">
                <span style="font-weight: bolder;"> AI创作助手</span>
                <div class="chat-tools">
                    <el-tooltip content="清空对话记录" placement="top">
                        <img @click="clearchatmessages"
                            style="height: 20px; width: 20px; margin: 10px 0; cursor: pointer;"
                            src="../assets/clear.png" alt="清空记录">
                    </el-tooltip>
                </div>
            </el-header>
            <el-main class="chat-content">
                <div v-for="(msg, index) in chatShowMessages" :key="index"
                    :class="['chat-message', msg.role === 'user' ? 'user-message' : 'ai-message']">
                    <div v-if="msg.content === '' && msg.role !== 'user'" class="loading-indicator"
                        :class="[msg.role !== 'user' ? 'markdown-container' : '']">
                        <img src="../assets/chatload.gif" alt="加载中" style="width: 30px; height: 30px;margin: 0;">
                    </div>
                    <div :class="[msg.role !== 'user' ? 'markdown-container' : '']" v-if="msg.content !== ''"
                        v-html="parseMarkdown(msg.content)"></div>
                </div>
            </el-main>
            <el-footer class="chat-input">
                <el-input style="width: 80%; min-height: 100%;" v-model="inputMessage" minlength="50px" autosize
                    type="textarea" resize="none" placeholder="请输入…(Shift+Enter换行)" clearable
                    @keydown.enter="handleEnterKey"></el-input>
                <el-button style="margin-left: 5px; width: calc(20% - 5px); height: 100%" type="primary"
                    @click="sendMessage">发送</el-button>
            </el-footer>
        </el-container>
        <div class="tab-content">
            <div style="display: flex;">
                <el-tabs v-model="activeName" class="tabs" @tab-click="handleClick">
                    <el-tab-pane label="作品信息" name="info"></el-tab-pane>
                    <el-tab-pane label="角色关系" name="character"></el-tab-pane>
                    <el-tab-pane label="场景设计" name="scene"></el-tab-pane>
                    <el-tab-pane label="作品创作" name="newcreate"></el-tab-pane>
                </el-tabs>
                <div class="tolist" @click="tobooklist">回到作品列表</div>
            </div>
            <el-main class="tab-main">
                <RouterView />
            </el-main>
        </div>
    </div>
</template>

<script>
import { marked } from 'marked';
import { fetchEventSource } from '@microsoft/fetch-event-source';
export default {
    data() {
        return {
            chatShowMessages: [{ role: 'assistant', content: '你好，😊我是您的AI创作助手！来试试和我对话吧～' }],
            chatMessages: [],
            inputMessage: '',
            isLoading: false // 新增加载状态
        }
    },
    setup() {
        return {
            activeName: 'info'
        }
    },
    methods: {
        clearchatmessages() {
            this.chatShowMessages = [{ role: 'assistant', content: '你好，😊我是您的AI创作助手！来试试和我对话吧～' }]
            this.chatMessages = []
        },
        parseMarkdown(content) {
            return marked.parse(content);
        },
        handleEnterKey(e) {
            if (e.shiftKey) {
                // 允许Shift+回车换行
                return;
            } else {
                // 普通回车发送消息
                e.preventDefault();
                this.sendMessage();
            }
        },
        async sendMessage() {
            if (!this.inputMessage.trim()) {
                this.$message.warning('请输入内容');
                return
            }
            if (this.isLoading) {
                this.$message.warning('AI回答中～');
                return;
            } // 防连点

            const userMessage = {
                role: 'user',
                content: this.inputMessage
            };

            this.chatShowMessages.push(userMessage);
            this.$nextTick(() => {
                this.scrollToBottom();
            });
            this.chatMessages.push(userMessage);
            this.inputMessage = '';

            this.isLoading = true;
            const aiMessage = { role: 'assistant', content: '' };
            this.chatShowMessages.push(aiMessage);
            const lastIndex = this.chatShowMessages.length - 1;

            let controller = new AbortController(); // 添加AbortController
            try {
                await fetchEventSource('/agents/aichat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'text/event-stream', // 明确指定接受SSE
                        'X-Auth-Token': localStorage.getItem('token') //token
                    },
                    body: JSON.stringify({
                        messages: [...this.chatMessages.slice(-20)], //最近的10轮对话
                        book_id:localStorage.getItem('currentBookId')
                    }),
                    signal: controller.signal, // 添加中止信号
                    timeout: 60000,  // 60秒超时
                    retry: false,  // 关闭报错重试
                    openWhenHidden: true, // 防止挂起重试！！！！避免重复请求后端
                    onopen: (e) => {
                        if (e.status !== 200) {
                            // 接口异常代码
                            console.log(e.status)
                            controller.abort();
                            if (e.status === 401) {
                                this.$message.error('登录已过期，请重新登录');
                                this.$router.push('/login');  // 可选的跳转登录页
                            }else{
                                this.$message.error('服务器错误，请稍后再试');
                            }
                            // 回滚消息
                            this.chatShowMessages.splice(-2);
                            this.chatMessages.splice(-2);
                        }
                    },
                    onmessage: (event) => {
                        try {
                            const data = JSON.parse(event.data);
                            if (data.content === "[DONE]") {
                                controller.abort();
                                return;
                            }
                            if (data.error) {
                                controller.abort();
                                throw new Error(data.error);
                            }
                            // 检查消息数组是否存在该索引
                            if (this.chatShowMessages[lastIndex]) {
                                this.chatShowMessages[lastIndex].content += (data.context !== "[DONE]" && data.context !== null ? data.context : "");
                            }
                            this.$forceUpdate()
                            this.$nextTick(() => {
                                this.scrollToBottom();
                            });
                        } catch (e) {
                            console.log('SSE parse error:', e);
                            controller.abort();
                        }
                    },
                    onerror: (err) => {
                        controller.abort(); // 出错时中止连接
                        throw new Error('模型服务异常，请稍后重试～');
                    },
                    onclose: () => {
                        controller.abort(); // 连接关闭时中止
                    }
                });
                this.chatMessages.push(aiMessage);
                this.chatMessages[lastIndex - 1].content = this.chatShowMessages[lastIndex].content
            } catch (error) {
                this.$message.error('请求失败: ' + error.message);
                // 回滚消息
                this.chatShowMessages.splice(-2);
                this.chatMessages.splice(-2);
            } finally {
                this.isLoading = false;
                controller.abort(); // 确保最终中止
                console.log(this.chatMessages)
                console.log(this.chatShowMessages)
            }
        },
        scrollToBottom() {
            const container = this.$el.querySelector('.chat-content');
            container.scrollTop = container.scrollHeight;
        },
        tobooklist() {
            this.$router.push('/workbench')
        },
        handleClick() {
            switch (this.activeName) {
                case 'info':
                    this.$router.push('/workbench/createbook/bookinfoform');
                    break;
                case 'character':
                    this.$router.push('/workbench/createbook/characterlist');
                    break;
                case 'scene':
                    this.$router.push('/workbench/createbook/scenelist');
                    break;
                case 'newcreate':
                    this.$router.push('/workbench/createbook/newcreationcharacter');
                    break;
                // 其他tab页面的路由...
                default:
                    this.$router.push('/workbench/createbook/zero');
                    break;
            }
        }
    },
    mounted() {
        const actiontab = this.$route.query.actiontab
        if (actiontab) {
            this.activeName = actiontab
        }
        this.handleClick()
    }
}
</script>

<style scoped>
:deep(.el-textarea__inner) {
    border: 1px rgb(217, 217, 217) solid;
    resize: none;
    box-shadow: none;
    padding: 10px 15px;
    min-height: 100px;
    max-height: 150px;
    overflow-y: auto;
    font-size: 14px;
    line-height: 1.5;
    color: var(--el-text-color-regular);
}

:deep(.el-textarea__inner):focus {
    outline: none;
    border: none;
    box-shadow: 0 0 0 2px var(--el-color-primary-light-5);
}

.loading-indicator {
    height: 62px;
}

.markdown-container {
    max-width: 100%;
    margin: 0 auto;
    padding: 1rem;
    border: 0.5px solid rgb(217, 217, 217);
    border-radius: 8px;
    overflow-x: auto;
}

.createbook-container {
    width: 100%;
    height: 100%;
    /* border: 1px red solid; */
    display: flex;
}

/* 左侧对话窗口样式 */
.chat-panel {
    width: 20%;
    height: 100%;
    border-right: 1px solid var(--el-border-color);
    background-color: var(--el-bg-color);
}

.chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0;
    margin-right: 15px;
    border-bottom: 1px solid var(--el-border-color);
    height: 40px;
}

.chat-tools {
    display: flex;
    gap: 5px;
}

.chat-content {
    /* padding: 15px; */
    padding-top: 15px;
    padding-right: 15px;
    padding-bottom: 15px;
    padding-left: 0;
    height: auto;
    overflow-y: auto;
    height: calc(100% - 120px - var(--additional-height, 0px));
    /* 添加默认值 */
}

.chat-message {
    margin-bottom: 15px;
    padding: 10px 15px;
    border-radius: 8px;
    max-width: 95%;
    word-break: break-word;
}

.user-message {
    background-color: var(--el-color-primary-light-9);
    /* color: var(--el-color-primary); */
    margin-left: auto;
    max-width: 90%;
}

.ai-message {
    padding-left: 0;
    /* background-color: white; */
    /* color: #409EFF; */
    color: #000;
    margin-right: auto;
    /* border: 1px #79BBFF solid; */
}

.chat-input {
    height: auto;
    min-height: 50px;
    padding-top: 10px;
    padding-left: 0;
    padding-right: 0;
    margin-right: 15px;
    border-top: 1px solid var(--el-border-color);
}

.tab-content {
    width: 80%;
    /* border: blue 1px solid; */
}

.tabs {
    padding-left: 15px;
    width: calc(100% - 90px)
}

.tolist {
    height: 40px;
    width: 90px;

    /* text-decoration: underline; */
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 2px solid #E4E7ED;

    &:hover {
        color: #409EFF;
        font-weight: bolder;
    }
}

.tab-main {
    height: calc(100% - 54px);
    padding: 0;
    margin: 10px 0;
    padding-bottom: 10px;
    /* border: blue 1px solid; */
    /* margin-left: 15px; */
}
</style>