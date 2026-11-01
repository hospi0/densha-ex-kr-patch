# -*- coding: utf-8 -*-
# 머리 조건 없이 CHR 압축 덩어리 찾기(2026-10-31): 풀었을 때 정확히 압축 크기만큼 읽어야 함 — python tools/chr_scan.py
# (GO_SEL @273C 노선 선택 배경이 그림 머리 [2,1] 이라 v2img 검사에서 빠졌던 것을 이걸로 찾음)
import sys,struct,glob,os; sys.path.insert(0,'tools')
def try_dec(d,i):
    t=d[i]; size,cs=struct.unpack_from('<II',d,i+2)
    k=t+2; mask=(1<<k)-1; N=1<<(16-k); r=N-(mask+3); ring=bytearray(N); out=bytearray(); j=i+10; end=i+10+cs
    while len(out)<size:
        if j>=end: return None
        fl=d[j]; j+=1
        for b in range(8):
            if len(out)>=size: break
            if fl>>b&1:
                if j>=end: return None
                c=d[j]; j+=1; out.append(c); ring[r]=c; r=(r+1)%N
            else:
                if j+1>=end: return None
                b0,b1=d[j],d[j+1]; j+=2; p=b0|(b1>>k)<<8
                for q in range((b1&mask)+3):
                    c=ring[(p+q)%N]; out.append(c); ring[r]=c; r=(r+1)%N
    return bytes(out) if j==end else None
for p in sorted(glob.glob('work/disc0/*.BIN')):
    d=open(p,'rb').read(); res=[]
    for i in range(len(d)-10):
        if d[i]<6 and d[i+1]==0:
            u,c=struct.unpack_from('<II',d,i+2)
            if 32<c<=len(d)-i-10 and c<u<=c*40 and u<0x80000:
                o=try_dec(d,i)
                if o: res.append((hex(i),d[i],u,c,o[:8].hex()))
    if res: print(os.path.basename(p),res)
