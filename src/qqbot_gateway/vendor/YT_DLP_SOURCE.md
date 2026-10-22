# yt-dlp最小字幕字段适配

源：https://github.com/yt-dlp/yt-dlp/blob/897341241f2bfb2439fe0367f4c7c9ccd29a3828/yt_dlp/extractor/bilibili.py

固定提交：897341241f2bfb2439fe0367f4c7c9ccd29a3828。2026-10-22取得源码113650字节，SHA256 b99ad995a016b11097cdadfb64bc6da55cd64129b76e7914eafbc7e45685ec33；LICENSE 1211字节，SHA256 7e12e5df4bae12cb21581ba157ced20e1986a0508dd10d0e8a4ab9a4cf94e85c。许可原文见[Unlicense](yt_dlp_UNLICENSE)。

仅适配BilibiliBaseIE._get_subtitles的固定player端点、need_login_subtitle、subtitle.subtitles、lan/subtitle_url字段。修改：独立纯函数，不依赖traverse_obj；外层严格类型/用途校验，先选单轨再读取，JSON原时间保留。删除全部弹幕、SRT、下载循环、extract_info、播放信息、签名/指纹和登录辅助。view元数据、认证隔离、限额、缓存和节选由本项目独立实现；未安装yt-dlp或第三方AstrBot插件。此事实接口不保证长期稳定。
