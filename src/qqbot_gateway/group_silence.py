"""Local silence control. Gate owns RAM state; mirrors never restore it."""
import asyncio
import base64
import hashlib
import hmac
import json
import re
import secrets
import time
import unicodedata

DENIED = 'GROUP_MUTED_OR_STALE_OUTPUT'
FIELDS = {'v','boot_id','connection_id','bot','group','sender','message_id','generation','expires_ms','nonce'}

def group_ref(bot, group):
    return hashlib.sha256(('qqbot-silence-v1\0'+str(bot)+'\0'+str(group)).encode()).hexdigest()

def real_at(event, bot):
    return any(s.get('type')=='at' and str(s.get('data',{}).get('qq'))==bot for s in event['message'])

def silence_request(text, aliases, mentioned=False, limit=2000):
    if not isinstance(text,str) or len(text)>limit:return False
    text=unicodedata.normalize('NFKC',text).casefold()
    # Remove quoted material, code and quote lines, never fetch a reply body.
    text=re.sub(r'```[\s\S]*?(?:```|$)|`[^`]*(?:`|$)', '', text)
    text=re.sub(r'“[^”]*(?:”|$)|「[^」]*(?:」|$)|『[^』]*(?:』|$)|"[^"\n]*(?:"|$)|‘[^’]*(?:’|$)|\'[^\'\n]*(?:\'|$)', '',text)
    text='\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('>'))
    names=[]
    for name in sorted(aliases,key=len,reverse=True):
        name=unicodedata.normalize('NFKC',name).casefold()
        names.append((r'(?<![a-z0-9_])'+re.escape(name)+r'(?![a-z0-9_])') if name.isascii() else re.escape(name))
    target='(?:'+'|'.join(names)+')'
    modifier=r'(?:先|暂时|这会儿|现在|请|麻烦|能不能|可以|一下|你|就|还是|这段讨论|本次讨论|让|叫|帮忙|\s|[,，:：])*'
    negative=r'(?:别|不要|先别|先不要)'
    participate=r'(?:说话|说了|发言|插话|插嘴|接话|参与(?:这段)?讨论|参与|加入讨论|掺和)'
    quiet=r'(?:安静(?:一下|一会儿)?|闭嘴|暂停发言|停止发言)'
    for clause in re.split(r'[。!！;；\n]',text):
        if re.search(r'如果|假如|假设|有人说|他说|她说|转述|举例|例如|为什么|怎么|不是|并非|不用|无需|不必|别不|不要不|不让你|不礼貌|这句话|这句',clause):continue
        clause=clause.strip()
        if not clause:continue
        # Anchored direct address. @ supplies the object only for new direct text.
        prefix=rf'(?:{target}{modifier}|{modifier}{target}{modifier})'
        tail=r'(?:了|吧|啊|呀|呢|好吗|好么|可以吗|行吗|吗|么|一下|一会儿|\s|[,，?？])*'
        if re.fullmatch(prefix+rf'(?:{negative}{modifier}{participate}|{quiet})'+tail,clause):return True
        if re.fullmatch(modifier+negative+rf'(?:让|叫){modifier}{target}{modifier}{participate}'+tail,clause):return True
        if mentioned and re.fullmatch(modifier+rf'(?:{negative}{modifier}{participate}|{quiet})'+tail,clause):return True
    return False

