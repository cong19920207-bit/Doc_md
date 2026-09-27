# 文档索引

> 人和 AI 读 **Hayyo 产品规则** 的默认入口。最后更新：2026-09-20。机器路由以 [`llm-manifest.json`](llm-manifest.json) 为准。  
> 已收录 [`../Aold_D/`](../Aold_D/)（旧称 `demo/`）内 **V1.0.0～V1.4.0** 产品规则。版本三态（已收录 / 待确认收录 / 工作区文档，非权威）见 [`VERSIONS.md`](VERSIONS.md)。V1.5.0 在 [`../workspace/v1.5.0/`](../workspace/v1.5.0/README.md)，不覆盖 V1.4.0。补丁里的规则同样是项目功能。  
> 仓库总入口 [`../INDEX.md`](../INDEX.md)。本仓库工程文档在 [`../site/docs/INDEX.md`](../site/docs/INDEX.md)，不在本目录。

## 怎么读

- 改某个功能：打开对应 **`PRD.md`**（现行唯一权威正文），并看 **「关联后台」**（有则再打开后台锚点）。同一条规则以后出现的版本为准；**当前权威收到 V1.4.0**。V1.5.0 非权威。
- [`CONFIRMED.md`](CONFIRMED.md) 是 RQ 拍板账本，不是功能正文。清洗完成后日常不必先读完全表；若 PRD 与拍板冲突，先对账再改 PRD。
- 记一条尚未写入 `PRD.md` 的产品缺口：打开 [`inbox/INDEX.md`](inbox/INDEX.md)。**不当合同**；`条目/` 不默认读。本仓库工程事项去 [`../site/docs/inbox/INDEX.md`](../site/docs/inbox/INDEX.md)。
- 改后台菜单 / 配置页：打开 [`design/admin/PRD.md`](design/admin/PRD.md)，用文首 **「关联客户端」** 反查 App 功能。读后台现行说明、日后切块：[`design/admin/brief/current.md`](design/admin/brief/current.md)（派生，锚点与 PRD 同名）。
- 问某版本发了什么：[`VERSIONS.md`](VERSIONS.md)。
- 对原文：各功能 `history/`（含叠稿回退 `history/PRD.stacked-2026-09-16.md`，不默认读）。
- 排除：`history/`、`archive/`、[`../Aold_D/`](../Aold_D/)（旧称 `demo/`）。图在各功能 `images/`。旧文中的 `垃圾桶/` 当前不存在。
- 权威分工：后台页面与配置在 `admin`；App 交互在对应功能。不复制同一条公式到两份正文。
- Chunk：默认切当前功能 `brief/current.md` 的章节（含 24 个客户端与运营后台；给人读现行规则，兼作日后切块源）。`PRD.md` 只用于校对，不进默认切块。`brief/` 不进 [`llm-manifest.json`](llm-manifest.json) 的 `scan_roots`。相关功能走 `related_documents` 二次跳转，不把 `history/` 切进默认块。

## 任务 → 当前权威

