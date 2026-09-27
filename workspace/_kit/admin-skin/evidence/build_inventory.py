# 一次性：由现网菜单树生成对照表。台账不是产品权威。
# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TREE = json.loads(Path(__file__).with_name("menu-tree-2026-09-04.json").read_text(encoding="utf-8"))

MODULES = {
    0: "Manage",
    1: "数据统计",
    2: "平台配置",
    3: "Audit",
    4: "代理管理",
    5: "后台配置",
}

# (模块, 分组, 页面名) -> (锚点, 状态, 备注)
EXACT = {
    ("Manage", "Manage Room", "房间管理"): ("#admin-rooms", "matched", ""),
    ("Manage", "Manage Room", "运营房管理"): ("#admin-rooms", "matched", ""),
    ("Manage", "Manage Room", "运营房考核标准"): ("#admin-rooms", "matched", ""),
    ("Manage", "Manage Room", "Audit Room"): ("#admin-rooms", "matched", "PRD：房间管理复制一份纯英文 Audit Room"),
    ("Manage", "Manage Room", "官方房考核标准"): ("#admin-room-kpi", "matched", "V1.1.0 考核"),
    ("Manage", "Manage Room", "管理员工作时间配置"): ("#admin-rooms", "matched", ""),
    ("Manage", "Manage Room", "官方房房间管理员配置"): ("#admin-rooms", "matched", ""),
    ("Manage", "Manage User", "账号信息"): ("#admin-users", "matched", "3.3.2.1"),
    ("Manage", "Manage User", "User list"): ("#admin-users", "matched", "金标准；3.3.2.3 / 3.3.2.4"),
    ("Manage", "Manage User", "账号添加好友"): ("#admin-rooms", "uncertain", "PRD 写在房间章「官方账号添加好友」"),
    ("Manage", "Manage User", "用户登录设备"): ("#admin-users", "uncertain", "可能是详情「登陆记录」拆页"),
    ("Manage", "Manage User", "自动封号记录"): ("#admin-currency", "matched", "正文在货币章 3.8.10，菜单在 User"),
    ("Manage", "Manage User", "平台排行榜白名单"): ("#admin-grant", "matched", "写在赠送章附近 3.8.2"),
    ("Manage", "Manage User", "用户网络测试结果"): ("#admin-currency", "matched", "正文在货币章后 3.8.14，菜单在 User"),
    ("Manage", "Manage User", "设备号封禁"): ("#admin-users", "matched", "3.4.6.2"),
    ("Manage", "Manage User", "设备指纹封禁"): ("#admin-users", "matched", "3.9.2"),
    ("Manage", "Manage User", "代理充值白名单"): ("#admin-merchant", "matched", "菜单在 User，规则在币商 3.1.5.6"),
    ("Manage", "Manage User", "帐号封禁"): ("#admin-users", "matched", "3.8.7"),
    ("Manage", "Manage User", "设备指纹风控记录"): ("#admin-users", "matched", "3.9.3"),
    ("Manage", "Manage User", "个人靓号变动记录"): ("3.9.1", "matched", "第九部分其他需求；不是商城管理"),
    ("Manage", "Manage Family", "家族管理"): ("—", "live-only", "PRD 无独立后台章"),
    ("Manage", "Manage VIP", "VIP Pool"): ("#admin-vip", "matched", ""),
    ("Manage", "Manage VIP", "VIP 消费数据"): ("#admin-vip", "matched", ""),
    ("Manage", "Manage VIP", "VIP升降级"): ("#admin-vip", "matched", ""),
    ("Manage", "货币管理", "自动返币配置"): ("—", "live-only", "DigHunt，货币章无此页"),
    ("Manage", "货币管理", "自动返币申请"): ("—", "live-only", "DigHunt，货币章无此页"),
    ("Manage", "货币管理", "自动返币记录"): ("—", "live-only", "DigHunt，货币章无此页"),
    ("Manage", "货币管理", "申请加减货币"): ("#admin-currency", "matched", "3.3.2.1"),
    ("Manage", "货币管理", "货币操作记录"): ("#admin-currency", "matched", "3.3.2.3"),
    ("Manage", "货币管理", "货币审核记录"): ("#admin-currency", "matched", "3.3.2.2"),
    ("Manage", "货币管理", "申请加减金币"): ("#admin-merchant", "matched", "PRD 写在币商章；菜单位置：货币管理-代理金币操作"),
    ("Manage", "货币管理", "申请操作查询"): ("#admin-merchant", "matched", "3.1.5.1 / 3.1.5.2"),
    ("Manage", "货币管理", "审核记录"): ("#admin-merchant", "matched", "3.1.5.2 金币审核记录"),
    ("Manage", "货币管理", "转账记录"): ("#admin-merchant", "matched", "3.1.5.3 代理转账"),
    ("Manage", "货币管理", "平台给代理自动补币"): ("#admin-merchant", "matched", "3.1.5.4"),
    ("Manage", "货币管理", "薪资抵扣审核记录"): ("—", "live-only", "货币章无薪资模块"),
    ("Manage", "货币管理", "薪资结算"): ("—", "live-only", "货币章无薪资模块"),
    ("Manage", "货币管理", "薪资结算审核记录"): ("—", "live-only", "货币章无薪资模块"),
    ("Manage", "货币管理", "主播薪资明细"): ("—", "live-only", "货币章无薪资模块"),
    ("Manage", "货币管理", "扣薪/加薪记录"): ("—", "live-only", "货币章无薪资模块"),
    ("Manage", "货币管理", "退款冻币用户"): ("#admin-currency", "matched", "3.3.2.7"),
    ("Manage", "货币管理", "补单"): ("#admin-currency", "matched", "系统消息另见 #admin-recharge-msg，本页未拆菜单"),
    ("Manage", "货币管理", "金币操作查询"): ("#admin-currency", "matched", ""),
    ("Manage", "货币管理", "钻石操作查询"): ("—", "live-only", "PRD 已删钻石，现网仍有查询页"),
    ("Manage", "货币管理", "宝石操作查询"): ("#admin-currency", "matched", "货币类型含宝石"),
    ("Manage", "币商管理", "币商代理管理"): ("#admin-merchant", "matched", ""),
    ("Manage", "预警管理", "预警任务"): ("#admin-alert", "matched", ""),
    ("数据统计", "用户统计", "新增用户"): ("#admin-stats", "matched", "3.2.1.1"),
    ("数据统计", "用户统计", "活跃用户"): ("#admin-stats", "matched", "3.2.1.2"),
    ("数据统计", "用户统计", "用户留存"): ("#admin-stats", "matched", "3.2.1.3"),
    ("数据统计", "用户统计", "用户平台时长"): ("#admin-stats", "matched", "3.2.1.4"),
    ("数据统计", "用户统计", "新用户充值"): ("#admin-stats", "matched", "3.2.1.5"),
    ("数据统计", "用户统计", "新用户来源统计"): ("#admin-stats", "matched", "3.2.1.6"),
    ("数据统计", "用户统计", "新用户平台时长"): ("#admin-stats", "live-only", "与「用户平台时长」并列"),
    ("数据统计", "用户统计", "平台日总表"): ("#admin-stats", "matched", "3.2.1.7"),
    ("数据统计", "用户统计", "平台消耗日总表"): ("#admin-stats", "matched", "3.2.1.8"),
    ("数据统计", "用户统计", "新人行为留存"): ("#admin-stats", "matched", "PRD 名「新人行为统计日表」"),
    ("数据统计", "用户统计", "用户平台时长详情"): ("#admin-stats", "matched", "3.2.1.10"),
    ("数据统计", "用户统计", "家族日总表"): ("—", "live-only", ""),
    ("数据统计", "用户统计", "邀请日总表"): ("#admin-referral-v130", "uncertain", "也可能只是统计，不是拉新后台"),
    ("数据统计", "用户统计", "邀请查询"): ("#admin-referral-v130", "uncertain", ""),
    ("数据统计", "用户统计", "Cp关系日总表"): ("—", "live-only", ""),
    ("数据统计", "消费统计", "用户充币统计"): ("#admin-stats", "matched", "3.2.3.1"),
    ("数据统计", "消费统计", "用户订阅日志"): ("—", "live-only", ""),
    ("数据统计", "消费统计", "用户充值日志"): ("#admin-stats", "matched", "3.2.3.2"),
    ("数据统计", "消费统计", "用户订阅操作日志"): ("—", "live-only", ""),
    ("数据统计", "消费统计", "用户充值操作日志"): ("#admin-stats", "matched", "3.2.3.3"),
    ("数据统计", "商品统计", "金币统计"): ("#admin-stats", "matched", "3.2.4.1"),
    ("数据统计", "商品统计", "钻石统计"): ("—", "live-only", "多份 PRD 已删钻石，现网仍有入口"),
    ("数据统计", "商品统计", "宝石统计"): ("#admin-stats", "matched", "3.2.4.2"),
    ("数据统计", "商品统计", "礼物统计"): ("#admin-stats", "matched", "3.2.4.3"),
    ("数据统计", "商品统计", "礼物查询"): ("#admin-stats", "matched", "3.2.4.4"),
    ("数据统计", "商品统计", "游戏币统计"): ("—", "live-only", ""),
    ("数据统计", "商品统计", "周星统计"): ("#admin-stats", "matched", "3.2.4.5"),
    ("数据统计", "商品统计", "商品统计"): ("#admin-stats", "matched", "3.2.4.6"),
    ("数据统计", "商品统计", "用户金币流向"): ("#admin-stats", "matched", "3.2.4.7"),
    ("数据统计", "商品统计", "爆奖礼物统计"): ("#admin-gift-burst", "matched", ""),
    ("数据统计", "商品统计", "爆奖礼物消费统计"): ("#admin-gift-burst", "matched", ""),
    ("数据统计", "商品统计", "幸运礼物统计"): ("#admin-stats", "matched", "3.2.4.8"),
    ("数据统计", "房间统计", "房间在线统计"): ("#admin-stats", "matched", "3.2.2"),
    ("数据统计", "房间统计", "房间消耗统计"): ("#admin-stats", "matched", "3.2.2"),
    ("数据统计", "房间统计", "活动房/运营房统计"): ("#admin-stats", "matched", "3.2.2"),
    ("数据统计", "房间统计", "房间用户监控管理"): ("—", "live-only", ""),
    ("数据统计", "房间统计", "房间用户监控统计"): ("—", "live-only", ""),
    ("数据统计", "房间统计", "礼物计数器"): ("#admin-stats", "matched", "3.2.5"),
    ("数据统计", "房间统计", "俱乐部统计"): ("—", "live-only", ""),
    ("数据统计", "房间统计", "数据总览"): ("#admin-stats", "uncertain", "PK 总览，PRD 未单列此菜单名"),
    ("数据统计", "房间统计", "数据详情"): ("#admin-stats", "uncertain", "PK 详情"),
    ("数据统计", "游戏统计", "水果机/动物机统计"): ("#admin-room-game", "matched", ""),
    ("数据统计", "排行榜统计", "礼物排行榜"): ("#admin-stats-ranking", "uncertain", "PRD 3.2.7 是房间送礼/用户送礼/收钻/充值，不是「礼物排行榜」这一页"),
    ("数据统计", "客服统计", "客服处理统计"): ("#admin-stats", "matched", "3.2.9"),
    ("数据统计", "AppsFlyer", "渠道报表统计"): ("#admin-stats-channel", "uncertain", "PRD 只有渠道日报；与「新人行为统计」URL 可能对调"),
    ("数据统计", "AppsFlyer", "新人行为统计"): ("#admin-stats-channel", "uncertain", "AppsFlyer 组，未对字段"),
    ("数据统计", "AppsFlyer", "Campaign管理"): ("#admin-stats-channel", "uncertain", "PRD 渠道章未单列 Campaign"),
    ("数据统计", "AppsFlyer", "BD账号统计"): ("#admin-stats-channel", "uncertain", "PRD 渠道章未单列 BD 账号"),
    ("数据统计", "任务统计", "新手任务统计"): ("#admin-stats-task", "matched", ""),
    ("数据统计", "任务统计", "每日任务统计"): ("#admin-stats-task", "matched", ""),
    ("数据统计", "埋点统计", "Sailfish明细"): ("#admin-sailfish", "matched", ""),
    ("平台配置", "商品管理", "礼物管理"): ("#admin-gifts", "matched", ""),
    ("平台配置", "商品管理", "幸运礼物管理"): ("#admin-gifts", "matched", "3.4.1.2"),
    ("平台配置", "商品管理", "周星礼物"): ("#admin-gifts", "matched", "3.4.1.3"),
    ("平台配置", "商品管理", "商城管理"): ("#admin-mall", "matched", ""),
    ("平台配置", "Banner管理", "Banner列表"): ("#admin-banner", "matched", ""),
    ("平台配置", "Banner管理", "活动管理"): ("#admin-activity", "overlay", "V1.3.0 增量；旧 Banner 章仍有活动描述"),
    ("平台配置", "敏感词管理", "关键词管理"): ("#admin-manage", "matched", "3.6.3"),
    ("平台配置", "消息管理", "惩罚理由文案配置"): ("#admin-msg", "matched", ""),
    ("平台配置", "消息管理", "惩罚消息文案配置"): ("#admin-msg", "matched", ""),
    ("平台配置", "消息管理", "Syestem消息"): ("#admin-msg", "matched", "现网拼写 Syestem"),
    ("平台配置", "消息管理", "Official/Agency消息"): ("#admin-merchant", "matched", "3.1.4.2"),
    ("平台配置", "消息管理", "房间广播"): ("#admin-msg", "matched", "3.6.4.4"),
    ("平台配置", "消息管理", "打招呼文案模板"): ("#admin-msg", "matched", "3.6.4.5"),
    ("平台配置", "消息管理", "Agency分类配置"): ("—", "live-only", ""),
    ("平台配置", "签到配置", "七日签到配置"): ("#admin-checkin", "matched", ""),
    ("平台配置", "签到配置", "新七日签到配置"): ("#admin-checkin", "matched", ""),
    ("平台配置", "休闲游戏", "休闲游戏数据"): ("#admin-casual-game", "matched", ""),
    ("平台配置", "休闲游戏", "休闲游戏配置项"): ("#admin-casual-game", "matched", ""),
    ("平台配置", "休闲游戏", "休闲游戏门票配置"): ("#admin-casual-game", "matched", ""),
    ("平台配置", "休闲游戏", "休闲游戏对局明细"): ("#admin-casual-game", "matched", ""),
    ("平台配置", "休闲游戏", "休闲游戏日报统计"): ("—", "live-only", "PRD 3.4.5 是邮件日报加游戏字段，不是此后台页"),
    ("平台配置", "福利券配置", "VIP体验券"): ("#admin-coupon", "matched", ""),
    ("平台配置", "福利券配置", "体验券使用记录"): ("#admin-coupon", "matched", ""),
    ("平台配置", "福利发放", "发放计划配置"): ("#admin-coupon", "matched", "3.7.10"),
    ("平台配置", "福利发放", "用户群体配置"): ("#admin-coupon", "matched", "3.7.11"),
    ("平台配置", "协议配置", "协议配置"): ("—", "live-only", ""),
    ("平台配置", "游戏配置", "内容配置"): ("—", "live-only", "水果大战内容"),
    ("平台配置", "游戏配置", "水果派对入口管理"): ("—", "live-only", ""),
    ("平台配置", "游戏配置", "表情配置"): ("—", "live-only", ""),
    ("Audit", "Manage Report", "Manage Report"): ("#admin-manage", "matched", "3.6.1 举报"),
    ("Audit", "Manage Feedback", "Log In Feedback"): ("#admin-manage", "matched", "3.6.2.1"),
    ("Audit", "Manage Feedback", "App Problem Feedback"): ("#admin-manage", "matched", "3.6.2.2"),
    ("Audit", "Manage Feedback", "回复子分类管理"): ("#admin-manage", "matched", "3.6.2.3"),
    ("Audit", "Manage Feedback", "回复分类管理"): ("#admin-manage", "matched", ""),
    ("Audit", "Manage Feedback", "回复模板配置"): ("#admin-manage", "matched", "3.6.2.4"),
    ("Audit", "Action Record", "Action Record"): ("#admin-manage", "matched", "3.6.6.1"),
    ("Audit", "Action Record", "平台操作记录"): ("#admin-manage", "matched", "3.6.6.2"),
    ("Audit", "Action Record", "身份修改记录"): ("#admin-manage", "matched", "3.6.6.3"),
    ("Audit", "Action Record", "后台登录记录"): ("#admin-manage", "matched", "3.6.6.4"),
    ("后台配置", "版本配置对比", "版本配置对比"): ("#admin-config", "matched", "3.8.1"),
    ("后台配置", "系统配置", "系统配置"): ("#admin-config", "uncertain", "更新弹窗语区可能在此，见 #admin-update-popup"),
    ("后台配置", "账号角色申请", "账号角色申请"): ("#admin-login", "matched", "3.1.4"),
    ("Manage", "商品赠送管理", "贵族赠送"): ("#admin-grant", "uncertain", "PRD 既保留贵族配置又写去除贵族"),
}

