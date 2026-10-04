# 运营后台现网对照表

> 台账，不是产品权威。现行规则仍以 [`../../../site/core-docs/prd/design/admin/PRD.md`](../../../site/core-docs/prd/design/admin/PRD.md) 为准。  
> `live-only` 只归档，确认前不写入 `admin/PRD.md`。

## 采集说明

| 项 | 值 |
|---|---|
| 环境 | `https://fat-admin.sameronline.live`（FAT） |
| 采集日 | 2026-09-04 |
| 账号 | 当时已登录可见菜单；其它角色可能更少 |
| 壳 | `Home/Index`，layui-admin / layuimini，功能在 iframe 内页 |
| 叶子页 | 183 个（已含 `layuimini-href`） |
| 原始树 | [`evidence/menu-tree-2026-09-04.json`](evidence/menu-tree-2026-09-04.json) |
| 未采 | 183 页的内页截图/HTML；页内 Tab、行内按钮、二次弹窗（User list 仅采了列表/筛选结构；Operation 弹窗因列表 0 条未采） |

## 采集范围（没有整站存档）

**没有**把每个后台页面做成可打开的存档，**也没有**采集各页弹窗。

| 已保存 | 未保存 |
|---|---|
| 全量菜单路径 + 内页 URL（183 条） | 183 页各自的列表字段、筛选、Tab |
| 仅 User list 的列表/筛选结构 | 各页行内按钮、二次弹窗、抽屉 |
| User list 本地仿页（金标准 + 对照 Demo） | 除 User list 外的任何页面 HTML/截图 |

状态计数：`live-only` 50、`matched` 104、`overlay` 16、`uncertain` 13。

状态含义（**菜单级**，不是字段级；字段只核过 User list）：

- `matched`：现网菜单名对上 PRD 现行锚点（不是「该页字段已核对」）
- `overlay`：现网有，PRD 有新旧两段，只绑新锚点
- `live-only`：现网有，PRD 无独立章节
- `prd-only`：PRD 有，这次菜单没看到
- `uncertain`：名字像，但对不准，或同大类不等于同一页

## 顶栏

| 现网 | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|
| Manage | `#admin-ops` | matched | 运营管理壳 |
| 数据统计 | `#admin-stats` | matched | |
| 平台配置 | `#admin-platform` | matched | |
| Audit | `#admin-manage` | matched | 举报/反馈/操作记录 |
| 代理管理 | — | live-only | `/Agent/*` 银行与销售加币；币商是 Manage「币商代理管理」`#admin-merchant` |
| 后台配置 | `#admin-config` `#admin-login` | matched | 系统/角色 |

## Manage

### Manage Room

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 房间管理 | `/ManageMent/RoomManage/RoomConfig` | #admin-rooms | matched |  |
| 运营房管理 | `/ManageMent/OperationRoom/OperationRoomConfig` | #admin-rooms | matched |  |
| 运营房考核标准 | `/ManageMent/OperationRoom/Wage` | #admin-rooms | matched |  |
| Audit Room | `/ManageMent/RoomManage/ForeignRoomConfig` | #admin-rooms | matched | PRD：房间管理复制一份纯英文 Audit Room |
| 官方房考核标准 | `/ManageMent/OfficialRoomManagerSalary/Index` | #admin-room-kpi | matched | V1.1.0 考核 |
| 管理员工作时间配置 | `/ManageMent/OfficialRoomManager/Index` | #admin-rooms | matched |  |
| 官方房房间管理员配置 | `/ManageMent/OfficialRoomOperator/Index` | #admin-rooms | matched |  |