| 任务或功能 | 打开这一份 |
|---|---|
| 拍板记录（RQ 账本，不是功能正文） | [`CONFIRMED.md`](CONFIRMED.md) |
| 记一条未立项产品缺口（不当合同） | [`inbox/INDEX.md`](inbox/INDEX.md) |
| 登录注册 | [`design/auth-login/PRD.md`](design/auth-login/PRD.md) |
| 签到与任务 | [`design/checkin-task/PRD.md`](design/checkin-task/PRD.md) |
| 用户等级 | [`design/user-level/PRD.md`](design/user-level/PRD.md) |
| 拉新 | [`design/referral/PRD.md`](design/referral/PRD.md) |
| 币商 | [`design/merchant/PRD.md`](design/merchant/PRD.md) |
| YallaPay | [`design/yallapay/PRD.md`](design/yallapay/PRD.md) |
| 积分提现 | [`design/payout/PRD.md`](design/payout/PRD.md) |
| 个人中心 | [`design/profile/PRD.md`](design/profile/PRD.md) |
| 消息 | [`design/messaging/PRD.md`](design/messaging/PRD.md) |
| 金币充值 | [`design/recharge/PRD.md`](design/recharge/PRD.md) |
| 房间 | [`design/room/PRD.md`](design/room/PRD.md) |
| 房间聊天频率 / Android 列表 | [`design/room-chat/PRD.md`](design/room-chat/PRD.md) |
| 房间列表官方房置顶 | [`design/room-list/PRD.md`](design/room-list/PRD.md) |
| 排行榜 | [`design/ranking/PRD.md`](design/ranking/PRD.md) |
| 商城 / 背包 / 靓号 | [`design/mall/PRD.md`](design/mall/PRD.md) |
| 关系体系 | [`design/relationship/PRD.md`](design/relationship/PRD.md) |
| 用户 VIP | [`design/vip/PRD.md`](design/vip/PRD.md) |
| 福利券 | [`design/coupon/PRD.md`](design/coupon/PRD.md) |
| 抽奖 | [`design/lottery/PRD.md`](design/lottery/PRD.md) |
| 房间游戏（水果机等） | [`design/room-game/PRD.md`](design/room-game/PRD.md) |
| 休闲游戏（含门票表、逃跑/管理结束） | [`design/casual-game/PRD.md`](design/casual-game/PRD.md) |
| 应用改名 / 更新弹窗 | [`design/app-branding/PRD.md`](design/app-branding/PRD.md) |
| 运营后台（独立模块；与客户端用指针互指） | [`design/admin/PRD.md`](design/admin/PRD.md)（权威）；现行说明 [`design/admin/brief/current.md`](design/admin/brief/current.md) |
| 渠道埋点 | [`design/channel-tracking/PRD.md`](design/channel-tracking/PRD.md) |
| 基建与跨模块优化 | [`design/infra/PRD.md`](design/infra/PRD.md) |
| 术语 / 缺口 | [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) |
| 版本切片 | [`VERSIONS.md`](VERSIONS.md) |

## 功能 ID 对照

| 功能 ID | 中文名 | 主要来源版本 |
|---|---|---|
| `auth-login` | 登录注册 | V1.0.0 + V1.0.1 + V1.1.0 + V1.4.0 |
| `checkin-task` | 签到与任务 | V1.0.0 |
| `user-level` | 用户等级 | V1.0.0 |
| `referral` | 拉新 | V1.0.0 + V1.3.1 + V1.3.2 + V1.4.0（V1.1.0 补充见 infra；后台见 admin） |
| `merchant` | 币商 | V1.0.0 |
| `yallapay` | YallaPay | V1.1.0 目录 + V1.1.1 正文 |
| `payout` | 积分提现 | V1.4.0（不并入 yallapay） |
| `profile` | 个人中心 | V1.0.0 + V1.4.0 指针 |
| `messaging` | 消息 | V1.0.0 + V1.4.0 |
| `recharge` | 金币充值 | V1.0.0 |
| `room` | 房间 | V1.0.0 + V1.1.0 房间内需求 + V1.4.0 |
| `room-chat` | 房间聊天 | V1.0.1 |
| `room-list` | 房间列表置顶 | V1.0.1 |
| `ranking` | 排行榜 | V1.0.0 |
| `mall` | 商城背包靓号 | V1.0.0 + V1.4.0 |
| `relationship` | 关系体系 | V1.0.0 |
| `vip` | 用户 VIP | V1.0.0 |
| `coupon` | 福利券 | V1.1.0 + V1.4.0 |
| `lottery` | 抽奖 | V1.1.0 + V1.4.0 |
| `room-game` | 房间游戏 | V1.0.0 + V1.4.0 |
| `casual-game` | 休闲游戏 | V1.3.0 + V1.3.2 + 门票 Excel + V1.4.0 |
| `app-branding` | 品牌 / 更新 | V1.2.0 + V1.3.0 + V1.4.0 |
| `admin` | 运营后台 | V1.0.0 独立后台 + V1.1.0 第七部分 + V1.3.0 + V1.4.0 |
| `channel-tracking` | 渠道埋点 | V1.0.1 + V1.1.0 + V1.3.0 |
| `infra` | 基建与其他 | 各版「其他/基建/其他优化」+ V1.4.0 |

