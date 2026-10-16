class GatewayError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


MESSAGES = {
    'SHUTTING_DOWN': '机器人正在关闭，请稍后再试。',
    'EMPTY_REPLY': '这次没有生成可显示的文字，请换个问法再试。',
    'INPUT_TOO_LONG': '这条文字和固定设定已超过当前输入预算，请缩短问题或由管理员调整预算。',
    'MODEL_CONFIG_UNSUPPORTED': '当前模型或推理强度不支持此配置，请管理员检查本机模型能力。',
    'BACKEND_UNAVAILABLE': '暂时接不上模型，稍后再试。',
    'AUTH_REQUIRED': '模型账号需要在本机重新登录，管理员处理后再试。',
    'QUOTA_EXHAUSTED': '当前模型额度不足，请管理员检查额度或明确调整模型配置。',
    'RATE_LIMITED': '模型服务暂时限流，稍后再试。',
    'QUEUE_FULL': '当前排队较多，稍后再试。',
    'QUEUE_TIMEOUT': '排队等待超时，请稍后重新提问。',
    'MODEL_TIMEOUT': '模型这次回答超时了，请稍后再试。',
    'PROTOCOL_ERROR': '模型没有返回有效的最终回答，请管理员查看本机诊断。',
    'TOOL_ISOLATION_FAILED': '模型工具隔离检查未通过，已停止本次请求。',
    'CLEANUP_FAILED': '模型进程清理未确认完成，已停止接收新请求。',
    'UNSUPPORTED_REQUEST': '当前接口只接受规定范围内的纯文本请求。',
}


def classify_error(value):
    text = str(value).lower()
    if any(x in text for x in ('quota', 'insufficient credit', 'credits exhausted', '余额不足', '额度不足', '配额耗尽')):
        return 'QUOTA_EXHAUSTED'
    if any(x in text for x in ('401', 'unauthorized', 'not logged in', 'authentication', 'login required', 'token expired', '未登录', '登录失效', '鉴权')):
        return 'AUTH_REQUIRED'
    if any(x in text for x in ('429', 'rate limit', 'too many requests', '限流')):
        return 'RATE_LIMITED'
    return 'BACKEND_UNAVAILABLE'
