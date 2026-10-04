# 核心文档

> 网站业务文档的分类入口。最后更新：2026-10-04。  
> 仓库总入口：[../../INDEX.md](../../INDEX.md)。网站工程文档与实现契约仍在 [../docs/INDEX.md](../docs/INDEX.md)。

| 分类 | 内容 | 权威入口 |
|---|---|---|
| PRD | Hayyo 产品规则、图片、现行说明、版本与归档 | [prd/INDEX.md](prd/INDEX.md) |

## 维护约定

- `site/core-docs/prd/` 是从原根 `prd/` 一次性迁移后的唯一产品文档源；不维护旧目录、副本或反向同步。
- 产品规则仍以每个功能的 `PRD.md` 为准，brief、原型及图表不另立一套规则。
- 后续其他 Markdown 分类与 `prd/` 并列；本轮不创建空分类，也不自动纳入发布或问答语料。
- 本目录不存网站自身的工程需求、执行记录和实现契约，它们继续放在 `site/docs/`。
- 源码内的 manifest 路径和 brief 的 `source` 以仓库根为基准，指向 `site/core-docs/prd/...`。
- 浏览器地址 `/prd/...`、知识块及历史问答的逻辑标识 `prd/...` 保持稳定。发布器负责生成浏览器 manifest 和 URL 映射，不把源码 manifest 直接当运行时清单。
- 自动生成的发布文件不是第二份权威，不人工编辑，也不反向覆盖本目录。

## 本地维护与发布边界

1. 直接编辑本目录中的权威文档；新增 PRD 功能时同步产品 manifest、PRD、brief 和 changelog。
2. 仓库根执行 `sh site/preview.sh`，生成 `site/release/www` 并刷新本地服务；只有文档/前端变化且 API 镜像已更新时，可用 `sh site/preview.sh --no-build`。
3. 浏览器继续访问 `http://127.0.0.1:18765/feature-interaction/`；文档 URL 仍为 `/prd/...`。发布目录不可人工编辑。

Web 只读挂载生成产物；API 只读挂载本目录为 `/core-docs`。发布器仅选现行文档、brief、变更日志、图片和明确的功能历史版本，生成浏览器 manifest 与历史 JSON；仓库工作区、工程文档、归档、源码、配置及证书包不整目录公开。未发布的本地文档链接在阅读器中标记“未发布”。静态页面采用 `site/docker/publish-files.json` 的逐文件清单，不因新增文件自动发布；其中显式保留运营后台原型与两个复盘汇总页，不等于开放这些源目录。完整路径映射、选择规则与刷新流程见 [H5 实现契约 §8](../docs/contracts/h5-kb/contract.md#8-核心文档与受控发布)。

本地运行切换已完成，生产未部署。完整验证范围、浏览器验收状态和恢复位置见[核心文档迁移开发执行记录](../docs/design/core-docs-migration/execution/核心文档迁移开发执行记录.md)。