`gift-burst` 爆奖礼物**客户端**正文在 V1.1.0「房间内需求」，合入 [`design/room/PRD.md`](design/room/PRD.md)；**后台**在 [`design/admin/PRD.md#admin-gift-burst`](design/admin/PRD.md#admin-gift-burst)。

## 客户端 ↔ 后台

后台独立成模块，不把后台页面拆进各功能。关联只用指针。对照也可从 `admin` 文首「关联客户端」反查。切块与现行说明走 `admin/brief/current.md` 同名锚；改字段仍改 `admin/PRD.md`。

| 客户端功能 | 主要后台锚点 |
|---|---|
| [`room`](design/room/PRD.md) / [`room-list`](design/room-list/PRD.md) | [房间管理](design/admin/PRD.md#admin-rooms)、[礼物](design/admin/PRD.md#admin-gifts)、[爆奖礼物](design/admin/PRD.md#admin-gift-burst)、[活动](design/admin/PRD.md#admin-activity) |
| [`mall`](design/mall/PRD.md) | [商城管理](design/admin/PRD.md#admin-mall)、[赠送](design/admin/PRD.md#admin-grant) |
| [`merchant`](design/merchant/PRD.md) | [币商后台](design/admin/PRD.md#admin-merchant) |
| [`referral`](design/referral/PRD.md) | [拉新后台](design/admin/PRD.md#admin-referral)（含奖励组 / 批量查询；旧锚点 `#admin-referral-v130` 同章） |
| [`payout`](design/payout/PRD.md) | [积分与提现 V1.4.0](design/admin/PRD.md#admin-payout) |
| [`casual-game`](design/casual-game/PRD.md) | [休闲游戏后台](design/admin/PRD.md#admin-casual-game) |
| [`checkin-task`](design/checkin-task/PRD.md) | [签到管理](design/admin/PRD.md#admin-checkin)、[任务统计](design/admin/PRD.md#admin-stats-task) |
| [`recharge`](design/recharge/PRD.md) | [货币管理](design/admin/PRD.md#admin-currency)、[补单消息](design/admin/PRD.md#admin-recharge-msg) |
| [`vip`](design/vip/PRD.md) | [VIP 后台](design/admin/PRD.md#admin-vip)、[赠送](design/admin/PRD.md#admin-grant) |
| [`ranking`](design/ranking/PRD.md) | [排行榜后台](design/admin/PRD.md#admin-stats-ranking) |
| [`messaging`](design/messaging/PRD.md) | [消息管理](design/admin/PRD.md#admin-msg) |
| [`channel-tracking`](design/channel-tracking/PRD.md) | [渠道报表](design/admin/PRD.md#admin-stats-channel) |
| [`coupon`](design/coupon/PRD.md) | [体验券 / 发放体系](design/admin/PRD.md#admin-coupon) |
| [`room-game`](design/room-game/PRD.md) | [水果机统计](design/admin/PRD.md#admin-room-game) |
| [`auth-login`](design/auth-login/PRD.md) / [`profile`](design/profile/PRD.md) | [用户管理](design/admin/PRD.md#admin-users) |
| [`app-branding`](design/app-branding/PRD.md) | [更新弹窗语区](design/admin/PRD.md#admin-update-popup)、[活动 Banner](design/admin/PRD.md#admin-banner) |

登录权限、多数数据统计、操作审计为纯后台，不挂客户端。

## 维护

- 版本状态只使用 **已收录 / 待确认收录 / 工作区文档，非权威**。定义见 [`VERSIONS.md`](VERSIONS.md)。
- 同一功能只有一份当前权威：`design/<功能>/PRD.md`。
- 后台页面只写在 `admin`；客户端用「关联后台」指针，不复制配置字段。
- 补丁包是发版形态，其中规则按项目功能收录。
- 缺证据标 `needs-input` / `needs-review`。
- 立项前缺口进 [`inbox/`](inbox/INDEX.md)，不当现行规则。确认后再改对应功能 `PRD.md`。
- 原文 Word 只在 [`../Aold_D/`](../Aold_D/)（旧称 `demo/`），不删除。各功能正文里的 `demo/` 来源路径即此目录。