### Manage User

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 账号信息 | `/ManageMent/Account/Index` | #admin-users | matched | 3.3.2.1 |
| User list | `/ManageMent/AccountUser/Index` | #admin-users | matched | 金标准；3.3.2.3 / 3.3.2.4 |
| 账号添加好友 | `/ManageMent/BestFriendsLog/BestFriendsLogIndex` | #admin-rooms | uncertain | PRD 写在房间章「官方账号添加好友」 |
| 用户登录设备 | `/ManageMent/AccountLoginRecord/LoginDevice` | #admin-users | uncertain | 可能是详情「登陆记录」拆页 |
| 自动封号记录 | `/ManageMent/OrderRefund/AccountBlockPage` | #admin-currency | matched | 正文在货币章 3.8.10，菜单在 User |
| 平台排行榜白名单 | `/ManageMent/AccountWhitelist/Index` | #admin-grant | matched | 写在赠送章附近 3.8.2 |
| 用户网络测试结果 | `/ManageMent/NetWorkTest/Index` | #admin-currency | matched | 正文在货币章后 3.8.14，菜单在 User |
| 设备号封禁 | `/ManageMent/DeviceStatus/Index` | #admin-users | matched | 3.4.6.2 |
| 设备指纹封禁 | `/ManageMent/DeviceFingerprint/Index` | #admin-users | matched | 3.9.2 |
| 代理充值白名单 | `/ManageMent/AnchorForumAgentWhitelist/Index` | #admin-merchant | matched | 菜单在 User，规则在币商 3.1.5.6 |
| 帐号封禁 | `/ManageMent/BlockUser/Index` | #admin-users | matched | 3.8.7 |
| 设备指纹风控记录 | `/ManageMent/RiskFingerprint/RecordIndex` | #admin-users | matched | 3.9.3 |
| 个人靓号变动记录 | `/ManageMent/PrettyvipidLog/Index` | 3.9.1 | matched | 第九部分其他需求；不是商城管理 |

### Manage Family

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 家族管理 | `/ManageMent/Family/Index` | — | live-only | PRD 无独立后台章 |

### Manage VIP

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| VIP Pool | `/ManageMent/AccountKa/Index` | #admin-vip | matched |  |
| VIP 消费数据 | `/ManageMent/StsKaConsum/VipIndex` | #admin-vip | matched |  |
| VIP升降级 | `/ManageMent/AccountViplevelLog/Index` | #admin-vip | matched |  |

### 货币管理

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 自动返币配置 | `/ManageMent/DigHuntUserRefundCoinConfig/Index` | — | live-only | DigHunt，货币章无此页 |
| 自动返币申请 | `/ManageMent/DigHuntUserRefundCoinVerify/Index` | — | live-only | DigHunt，货币章无此页 |
| 自动返币记录 | `/ManageMent/DighuntuserRefundcoinLog/Index` | — | live-only | DigHunt，货币章无此页 |
| 申请加减货币 | `/ManageMent/InsideCurrencyVerify/InsideCurrency` | #admin-currency | matched | 3.3.2.1 |
| 货币操作记录 | `/ManageMent/InsideCurrencyVerify/InsideCurrencyLogIndex` | #admin-currency | matched | 3.3.2.3 |
| 货币审核记录 | `/ManageMent/InsideCurrencyVerify/InsideCurrencyCheckIndex` | #admin-currency | matched | 3.3.2.2 |
| 申请加减金币 | `/ManageMent/InsideAgentVerify/InsideAgent` | #admin-merchant | matched | PRD 写在币商章；菜单位置：货币管理-代理金币操作 |
| 申请操作查询 | `/ManageMent/InsideAgentVerify/InsideAgentLogPage` | #admin-merchant | matched | 3.1.5.1 / 3.1.5.2 |
| 审核记录 | `/ManageMent/InsideAgentVerify/InsideAgentCheckLogPage` | #admin-merchant | matched | 3.1.5.2 金币审核记录 |
| 转账记录 | `/ManageMent/InsideAgentVerify/InsideAgentTransferLog` | #admin-merchant | matched | 3.1.5.3 代理转账 |
| 平台给代理自动补币 | `/ManageMent/InsideAgentVerify/InsideAgentTransferRepairLog` | #admin-merchant | matched | 3.1.5.4 |
| 薪资抵扣审核记录 | `/ManageMent/AnchorForumSalaryDeduction/Index` | — | live-only | 货币章无薪资模块 |
| 薪资结算 | `/ManageMent/AnchorForumSalaryDeduction/SettlementIndex` | — | live-only | 货币章无薪资模块 |
| 薪资结算审核记录 | `/ManageMent/AnchorForumSalaryDeduction/SettlementVerifyIndex` | — | live-only | 货币章无薪资模块 |
| 主播薪资明细 | `/ManageMent/AnchorForumSalaryDeduction/AnchorSalaryIndex` | — | live-only | 货币章无薪资模块 |
| 扣薪/加薪记录 | `/ManageMent/AnchorForumSalaryDeduction/SalaryCorrectLogIndex` | — | live-only | 货币章无薪资模块 |
| 退款冻币用户 | `/ManageMent/OrderRefund/OrderRefundPage` | #admin-currency | matched | 3.3.2.7 |
| 补单 | `/ManageMent/OrderSupplement/Index` | #admin-currency | matched | 系统消息另见 #admin-recharge-msg，本页未拆菜单 |
| 金币操作查询 | `/ManageMent/InsideCoinVerify/InsideCoinLogPage` | #admin-currency | matched |  |
| 钻石操作查询 | `/ManageMent/InsideDiamondVerify/InsideDiamondLogPage` | — | live-only | PRD 已删钻石，现网仍有查询页 |
| 宝石操作查询 | `/ManageMent/InsideGemStoneVerify/InsideGemStoneLogPage` | #admin-currency | matched | 货币类型含宝石 |

