"""Current event facts only. No attachment paths, quote bodies or history."""
from dataclasses import dataclass
KINDS={'image','audio','video','file','forward','unknown'}
@dataclass(frozen=True)
class Input:
    text:str
    kind:str
    notice:str|None=None

def normalize(raw, fallback='', image=None):
    raw=raw if isinstance(raw,dict) else {}
    text=raw.get('qqbot_text',fallback)
    text=text.strip() if isinstance(text,str) else ''
    kinds=raw.get('qqbot_media_kinds',[])
    if not isinstance(kinds,list) or len(kinds)>6 or any(k not in KINDS for k in kinds):kinds=['unknown']
    if not kinds and raw.get('qqbot_media') and not image:kinds=['unknown']
    unsupported=[k for k in kinds if k!='image']
    if unsupported:
        names={'audio':'音频','video':'视频','file':'文件','forward':'转发','unknown':'媒体'}
        return Input(text,'unsupported','本条'+ '/'.join(names[k] for k in unsupported)+'暂不能读取，请贴出需要讨论的文字。')
    if 'image' in kinds and not image:return Input(text,'image_failed','本条图片暂时无法读取，请稍后重新发送。')
    if image:return Input(text,'image')
    if text:return Input(text,'text')
    return Input('','empty','我在，怎么啦？')
