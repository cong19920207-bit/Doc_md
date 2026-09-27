# 渠道埋点
> 功能 ID：`channel-tracking` · 权威：`current` · 产品：Hayyo · 更新：2026-09-16  
> 现行规则收到 V1.4.0。旧版原文见 [`history/`](history/)。叠稿回退见 [`history/PRD.stacked-2026-09-16.md`](history/PRD.stacked-2026-09-16.md)。  
> 拍板记录见 [`../../CONFIRMED.md`](../../CONFIRMED.md)。未收入版本或原文未写的接口/字段：不编造。

## 范围
- App 投放埋点口径（AF / Firebase）。明细表外链不在本文展开。

## 关联后台
- 后台页面与配置以 [`../admin/PRD.md`](../admin/PRD.md) 为准；本文只写 App 侧规则。
- 渠道报表：[`../admin/PRD.md#admin-stats-channel`](../admin/PRD.md#admin-stats-channel)

## 规则

### 渠道埋点统计

| 功能名称 | 渠道埋点统计 |
|---|---|
| 优先级 | 高 |
| 功能描述 | / |
| 输入/前置条件 | / |
| 交互原型 | / |
| 字段描述 | / |
| 需求描述 | 平台：安卓、IOS<br>支持平台：AF和Firebase，用于投放按照特定指标的优化；<br>数据口径和所需埋点如下：<br>注册：渠道注册成功的行为<br>留存：次日、三日、七日（数据口径以平台定位为准，登录行为）<br>点击付费：所有点击付费入口；<br>首充礼包的充值按钮；<br>充值页面/充值弹窗，点击充值按钮；<br>完成付费：完成充值行为，按照订单最好；<br>应用内购充值成功；<br>渠道充值充值成功，包括币商；<br>完成充值的金额也要上报；<br>进入房间：进入房间行为；<br>上麦：上麦行为；<br>玩水果机：付费玩水果机的行为；<br>送礼行为：产生金币送礼成功的行为； |
| 补充说明 | 版本埋点明细见外链（原文）：https://365.kdocs.cn/l/cbSRmBnKkeZh |

## 版本

明细见 [`changelog.md`](changelog.md)。原文切片与叠稿在 [`history/`](history/)。
