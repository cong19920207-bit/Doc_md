CREATE DATABASE IF NOT EXISTS hayyo_kb
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE hayyo_kb;

CREATE TABLE IF NOT EXISTS qa_rounds (
  round_id VARCHAR(64) NOT NULL PRIMARY KEY,
  conv_id VARCHAR(64) NOT NULL,
  created_at DATETIME(3) NOT NULL,
  updated_at DATETIME(3) NOT NULL,
  original_query TEXT,
  rewrite_query TEXT,
  same_topic TINYINT NULL,
  named_feature_ids JSON NULL,
  lanes JSON NULL,
  c_gen JSON NULL,
  answer MEDIUMTEXT,
  status VARCHAR(32) NOT NULL,
  models JSON NULL,
  user_id VARCHAR(64) NULL,
  owner_id VARCHAR(64) NULL,
  tenant_id VARCHAR(64) NULL,
  role VARCHAR(64) NULL,
  feedback VARCHAR(16) NULL,
  feedback_at DATETIME(3) NULL,
  schema_ver INT NULL,
  logical_round_id VARCHAR(64) NULL,
  op_type VARCHAR(16) NULL,
  user_msg_id VARCHAR(64) NULL,
  assistant_msg_id VARCHAR(64) NULL,
  used_knowledge_rag TINYINT NULL,
  snapshot JSON NULL,
  error_type VARCHAR(32) NULL,
  biz_result VARCHAR(24) NULL,
  exec_state VARCHAR(16) NULL,
  check_status VARCHAR(16) NULL,
  text_integrity VARCHAR(16) NULL,
  msg_save VARCHAR(16) NULL,
  runtime_save VARCHAR(16) NULL,
  client_request_id VARCHAR(64) NULL,
  pending_reply JSON NULL,
  route VARCHAR(24) NULL,
  requires_history TINYINT NULL,
  router JSON NULL,
  finished_at DATETIME(3) NULL,
  task_prep JSON NULL,
  rewrite JSON NULL,
  call_usage JSON NULL,
  evidence_check JSON NULL,
  recall JSON NULL,
  history_refs JSON NULL,
  answer_process JSON NULL,
  INDEX idx_qa_rounds_created (created_at),
  INDEX idx_qa_rounds_status (status),
  INDEX idx_qa_rounds_conv (conv_id),
  INDEX idx_qa_rounds_conv_req (conv_id, client_request_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_roles (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  is_super TINYINT NOT NULL DEFAULT 0,
  is_preset TINYINT NOT NULL DEFAULT 0,
  created_at DATETIME(3) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_role_permissions (
  role_id VARCHAR(64) NOT NULL,
  perm_code VARCHAR(64) NOT NULL,
  PRIMARY KEY (role_id, perm_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_accounts (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  username VARCHAR(64) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role_id VARCHAR(64) NOT NULL,
  enabled TINYINT NOT NULL DEFAULT 1,
  tenant_id VARCHAR(64) NULL,
  created_at DATETIME(3) NOT NULL,
  updated_at DATETIME(3) NOT NULL,
  UNIQUE KEY uk_kb_accounts_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_sessions (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  account_id VARCHAR(64) NOT NULL,
  created_at DATETIME(3) NOT NULL,
  expires_at DATETIME(3) NOT NULL,
  revoked_at DATETIME(3) NULL,
  INDEX idx_kb_sessions_account (account_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_login_locks (
  username VARCHAR(64) NOT NULL PRIMARY KEY,
  fail_count INT NOT NULL DEFAULT 0,
  locked_until DATETIME(3) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_audit_logs (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  actor_id VARCHAR(64) NULL,
  actor_username VARCHAR(64) NULL,
  action VARCHAR(64) NOT NULL,
  object VARCHAR(255) NULL,
  ip VARCHAR(64) NULL,
  created_at DATETIME(3) NOT NULL,
  detail JSON NULL,
  op_id VARCHAR(64) NULL,
  result VARCHAR(16) NULL,
  error_code VARCHAR(64) NULL,
  object_type VARCHAR(32) NULL,
  actor_role VARCHAR(64) NULL,
  changed_fields JSON NULL,
  before_ver VARCHAR(64) NULL,
  after_ver VARCHAR(64) NULL,
  relation JSON NULL,
  reason VARCHAR(255) NULL,
  INDEX idx_kb_audit_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_conversations (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  account_id VARCHAR(64) NOT NULL,
  title VARCHAR(255) NOT NULL,
  title_locked TINYINT NOT NULL DEFAULT 0,
  payload MEDIUMTEXT NULL,
  last_seq BIGINT NOT NULL DEFAULT 0,
  clear_seq BIGINT NOT NULL DEFAULT 0,
  hidden_at DATETIME(3) NULL,
  purged_at DATETIME(3) NULL,
  run_exec_id VARCHAR(64) NULL,
  run_until DATETIME(3) NULL,
  save_block_exec_id VARCHAR(64) NULL,
  created_at DATETIME(3) NOT NULL,
  updated_at DATETIME(3) NOT NULL,
  INDEX idx_kb_convs_account (account_id, updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_conv_messages (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  conv_id VARCHAR(64) NOT NULL,
  seq BIGINT NOT NULL,
  round_id VARCHAR(64) NOT NULL,
  round_seq BIGINT NOT NULL,
  exec_id VARCHAR(64) NULL,
  role VARCHAR(16) NOT NULL,
  content MEDIUMTEXT,
  op_type VARCHAR(16) NOT NULL DEFAULT 'send',
  version_no INT NULL,
  is_current TINYINT NOT NULL DEFAULT 1,
  completeness VARCHAR(16) NOT NULL DEFAULT 'complete',
  client_request_id VARCHAR(64) NULL,
  source VARCHAR(16) NOT NULL DEFAULT 'live',
  created_at DATETIME(3) NOT NULL,
  UNIQUE KEY uk_conv_msg_seq (conv_id, seq),
  UNIQUE KEY uk_conv_msg_req (conv_id, client_request_id),
  INDEX idx_conv_msg_round (conv_id, round_seq),
  INDEX idx_conv_msg_round_id (round_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_conv_clears (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  conv_id VARCHAR(64) NOT NULL,
  boundary_seq BIGINT NOT NULL,
  actor_id VARCHAR(64) NULL,
  created_at DATETIME(3) NOT NULL,
  INDEX idx_conv_clears_conv (conv_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- STEP-Q14：对话记忆索引逐条记录（派生数据，可按消息表重建）
CREATE TABLE IF NOT EXISTS kb_mem_index (
  msg_id VARCHAR(64) NOT NULL PRIMARY KEY,
  conv_id VARCHAR(64) NOT NULL,
  seq BIGINT NOT NULL,
  status VARCHAR(16) NOT NULL,
  chunks INT NOT NULL DEFAULT 0,
  content_hash CHAR(64) NULL,
  attempts INT NOT NULL DEFAULT 0,
  error VARCHAR(64) NULL,
  gen INT NOT NULL DEFAULT 1,
  updated_at DATETIME(3) NOT NULL,
  INDEX idx_mem_index_conv (conv_id, seq)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_purge_ops (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  conv_id VARCHAR(64) NOT NULL,
  actor_id VARCHAR(64) NULL,
  status VARCHAR(16) NOT NULL,
  facts VARCHAR(16) NOT NULL,
  derived VARCHAR(16) NOT NULL,
  error VARCHAR(64) NULL,
  created_at DATETIME(3) NOT NULL,
  UNIQUE KEY uniq_purge_conv (conv_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_issues (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  title VARCHAR(80) NOT NULL,
  symptom VARCHAR(500) NOT NULL,
  category VARCHAR(16) NOT NULL,
  status VARCHAR(16) NOT NULL,
  assignee_id VARCHAR(64) NULL,
  close_reason VARCHAR(16) NULL,
  close_basis VARCHAR(500) NULL,
  source_type VARCHAR(16) NOT NULL,
  source_id VARCHAR(64) NULL,
  conv_id VARCHAR(64) NULL,
  source_deleted TINYINT NOT NULL DEFAULT 0,
  created_by VARCHAR(64) NULL,
  created_at DATETIME(3) NOT NULL,
  updated_at DATETIME(3) NOT NULL,
  INDEX idx_kb_issues_status (status, updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_issue_notes (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  issue_id VARCHAR(64) NOT NULL,
  actor_id VARCHAR(64) NULL,
  body VARCHAR(500) NOT NULL,
  created_at DATETIME(3) NOT NULL,
  INDEX idx_kb_issue_notes (issue_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_index_tasks (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  grp VARCHAR(16) NOT NULL,
  kind VARCHAR(32) NOT NULL,
  scope VARCHAR(64) NOT NULL,
  actor_id VARCHAR(64) NULL,
  status VARCHAR(16) NOT NULL,
  parent_id VARCHAR(64) NULL,
  scanned INT NOT NULL DEFAULT 0,
  changed INT NOT NULL DEFAULT 0,
  failed INT NOT NULL DEFAULT 0,
  integrity VARCHAR(16) NOT NULL,
  error VARCHAR(255) NULL,
  detail MEDIUMTEXT NULL,
  created_at DATETIME(3) NOT NULL,
  finished_at DATETIME(3) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
