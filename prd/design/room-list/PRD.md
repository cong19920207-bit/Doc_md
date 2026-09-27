# 房间列表
> 功能 ID：`room-list` · 权威：`current` · 产品：Hayyo · 更新：2026-09-16  
> 现行规则收到 V1.4.0。旧版原文见 [`history/`](history/)。叠稿回退见 [`history/PRD.stacked-2026-09-16.md`](history/PRD.stacked-2026-09-16.md)。  
> 拍板记录见 [`../../CONFIRMED.md`](../../CONFIRMED.md)。未收入版本或原文未写的接口/字段：不编造。

## 范围
- App 房间列表官方房置顶。
- 无游戏房列表坑位，无主播房列表坑位。

## 关联后台
- 后台页面与配置以 [`../admin/PRD.md`](../admin/PRD.md) 为准；本文只写 App 侧规则。
- 官方房 / 运营房相关后台：[`../admin/PRD.md#admin-rooms`](../admin/PRD.md#admin-rooms)

## 规则

### 官方房置顶

背景：英语、土语没有官方房，新人礼包推荐进入阿语官方房，用户进入房间后进入首页看不到官方房。

需求：阿语、英语、土语对应房间列表顶部置顶目前唯一的阿语官方房（技术方案为强行置顶，列表排序不会因为热度影响）。

## 版本

明细见 [`changelog.md`](changelog.md)。原文切片与叠稿在 [`history/`](history/)。
