"""用户可见的执行记录。只投影实际事件，不生成思考文本或增加模型调用。"""
from __future__ import annotations

from copy import deepcopy

from .aliases import c20_display_name


STAGES = {
    'route': ('理解问题', '正在识别本轮问题的类型与上下文需求。'),
    'task_prep': ('梳理本轮任务', '正在整理需要回答的问题、适用场景和缺少的条件。'),
    'recall': ('查找此前对话', '正在本会话允许的历史范围内查找相关原话。'),
    'conversation': ('整理此前内容', '正在读取本轮需要回看或重述的历史内容。'),
    'rewrite': ('明确检索问题', '正在结合本轮任务与可用上下文整理查询内容。'),
    'retrieve': ('查找相关资料', '正在知识库中查找与本轮问题相关的候选片段。'),
    'rerank': ('筛选参考依据', '正在筛选与本轮问题相关的参考片段。'),
    'generate': ('组织回答', '正在依据本轮选用的资料组织回答。'),
    'check': ('核对回答与原文', '正在核对回答的依据、适用条件与数字。'),
    'repair': ('按依据修正回答', '正在根据本次核对发现的问题修正草稿。'),
    'smalltalk': ('组织回复', '正在组织本轮回复。'),
    'clarify': ('明确缺少的信息', '正在整理需要你补充或确认的问题。'),
}
SOURCE_KEYS = ('path', 'chunk_id', 'anchor', 'heading', 'content_hash', 'collection', 'feature_id')


def text(value):
    return str(value or '').strip()[:600]


class AnswerProcess:
    def __init__(self, exec_id):
        self.exec_id = exec_id
        self.steps = []
        self.state = 'running'
        self.summary = ''
        self.document_count = 0

    def snapshot(self):
        return deepcopy({'version': 1, 'exec_id': self.exec_id, 'state': self.state,
                         'summary': self.summary, 'document_count': self.document_count, 'steps': self.steps})

    def current(self, stage=None):
        return next((s for s in reversed(self.steps) if stage is None or s['stage'] == stage), None)

    def complete_step(self, step):
        step['state'] = 'done'
        # 尚无具体结果说明的步骤结束时，移除“正在”文案。
        if step['details'] == [STAGES[step['stage']][1]]:
            step['details'] = [{'generate': '已依据本轮选用的资料生成回答草稿。',
                                'repair': '已根据核对结果生成修正稿。',
                                'conversation': '已整理本轮需要处理的历史内容。',
                                'smalltalk': '已生成本轮回复。',
                                'clarify': '已整理需要补充或确认的问题。'}.get(
                                    step['stage'], '本步骤已完成。')]

    def details(self, stage, lines, state=None, sources=None):
        step = self.current(stage)
        if step is None:
            return
        step['details'] = [text(line) for line in lines if text(line)][:12]
        if state:
            step['state'] = state
        if sources is not None:
            step['sources'] = sources

    def observe(self, event, data):
        """True 表示记录发生变化；token 不积累进过程，也不触发过程写库。"""
        if event == 'stage':
            stage = data.get('stage')
            if stage not in STAGES:
                return False
            previous = self.current()
            if previous and previous['state'] == 'running':
                self.complete_step(previous)
            title, detail = STAGES[stage]
            self.steps.append({'id': str(len(self.steps) + 1), 'stage': stage, 'title': title,
                               'state': 'running', 'details': [detail], 'sources': []})
        elif event == 'process':
            kind = data.get('kind')
            if kind == 'route':
                label = {'knowledge_query': '知识查询', 'conversation_task': '历史内容处理',
                         'ack': '确认回应', 'smalltalk': '日常交流', 'out_of_scope': '范围说明',
                         'unclear': '需要澄清的问题'}.get(data.get('route'), '问题处理')
                self.details('route', ['本轮识别为：' + label + '。'], 'done')
            elif kind == 'tasks':
                tasks = data.get('tasks') or []
                lines = [f"{text(t.get('goal'))}" +
                         (f"（{text(t.get('reason'))}）" if t.get('check') != 'ready' and t.get('reason') else '')
                         for t in tasks]
                for item in data.get('excluded') or []:
                    lines.append('未执行：' + text(item.get('text')) + '；' + text(item.get('reason')))
                constraint = data.get('response_constraint')
                if constraint:
                    lines.append('回答要求：' + text(constraint))
                self.details('task_prep', lines, 'done')
            elif kind == 'recall':
                reason = data.get('stop_reason')
                label = {'ready': '已取得用于理解本轮问题的历史内容。',
                         'not_found': '本次未找到所需的历史内容。',
                         'needs_clarification': '存在多个可能的历史对象，需要进一步确认。',
                         'no_progress': '未获得更多有效历史信息，本次查找已停止。',
                         'tool_error': '历史查找暂不可用。'}.get(reason, '本次历史查找已结束，以实际恢复内容继续处理。')
                self.details('recall', [label], 'done' if reason == 'ready' else 'warning')
            elif kind == 'check':
                verdict = data.get('check_status')
                lines = [f"本次核对发现 {data.get('issue_count', 0)} 项需要处理的问题。" if verdict == 'fail'
                         else '已完成本轮回答与所选原文的核对。']
                if data.get('conflict'):
                    lines.append('参考资料存在冲突，回答中需要保留分歧说明。')
                self.details('check', lines, 'done' if verdict == 'pass' else 'warning')
            else:
                return False
        elif event == 'rewrite':
            lines = ['本轮查询：' + text(data.get('rewrite_query') or data.get('standalone_query'))]
            features = data.get('named_feature_ids') or []
            if features:
                lines.append('涉及范围：' + '、'.join(c20_display_name(f) for f in features))
            self.details('rewrite', lines, 'done')
        elif event == 'retrieve':
            paths = set(data.get('paths') or [])
            self.details('retrieve', [f"找到 {data.get('count', 0)} 个候选片段，涉及 {len(paths)} 份文档。",
                                      '候选片段将继续筛选，尚不代表已支持全部结论。'], 'done')
        elif event == 'rerank':
            blocks = data.get('c_gen') or []
            self.document_count = len({b.get('path') for b in blocks if b.get('path')})
            sources = [{k: text(b.get(k)) for k in SOURCE_KEYS} for b in blocks]
            self.details('rerank', [f"本轮选用 {len(blocks)} 个参考片段，来自 {self.document_count} 份文档。"],
                         'done' if blocks else 'warning', sources)
        elif event == 'check':
            if data.get('check_status') == 'error':
                self.details('check', ['原文核对未能完成，本轮不能确认为可靠回答。'], 'error')
            elif data.get('check_status') == 'fail':
                self.details('check', ['本轮回答未通过原文核对，已返回说明。'], 'warning')
        elif event == 'error':
            self.finish('failed', '本轮未完成')
        else:
            return False
        return True

    def finish(self, state, summary):
        self.state, self.summary = state, summary
        step = self.current()
        if step and step['state'] == 'running':
            if state == 'completed':
                self.complete_step(step)
            else:
                step['state'] = 'error'