PREFIX = [
    (("Manage", "商品赠送管理"), "#admin-grant", "matched", ""),
    (("Manage", "拉新后台"), "#admin-referral-v130", "overlay", "旧锚点 #admin-referral 只作历史"),
    (("数据统计", "游戏统计"), "—", "live-only", "除水果机外多数无独立 admin 章"),
    (("代理管理",), "—", "live-only", "顶栏 /Agent/* 银行与销售加币，不是 Manage 币商（AnchorForum）"),
]


def strip_href(h):
    return (h or "").replace("\t", "").strip()


def classify(mod, group, name):
    key = (mod, group, name)
    if key in EXACT:
        return EXACT[key]
    for pref, anchor, status, note in PREFIX:
        if key[: len(pref)] == pref:
            if pref == ("数据统计", "游戏统计") and name == "水果机/动物机统计":
                return ("#admin-room-game", "matched", "")
            return (anchor, status, note)
    return ("—", "live-only", "本次按菜单名未对上独立章节")


def main():
    rows = []
    for nav in TREE:
        mod = MODULES[nav["i"]]
        for g in nav["groups"]:
            for it in g["items"]:
                href = strip_href(it["h"])
                anchor, status, note = classify(mod, g["g"], it["n"])
                rows.append((mod, g["g"], it["n"], href, anchor, status, note))

    from collections import Counter
    c = Counter(r[5] for r in rows)

    lines = []
    a = lines.append
    a("# 运营后台现网对照表")
    a("")
    a("> 台账，不是产品权威。现行规则仍以 [`../../../prd/design/admin/PRD.md`](../../../prd/design/admin/PRD.md) 为准。  ")
    a("> `live-only` 只归档，确认前不写入 `admin/PRD.md`。")
    a("")
    a("## 采集说明")
    a("")
    a("| 项 | 值 |")
    a("|---|---|")
    a("| 环境 | `https://fat-admin.sameronline.live`（FAT） |")
    a("| 采集日 | 2026-09-04 |")
    a("| 账号 | 当时已登录可见菜单；其它角色可能更少 |")
    a("| 壳 | `Home/Index`，layui-admin / layuimini，功能在 iframe 内页 |")
    a("| 叶子页 | %d 个（已含 `layuimini-href`） |" % len(rows))
    a("| 原始树 | [`evidence/menu-tree-2026-09-04.json`](evidence/menu-tree-2026-09-04.json) |")
    a("| 未采 | 183 页的内页截图/HTML；页内 Tab、行内按钮、二次弹窗（User list 仅采了列表/筛选结构；Operation 弹窗因列表 0 条未采） |")
    a("")
    a("## 采集范围（没有整站存档）")
    a("")
    a("**没有**把每个后台页面做成可打开的存档，**也没有**采集各页弹窗。")
    a("")
    a("| 已保存 | 未保存 |")
    a("|---|---|")
    a("| 全量菜单路径 + 内页 URL（183 条） | 183 页各自的列表字段、筛选、Tab |")
    a("| 仅 User list 的列表/筛选结构 | 各页行内按钮、二次弹窗、抽屉 |")
    a("| User list 本地仿页（金标准 + 对照 Demo） | 除 User list 外的任何页面 HTML/截图 |")
    a("")
    a("状态计数：" + "、".join(f"`{k}` {v}" for k, v in sorted(c.items())) + "。")
    a("")
    a("状态含义（**菜单级**，不是字段级；字段只核过 User list）：")
    a("")
    a("- `matched`：现网菜单名对上 PRD 现行锚点（不是「该页字段已核对」）")
    a("- `overlay`：现网有，PRD 有新旧两段，只绑新锚点")
    a("- `live-only`：现网有，PRD 无独立章节")
    a("- `prd-only`：PRD 有，这次菜单没看到")
    a("- `uncertain`：名字像，但对不准，或同大类不等于同一页")
    a("")
    a("## 顶栏")
    a("")
    a("| 现网 | PRD 锚点 | 状态 | 备注 |")
    a("|---|---|---|---|")
    a("| Manage | `#admin-ops` | matched | 运营管理壳 |")
    a("| 数据统计 | `#admin-stats` | matched | |")
    a("| 平台配置 | `#admin-platform` | matched | |")
    a("| Audit | `#admin-manage` | matched | 举报/反馈/操作记录 |")
    a("| 代理管理 | — | live-only | `/Agent/*` 银行与销售加币；币商是 Manage「币商代理管理」`#admin-merchant` |")
    a("| 后台配置 | `#admin-config` `#admin-login` | matched | 系统/角色 |")
    a("")

    cur_mod = None
    cur_g = None
    for mod, group, name, href, anchor, status, note in rows:
        if mod != cur_mod:
            if cur_mod is not None:
                a("")
            cur_mod = mod
            cur_g = None
            a(f"## {mod}")
            a("")
        if group != cur_g:
            if cur_g is not None:
                a("")
            cur_g = group
            a(f"### {group}")
            a("")
            a("| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |")
            a("|---|---|---|---|---|")
        a(f"| {name} | `{href}` | {anchor} | {status} | {note} |")

    a("")
    a("## User list 字段级（金标准）")
    a("")
    a("来源：2026-09-04 现网 iframe `/ManageMent/AccountUser/Index`。")
    a("筛选：ZID、XID、Room IDX、status（Block/Ban/Frozen/**GameBan**）、搜索。")
    a("列：User ID, Pretty ID, Nickname, Photo, Bio, Room, Region, Registration Time, 在线状态, 最近登录时间, 近7天活跃天数, Nationality, Device Number, Level, Noble Level, VIP Level, RegisterSource, Account Status, Last Punished Time, Last Banned Time, **Endtime of GameBan**, Operation。")
    a("样式：layui，主按钮 `#009688`，表头 `#f2f2f2`，14px 微软雅黑。")
    a("")
    a("| 对照 | 内容 |")
    a("|---|---|")
    a("| 对上 PRD 3.3.2.3 | ZID/XID、昵称、头像、简介、房间、语区、注册时间、国籍、设备、等级、VIP、状态、处罚/封禁时间、Operation |")
    a("| 现网有、PRD 要求去掉 | `Endtime of GameBan` 列；筛选 GameBan |")
    a("| 现网有、该节没写 | 在线状态、最近登录时间、近7天活跃天数、Noble Level、RegisterSource |")
    a("| PRD 有、0 条数据时未见 | Binding Method；Action 的 block/ban/modify/Reset（行内按钮未露出） |")
    a("")
    a("改这一页时：以 [`gold/index.html`](gold/index.html) 为改前稿，不要用文档图。")
    a("")
    a("## PRD 有、这次菜单没单独看到")
    a("")
    a("| PRD 锚点 | 内容 | 判断 |")
    a("|---|---|---|")
    a("| `#admin-login` 登录页 | 登录/滑块/改密 | 壳外页面，预期如此 |")
    a("| `#admin-update-popup` | 更新弹窗语区 | 可能在系统配置内，uncertain |")
    a("| `#admin-recharge-msg` | 补单系统消息 | 可能叠在「补单」页，未拆菜单 |")
    a("| `#admin-merchant` 3.1.5.7 | 币商代理灰名单 | PRD 写在 Manage-用户管理；这次菜单没有单独入口 |")
    a("| 3.8.2 域登陆 | 域登录 | `prd-only` 或藏在系统配置 |")
    a("")
    a("## 仍缺的采集")
    a("")
    a("1. User list 用有数据账号点开 Operation，补 block/ban/modify/Reset 弹窗字段")
    a("2. 换超管账号核对是否还有隐藏菜单")
    a("3. 系统配置内页是否含更新弹窗语区")
    a("4. 改某一页之前，再采该页字段、Tab、弹窗（不要假定已保存）")
    a("")

    out = ROOT / "inventory.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", out, "rows", len(rows), dict(c))


if __name__ == "__main__":
    main()