### 币商管理

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 币商代理管理 | `/ManageMent/AnchorForum/Index` | #admin-merchant | matched |  |

### 商品赠送管理

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 商品赠送 | `/ManageMent/SysShopSend/Index` | #admin-grant | matched |  |
| 贵族赠送 | `/ManageMent/SysNobleSend/Index` | #admin-grant | uncertain | PRD 既保留贵族配置又写去除贵族 |
| 靓号赠送 | `/ManageMent/PrettyVipIdSend/Index` | #admin-grant | matched |  |
| VIP赠送 | `/ManageMent/ViplevelSend/Index` | #admin-grant | matched |  |

### 预警管理

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 预警任务 | `/ManageMent/Warningconfig/Index` | #admin-alert | matched |  |

### 拉新后台

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 奖励组配置 | `/ManageMent/InviteRewardGroup/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| 个人拉新周期配置 | `/ManageMent/InviteCycleConfig/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| 个人拉新后台 | `/ManageMent/InviteAccountPermission/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| 个人拉新活动统计 | `/ManageMent/InvitePersonalInviteStats/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| 个人拉新充值结算 | `/ManageMent/InvitePersonalSettlement/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| BD拉新周期配置 | `/ManageMent/InviteBdCycleConfig/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| BD拉新后台 | `/ManageMent/InviteTeamPermission/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| BD拉新活动统计 | `/ManageMent/InviteBdInviteStats/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| 币商拉新周期配置 | `/ManageMent/InviteAgentCycleConfig/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| 币商拉新后台 | `/ManageMent/InviteTeamDealerPermission/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| 币商拉新活动统计 | `/ManageMent/InviteDealerInviteStats/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| 新用户充值阶梯配置 | `/ManageMent/InviteNewUserRewardStep/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| 新用户任务配置 | `/ManageMent/InviteNewUserTask/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| 新用户奖励领取记录 | `/ManageMent/InviteNewUserTaskProgress/Index` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |
| 新用户任务完成情况统计 | `/ManageMent/InviteNewUserTaskProgress/StsNewUserTaskDay` | #admin-referral-v130 | overlay | 旧锚点 #admin-referral 只作历史 |

## 数据统计

### 用户统计

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 新增用户 | `/StsAccount/NewUser/Index` | #admin-stats | matched | 3.2.1.1 |
| 活跃用户 | `/StsAccount/ActiveUser/Index` | #admin-stats | matched | 3.2.1.2 |
| 用户留存 | `/StsAccount/UserKeep/Index` | #admin-stats | matched | 3.2.1.3 |
| 用户平台时长 | `/StsAccount/UserPlatformOnline/Index` | #admin-stats | matched | 3.2.1.4 |
| 新用户充值 | `/StsAccount/NewUserRecharge/Index` | #admin-stats | matched | 3.2.1.5 |
| 新用户来源统计 | `/StsAccount/UserSourceStatistics/Index` | #admin-stats | matched | 3.2.1.6 |
| 新用户平台时长 | `/StsAccount/NewUserPlatformOnline/Index` | #admin-stats | live-only | 与「用户平台时长」并列 |
| 平台日总表 | `/StsConsum/Plat/Index` | #admin-stats | matched | 3.2.1.7 |
| 平台消耗日总表 | `/StsConsum/Plat/PlatDepleteTotal` | #admin-stats | matched | 3.2.1.8 |
| 新人行为留存 | `/StsAccount/UserNewKeepDay/Index` | #admin-stats | matched | PRD 名「新人行为统计日表」 |
| 用户平台时长详情 | `/StsAccount/UserPlatformOnline/Show` | #admin-stats | matched | 3.2.1.10 |
| 家族日总表 | `/StsAccount/Familyday/Index` | — | live-only |  |
| 邀请日总表 | `/StsAccount/InviterDay/Index` | #admin-referral-v130 | uncertain | 也可能只是统计，不是拉新后台 |
| 邀请查询 | `/ManageMent/Inviter/Index` | #admin-referral-v130 | uncertain |  |
| Cp关系日总表 | `/StsAccount/Cpday/Index` | — | live-only |  |

### 消费统计

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 用户充币统计 | `/StsConsum/Recharge/RechargeDiamond` | #admin-stats | matched | 3.2.3.1 |
| 用户订阅日志 | `/StsConsum/SubscribeOrder/Index` | — | live-only |  |
| 用户充值日志 | `/StsConsum/Recharge/RechargeOrder` | #admin-stats | matched | 3.2.3.2 |
| 用户订阅操作日志 | `/StsConsum/SubscribeOrder/SubscribeOrderCheck` | — | live-only |  |
| 用户充值操作日志 | `/StsConsum/Recharge/OrderCheck` | #admin-stats | matched | 3.2.3.3 |

### 商品统计

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 金币统计 | `/StsProduct/StsCoin/Index` | #admin-stats | matched | 3.2.4.1 |
| 钻石统计 | `/StsProduct/StsDiamonds/Index` | — | live-only | 多份 PRD 已删钻石，现网仍有入口 |
| 宝石统计 | `/StsProduct/StsGemstone/Index` | #admin-stats | matched | 3.2.4.2 |
| 礼物统计 | `/StsProp/StatProp/Index` | #admin-stats | matched | 3.2.4.3 |
| 礼物查询 | `/StsProp/StatProp/PropSearch` | #admin-stats | matched | 3.2.4.4 |
| 游戏币统计 | `/StsProduct/StsGameCoin/Index` | — | live-only |  |
| 周星统计 | `/StsProduct/WeeklyStarsLog/Index` | #admin-stats | matched | 3.2.4.5 |
| 商品统计 | `/StsProduct/ShopConfigStatistics/Index` | #admin-stats | matched | 3.2.4.6 |
| 用户金币流向 | `/ManageMent/Currencytraderecord/Index` | #admin-stats | matched | 3.2.4.7 |
| 爆奖礼物统计 | `/StsProp/StsPropJackpot/Index` | #admin-gift-burst | matched |  |
| 爆奖礼物消费统计 | `/StsProp/StsPropJackpot/ConsumeIndex` | #admin-gift-burst | matched |  |
| 幸运礼物统计 | `/StsProp/StatProp/LuckyPropTotalIndex` | #admin-stats | matched | 3.2.4.8 |

### 房间统计

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 房间在线统计 | `/StsRoom/RoomOnlineLog/BarOnlineLogPage` | #admin-stats | matched | 3.2.2 |
| 房间消耗统计 | `/StsRoom/RoomDepleteDay/RoomDeplete` | #admin-stats | matched | 3.2.2 |
| 活动房/运营房统计 | `/StsRoom/BarActivityDay/ActivityStatistics` | #admin-stats | matched | 3.2.2 |
| 房间用户监控管理 | `/StsRoom/RoomUsermointConfig/Index` | — | live-only |  |
| 房间用户监控统计 | `/StsRoom/Roomusermoint/Index` | — | live-only |  |
| 礼物计数器 | `/StsRoom/StsGiftCounter/Index` | #admin-stats | matched | 3.2.5 |
| 俱乐部统计 | `/StsRoom/RooomClubStatistics/Index` | — | live-only |  |
| 数据总览 | `/StsRoom/StsRoomPkOverview/Index` | #admin-stats | uncertain | PK 总览，PRD 未单列此菜单名 |
| 数据详情 | `/StsRoom/StsRoomPkOverview/PkIndexDetail` | #admin-stats | uncertain | PK 详情 |

### 游戏统计

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 水果机/动物机统计 | `/StsGame/FruitDay/Index` | #admin-room-game | matched |  |
| 水果机/动物机排行榜 | `/StsGame/FruitTop/Index` | — | live-only | 除水果机外多数无独立 admin 章 |
| 幸运转盘统计 | `/StsGame/Luckwheel/Index` | — | live-only | 除水果机外多数无独立 admin 章 |
| 水果大战统计 | `/StsGame/FruitWar/Index` | — | live-only | 除水果机外多数无独立 admin 章 |
| 幸运数字统计 | `/StsGame/StsLuckynumber/Index` | — | live-only | 除水果机外多数无独立 admin 章 |
| Ludo/Domino游戏统计 | `/StsGame/GameStatistics/Index` | — | live-only | 除水果机外多数无独立 admin 章 |
| 掷色子统计 | `/StsGame/DiceDay/Index` | — | live-only | 除水果机外多数无独立 admin 章 |
| 桌球统计 | `/StsGame/GameStatistics/BilliardsIndex` | — | live-only | 除水果机外多数无独立 admin 章 |
| Ludo/Domino机器人 | `/StsGame/StsRobot/Index` | — | live-only | 除水果机外多数无独立 admin 章 |
| 蛇梯游戏统计 | `/StsGame/ShakeLadder/Index` | — | live-only | 除水果机外多数无独立 admin 章 |
| 抽奖礼物统计 | `/StsGame/GiftDrawDay/Index` | — | live-only | 除水果机外多数无独立 admin 章 |
| 拉霸统计 | `/StsGame/SlotDay/Index` | — | live-only | 除水果机外多数无独立 admin 章 |
| 游戏表情使用统计 | `/StsGame/StsEmojStatisticsDay/Index` | — | live-only | 除水果机外多数无独立 admin 章 |
| 极限赛车统计 | `/StsGame/RacingDay/Index` | — | live-only | 除水果机外多数无独立 admin 章 |
| 珠宝集会统计 | `/StsGame/StsJewelryStatisticsday/Index` | — | live-only | 除水果机外多数无独立 admin 章 |

### 排行榜统计

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 礼物排行榜 | `/StsProp/StsSysRankList/Index` | #admin-stats-ranking | uncertain | PRD 3.2.7 是房间送礼/用户送礼/收钻/充值，不是「礼物排行榜」这一页 |

### 客服统计

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 客服处理统计 | `/StsCustomer/Customerday/Index` | #admin-stats | matched | 3.2.9 |

### AppsFlyer

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 渠道报表统计 | `/AppsFlyer/ChannelStatistics/NewerBehavior` | #admin-stats-channel | uncertain | PRD 只有渠道日报；与「新人行为统计」URL 可能对调 |
| 新人行为统计 | `/AppsFlyer/ChannelStatistics/ChannelStatistics` | #admin-stats-channel | uncertain | AppsFlyer 组，未对字段 |
| Campaign管理 | `/AppsFlyer/AfAnchorUserinfo/Index` | #admin-stats-channel | uncertain | PRD 渠道章未单列 Campaign |
| BD账号统计 | `/AppsFlyer/AfAnchorUserinfo/AnchorUserStatistics` | #admin-stats-channel | uncertain | PRD 渠道章未单列 BD 账号 |

### 任务统计

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 新手任务统计 | `/StsTask/NewUserTaskSts/Index` | #admin-stats-task | matched |  |
| 每日任务统计 | `/StsTask/EveryDayTaskSts/Index` | #admin-stats-task | matched |  |

### 埋点统计

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| Sailfish明细 | `/StsTracking/StsSailfish/Index` | #admin-sailfish | matched |  |

## 平台配置

### 商品管理

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 礼物管理 | `/PlatformConfig/Prop/Index` | #admin-gifts | matched |  |
| 幸运礼物管理 | `/PlatformConfig/PropLuck/Index` | #admin-gifts | matched | 3.4.1.2 |
| 周星礼物 | `/PlatformConfig/PropWeeklyStars/Index` | #admin-gifts | matched | 3.4.1.3 |
| 商城管理 | `/PlatformConfig/ShopConfig/Index` | #admin-mall | matched |  |

### Banner管理

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| Banner列表 | `/PlatformConfig/Banner/Index` | #admin-banner | matched |  |
| 活动管理 | `/ManageMent/Activity/Index` | #admin-activity | overlay | V1.3.0 增量；旧 Banner 章仍有活动描述 |

### 敏感词管理

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 关键词管理 | `/PlatformConfig/KeyWords/Index` | #admin-manage | matched | 3.6.3 |

### 消息管理

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 惩罚理由文案配置 | `/PlatformConfig/MsgConfigType/Index` | #admin-msg | matched |  |
| 惩罚消息文案配置 | `/PlatformConfig/MsgTypeTemplate/Index` | #admin-msg | matched |  |
| Syestem消息 | `/PlatformConfig/Message/Index` | #admin-msg | matched | 现网拼写 Syestem |
| Official/Agency消息 | `/PlatformConfig/TeamMsg/Index` | #admin-merchant | matched | 3.1.4.2 |
| 房间广播 | `/PlatformConfig/RoomBroadcast/Index` | #admin-msg | matched | 3.6.4.4 |
| 打招呼文案模板 | `/PlatformConfig/SysHitemplate/Index` | #admin-msg | matched | 3.6.4.5 |
| Agency分类配置 | `/PlatformConfig/AgencyClass/Index` | — | live-only |  |

### 签到配置

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 七日签到配置 | `/PlatformConfig/Sign/Index` | #admin-checkin | matched |  |
| 新七日签到配置 | `/PlatformConfig/SignNew/Index` | #admin-checkin | matched |  |

### 休闲游戏

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 休闲游戏数据 | `/CustomReportFlag/gamedata-bytesun-stat-day` | #admin-casual-game | matched |  |
| 休闲游戏配置项 | `/PlatformConfig/GameConfigItemBytesun/Index` | #admin-casual-game | matched |  |
| 休闲游戏门票配置 | `/PlatformConfig/GameTicketConfigBytesun/Index` | #admin-casual-game | matched |  |
| 休闲游戏对局明细 | `/PlatformConfig/GameDataBytesunMatchDetail/Index` | #admin-casual-game | matched |  |
| 休闲游戏日报统计 | `/CustomReportFlag/StsCasualGameDailyReport` | — | live-only | PRD 3.4.5 是邮件日报加游戏字段，不是此后台页 |

### 游戏配置

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 内容配置 | `/Statistics/AdminFruitwarconfig/Index` | — | live-only | 水果大战内容 |
| 水果派对入口管理 | `/PlatformConfig/AccountBlackwhiteList/Index` | — | live-only |  |
| 表情配置 | `/GameConfig/ExpressionConfig/Index` | — | live-only |  |

### 福利券配置

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| VIP体验券 | `/PlatformConfig/ExperienceVoucherConfig/Index` | #admin-coupon | matched |  |
| 体验券使用记录 | `/PlatformConfig/ExperienceVoucherConfig/UseRecords` | #admin-coupon | matched |  |

### 福利发放

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 发放计划配置 | `/PlatformConfig/IssuancePlanConfig/Index` | #admin-coupon | matched | 3.7.10 |
| 用户群体配置 | `/PlatformConfig/IssuanceGroup/Index` | #admin-coupon | matched | 3.7.11 |

### 协议配置

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 协议配置 | `/PlatformConfig/SysAgreementConfig/Index` | — | live-only |  |

## Audit

### Manage Report

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| Manage Report | `/AuditCheck/Report/Index` | #admin-manage | matched | 3.6.1 举报 |

### Manage Feedback

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| Log In Feedback | `/AuditCheck/Feedback/LoginIndex` | #admin-manage | matched | 3.6.2.1 |
| App Problem Feedback | `/AuditCheck/Feedback/Index` | #admin-manage | matched | 3.6.2.2 |
| 回复子分类管理 | `/AuditCheck/ChildReplyType/Index` | #admin-manage | matched | 3.6.2.3 |
| 回复分类管理 | `/AuditCheck/ReplyType/Index` | #admin-manage | matched |  |
| 回复模板配置 | `/AuditCheck/ReplyTemplate/Index` | #admin-manage | matched | 3.6.2.4 |

### Action Record

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| Action Record | `/AuditCheck/ActionRecord/Index` | #admin-manage | matched | 3.6.6.1 |
| 平台操作记录 | `/AuditCheck/ChangeRecord/Index` | #admin-manage | matched | 3.6.6.2 |
| 身份修改记录 | `/AuditCheck/UserModifyRecord/Index` | #admin-manage | matched | 3.6.6.3 |
| 后台登录记录 | `/Sys/Admin/AdminLoginRecord` | #admin-manage | matched | 3.6.6.4 |

## 代理管理

### 代理及销售管理

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 代理及销售管理 | `/Agent/Agent/Index` | — | live-only | 顶栏 /Agent/* 银行与销售加币，不是 Manage 币商（AnchorForum） |

### 代理加币记录

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 代理加币记录 | `/Agent/AgentCoinLog/Index` | — | live-only | 顶栏 /Agent/* 银行与销售加币，不是 Manage 币商（AnchorForum） |

### 用户转账记录

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 用户转账记录 | `/Agent/AgentPay/Index` | — | live-only | 顶栏 /Agent/* 银行与销售加币，不是 Manage 币商（AnchorForum） |

### 用户加币记录

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 用户加币记录 | `/Agent/AgentForUserCoin/Index` | — | live-only | 顶栏 /Agent/* 银行与销售加币，不是 Manage 币商（AnchorForum） |

### 银行账号管理

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 银行账号管理 | `/Agent/BankAccount/Index` | — | live-only | 顶栏 /Agent/* 银行与销售加币，不是 Manage 币商（AnchorForum） |

### 银行间转账

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 银行间转账 | `/Agent/Agentpay/BankTransfer` | — | live-only | 顶栏 /Agent/* 银行与销售加币，不是 Manage 币商（AnchorForum） |

### 银行收付款记录

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 银行收付款记录 | `/Agent/AgentCoinLog/BankTransferLog` | — | live-only | 顶栏 /Agent/* 银行与销售加币，不是 Manage 币商（AnchorForum） |

### 加币用户统计

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 加币用户统计 | `/Agent/AgentForUserCoin/AddUserCoinTotal` | — | live-only | 顶栏 /Agent/* 银行与销售加币，不是 Manage 币商（AnchorForum） |

### 充值用户分析

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 充值用户分析 | `/Agent/AgentUserAnalysis/Index` | — | live-only | 顶栏 /Agent/* 银行与销售加币，不是 Manage 币商（AnchorForum） |

### 充值国家统计

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 充值国家统计 | `/Agent/AgentCountryAnalysis/Index` | — | live-only | 顶栏 /Agent/* 银行与销售加币，不是 Manage 币商（AnchorForum） |

## 后台配置

### 版本配置对比

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 版本配置对比 | `/SysConfig/VersionConfig/Index` | #admin-config | matched | 3.8.1 |

### 系统配置

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 系统配置 | `/SysConfig/ConfigSys/Index` | #admin-config | uncertain | 更新弹窗语区可能在此，见 #admin-update-popup |

### 账号角色申请

| 现网菜单 | 内页 URL | PRD 锚点 | 状态 | 备注 |
|---|---|---|---|---|
| 账号角色申请 | `/Sys/Apply/Index` | #admin-login | matched | 3.1.4 |

## User list 字段级（金标准）

来源：2026-09-04 现网 iframe `/ManageMent/AccountUser/Index`。
筛选：ZID、XID、Room IDX、status（Block/Ban/Frozen/**GameBan**）、搜索。
列：User ID, Pretty ID, Nickname, Photo, Bio, Room, Region, Registration Time, 在线状态, 最近登录时间, 近7天活跃天数, Nationality, Device Number, Level, Noble Level, VIP Level, RegisterSource, Account Status, Last Punished Time, Last Banned Time, **Endtime of GameBan**, Operation。
样式：layui，主按钮 `#009688`，表头 `#f2f2f2`，14px 微软雅黑。