def decode_ticket(ticket):
    if not isinstance(ticket,str) or len(ticket)>2048:raise ValueError(DENIED)
    body,signature=ticket.split('.')
    def decode(part):
        if not re.fullmatch(r'[A-Za-z0-9_-]+',part):raise ValueError(DENIED)
        value=base64.urlsafe_b64decode(part+'='*((-len(part))%4))
        if base64.urlsafe_b64encode(value).decode().rstrip('=')!=part:raise ValueError(DENIED)
        return value
    raw=decode(body);sig=decode(signature)
    def pairs(items):
        value={}
        for key,item in items:
            if key in value:raise ValueError(DENIED)
            value[key]=item
        return value
    data=json.loads(raw,object_pairs_hook=pairs)
    if not isinstance(data,dict) or set(data)!=FIELDS or type(data['v']) is not int or data['v']!=1:raise ValueError(DENIED)
    if any(not isinstance(data[k],str) or not re.fullmatch(r'[a-f0-9]{32,64}',data[k]) for k in ('boot_id','connection_id','nonce')):raise ValueError(DENIED)
    if len(data['nonce'])!=32:raise ValueError(DENIED)
    from .config import qq_id
    if any(qq_id(data[k])!=data[k] for k in ('bot','group','sender')):raise ValueError(DENIED)
    if not isinstance(data['message_id'],str) or not 1<=len(data['message_id'])<=128:raise ValueError(DENIED)
    if any(type(data[k]) is not int or data[k]<0 for k in ('generation','expires_ms')):raise ValueError(DENIED)
    if json.dumps(data,sort_keys=True,separators=(',',':')).encode()!=raw or len(sig)!=32:raise ValueError(DENIED)
    return data,body,sig


def resume_request(text, aliases, mentioned=False, limit=2000):
    if not isinstance(text,str) or len(text)>limit:return False
    text=unicodedata.normalize('NFKC',text).strip().casefold()
    # Full match only: quoted, conditional, negated and forwarded commands fail.
    names='|'.join(re.escape(unicodedata.normalize('NFKC',n).casefold()) for n in sorted(aliases,key=len,reverse=True))
    prefix=rf'(?:(?:{names})[\s,，:：]*(?:你)?)' if names else r'(?!)'
    if mentioned:prefix=rf'(?:{prefix})?'
    return bool(re.fullmatch(prefix+r'(?:请|现在|你|\s)*(?:恢复发言|可以说话了|继续说话)[。!！~～\s]*',text))

class GroupSilence:
    def __init__(self,bot,groups,blocked=(),enabled=True,ttl=810,clock=time.monotonic):
        self.bot=bot;self.groups=frozenset(groups);self.blocked=frozenset(blocked);self.enabled=enabled
        self.clock=clock;self.ttl=ttl;self.boot_id=secrets.token_hex(16);self.secret=secrets.token_bytes(32)
        self.states={g:dict(mode='normal',generation=0) for g in groups}
        self.locks={g:asyncio.Lock() for g in groups}

    def normal(self,group):return group in self.states and self.states[group]['mode']=='normal'

    def control(self,group,stop,mention):
        state=self.states[group];mode='muted' if stop else 'normal' if mention else state['mode']
        if mode!=state['mode']:state.update(mode=mode,generation=state['generation']+1);return True
        return False

    def mirror(self):
        return dict(v=1,boot_id=self.boot_id,enabled=self.enabled,
                    groups={group_ref(self.bot,g):dict(s) for g,s in self.states.items()})

    def issue(self,event,connection):
        group=str(event['group_id'])
        if not self.normal(group):raise ValueError(DENIED)
        data=dict(v=1,boot_id=self.boot_id,connection_id=connection,bot=self.bot,group=group,sender=str(event['user_id']),
                  message_id=str(event['message_id']),generation=self.states[group]['generation'],
                  expires_ms=int((self.clock()+self.ttl)*1000),nonce=secrets.token_hex(16))
        body=base64.urlsafe_b64encode(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).decode().rstrip('=')
        sig=base64.urlsafe_b64encode(hmac.digest(self.secret,body.encode(),'sha256')).decode().rstrip('=')
        return body+'.'+sig

    def verify(self,ticket,group,connection):
        try:
            d,body,sig=decode_ticket(ticket)
            if (not hmac.compare_digest(sig,hmac.digest(self.secret,body.encode(),'sha256')) or
                d['boot_id']!=self.boot_id or d['connection_id']!=connection or d['bot']!=self.bot or d['group']!=group or
                d['sender'] in self.blocked or d['sender']==self.bot or not self.normal(group) or
                d['generation']!=self.states[group]['generation'] or d['expires_ms']<int(self.clock()*1000)):raise ValueError()
            return d
        except (ValueError,TypeError,KeyError,UnicodeError):raise ValueError(DENIED) from None