def process_for_row(row):
    """旧记录不补造过程；崩溃后的终态覆盖遗留 running 标记。"""
    process = deepcopy((row or {}).get('answer_process'))
    if not isinstance(process, dict):
        return None
    state = (row or {}).get('exec_state')
    if state in ('failed', 'interrupted') and process.get('state') == 'running':
        process.update(state=state, summary='本轮未完成')
        for step in process.get('steps') or []:
            if step.get('state') == 'running':
                step['state'] = 'error'
    return process


def answer_history(rows, get_log):
    """仅消费已通过会话可见性与清空边界过滤的消息，按逻辑回合绑定过程和版本。"""
    groups = {}
    for row in rows:
        group = groups.setdefault(row['round_id'], {'user': None, 'answers': []})
        if row['role'] == 'user':
            group['user'] = row
        elif row['role'] == 'assistant':
            group['answers'].append(row)
    messages = []
    for rid, group in groups.items():
        user = group['user']
        if not user:
            continue
        messages.append({'id': user['id'], 'role': 'user', 'text': user.get('content') or ''})
        versions = []
        chosen = 0
        for answer in sorted(group['answers'], key=lambda a: a.get('version_no') or 0):
            log = get_log(answer.get('exec_id')) or {}
            failed = answer.get('completeness') == 'error_notice'
            if answer.get('is_current'):
                chosen = len(versions)
            versions.append({'round_id': answer.get('exec_id'), 'assistant_msg_id': answer['id'],
                             'text': answer.get('content') or '', 'role': 'system' if failed else 'assistant',
                             'kind': log.get('error_type') if failed else None,
                             'citations': log.get('c_gen') or [], 'feedback': log.get('feedback') or '',
                             'refused': log.get('status') in ('empty', 'refuse'), 'logWritten': bool(log),
                             'historyRefs': log.get('history_refs') or [], 'process': process_for_row(log)})
        if versions:
            messages.append({'id': 'answer-' + rid, 'logical_round_id': rid, 'query': user.get('content') or '',
                             'versions': versions, 'viewIndex': chosen, **versions[chosen]})
    return messages