| 对照 | 内容 |
|---|---|
| 对上 PRD 3.3.2.3 | ZID/XID、昵称、头像、简介、房间、语区、注册时间、国籍、设备、等级、VIP、状态、处罚/封禁时间、Operation |
| 现网有、PRD 要求去掉 | `Endtime of GameBan` 列；筛选 GameBan |
| 现网有、该节没写 | 在线状态、最近登录时间、近7天活跃天数、Noble Level、RegisterSource |
| PRD 有、0 条数据时未见 | Binding Method；Action 的 block/ban/modify/Reset（行内按钮未露出） |

改这一页时：以 [`gold/index.html`](gold/index.html) 为改前稿，不要用文档图。

## PRD 有、这次菜单没单独看到

| PRD 锚点 | 内容 | 判断 |
|---|---|---|
| `#admin-login` 登录页 | 登录/滑块/改密 | 壳外页面，预期如此 |
| `#admin-update-popup` | 更新弹窗语区 | 可能在系统配置内，uncertain |
| `#admin-recharge-msg` | 补单系统消息 | 可能叠在「补单」页，未拆菜单 |
| `#admin-merchant` 3.1.5.7 | 币商代理灰名单 | PRD 写在 Manage-用户管理；这次菜单没有单独入口 |
| 3.8.2 域登陆 | 域登录 | `prd-only` 或藏在系统配置 |

## 仍缺的采集

1. User list 用有数据账号点开 Operation，补 block/ban/modify/Reset 弹窗字段
2. 换超管账号核对是否还有隐藏菜单
3. 系统配置内页是否含更新弹窗语区
4. 改某一页之前，再采该页字段、Tab、弹窗（不要假定已保存）

